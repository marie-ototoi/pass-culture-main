import datetime
import logging
import typing

from pcapi import settings
import pcapi.core.fraud.api as fraud_api
import pcapi.core.fraud.models as fraud_models
import pcapi.core.fraud.repository as fraud_repository
from pcapi.core.mails.transactional.users import accepted_as_beneficiary_email
from pcapi.core.payments import api as payments_api
from pcapi.core.subscription import messages as subscription_messages
from pcapi.core.users import api as users_api
from pcapi.core.users import constants as users_constants
from pcapi.core.users import external as users_external
from pcapi.core.users import models as users_models
from pcapi.core.users import repository as users_repository
from pcapi.core.users import utils as users_utils
from pcapi.domain import user_emails as old_user_emails
from pcapi.domain.postal_code.postal_code import PostalCode
from pcapi.models import db
from pcapi.models.beneficiary_import import BeneficiaryImport
from pcapi.models.beneficiary_import import BeneficiaryImportSources
from pcapi.models.beneficiary_import_status import ImportStatus
from pcapi.models.feature import FeatureToggle
import pcapi.repository as pcapi_repository
from pcapi.workers import apps_flyer_job

from . import exceptions
from . import models
from . import repository as subscription_repository


logger = logging.getLogger(__name__)


def attach_beneficiary_import_details(
    beneficiary: users_models.User,
    application_id: int,
    source_id: int,
    source: BeneficiaryImportSources,
    eligibility_type: typing.Optional[users_models.EligibilityType],
    details: typing.Optional[str] = None,
    status: ImportStatus = ImportStatus.CREATED,
) -> None:
    beneficiary_import = BeneficiaryImport.query.filter_by(
        applicationId=application_id,
        sourceId=source_id,
        source=source.value,
        beneficiary=beneficiary,
        eligibilityType=eligibility_type,
    ).one_or_none()
    if not beneficiary_import:
        beneficiary_import = BeneficiaryImport(
            applicationId=application_id,
            sourceId=source_id,
            source=source.value,
            beneficiary=beneficiary,
            eligibilityType=eligibility_type,
        )

    beneficiary_import.setStatus(status=status, detail=details)
    beneficiary_import.beneficiary = beneficiary

    pcapi_repository.repository.save(beneficiary_import)


def get_latest_subscription_message(user: users_models.User) -> typing.Optional[models.SubscriptionMessage]:
    return models.SubscriptionMessage.query.filter_by(user=user).order_by(models.SubscriptionMessage.id.desc()).first()


def create_successfull_beneficiary_import(
    user: users_models.User,
    source: BeneficiaryImportSources,
    source_id: typing.Optional[int] = None,
    application_id: typing.Optional[int] = None,
    eligibility_type: typing.Optional[users_models.EligibilityType] = None,
    third_party_id: typing.Optional[str] = None,
) -> None:
    if application_id:
        beneficiary_import_filter = BeneficiaryImport.applicationId == application_id
    elif third_party_id:
        beneficiary_import_filter = BeneficiaryImport.thirdPartyId == third_party_id
    else:
        raise ValueError(
            "create_successfull_beneficiary_import need need a non-None value for application_id or third_party_id"
        )
    existing_beneficiary_import = BeneficiaryImport.query.filter(beneficiary_import_filter).first()

    beneficiary_import = existing_beneficiary_import or BeneficiaryImport()
    if not beneficiary_import.beneficiary:
        beneficiary_import.beneficiary = user
    if eligibility_type is not None:
        beneficiary_import.eligibilityType = eligibility_type

    beneficiary_import.applicationId = application_id
    beneficiary_import.sourceId = source_id
    beneficiary_import.source = source.value
    beneficiary_import.setStatus(status=ImportStatus.CREATED, author=None)
    beneficiary_import.thirdPartyId = third_party_id

    pcapi_repository.repository.save(beneficiary_import)

    return beneficiary_import


def activate_beneficiary(
    user: users_models.User, deposit_source: str = None, has_activated_account: typing.Optional[bool] = True
) -> users_models.User:

    beneficiary_import = subscription_repository.get_beneficiary_import_for_beneficiary(user)
    if not beneficiary_import:
        raise exceptions.BeneficiaryImportMissingException()

    eligibility = beneficiary_import.eligibilityType
    deposit_source = beneficiary_import.get_detailed_source()

    if not users_api.is_eligible_for_beneficiary_upgrade(user, eligibility):
        raise exceptions.CannotUpgradeBeneficiaryRole()

    if eligibility == users_models.EligibilityType.UNDERAGE:
        user.validate_user_identity_15_17()
        user.add_underage_beneficiary_role()
    elif eligibility == users_models.EligibilityType.AGE18:
        user.validate_user_identity_18()
        user.add_beneficiary_role()
        user.remove_underage_beneficiary_role()
    else:
        raise exceptions.InvalidEligibilityTypeException()

    if "apps_flyer" in user.externalIds:
        apps_flyer_job.log_user_becomes_beneficiary_event_job.delay(user.id)

    deposit = payments_api.create_deposit(user, deposit_source=deposit_source, eligibility=eligibility)

    user.hasCompletedIdCheck = False

    db.session.add_all((user, deposit))
    db.session.commit()
    logger.info("Activated beneficiary and created deposit", extra={"user": user.id, "source": deposit_source})

    db.session.refresh(user)

    users_external.update_external_user(user)
    _send_beneficiary_activation_email(user, has_activated_account)

    return user


def check_and_activate_beneficiary(
    userId: int, deposit_source: str = None, has_activated_account: typing.Optional[bool] = True
) -> users_models.User:
    with pcapi_repository.transaction():
        user = users_repository.get_and_lock_user(userId)

        if not user.hasCompletedIdCheck:
            db.session.rollback()
            return user
        try:
            user = activate_beneficiary(user, deposit_source, has_activated_account)
        except exceptions.CannotUpgradeBeneficiaryRole:
            db.session.rollback()
            return user
        return user


def _send_beneficiary_activation_email(user: users_models.User, has_activated_account: bool):
    if not has_activated_account:
        old_user_emails.send_activation_email(
            user=user, reset_password_token_life_time=users_constants.RESET_PASSWORD_TOKEN_LIFE_TIME_EXTENDED
        )
    else:
        accepted_as_beneficiary_email.send_accepted_as_beneficiary_email(user=user)


def has_completed_profile(user: users_models.User) -> bool:
    return user.city is not None


def needs_to_perform_identity_check(user: users_models.User) -> bool:
    # TODO (viconnex) refacto this method to base result on fraud_checks made
    return (
        not user.hasCompletedIdCheck
        and not (fraud_api.has_user_performed_ubble_check(user) and FeatureToggle.ENABLE_UBBLE.is_active())
        and not user.extraData.get("is_identity_document_uploaded")  # Jouve
        and not (fraud_api.has_passed_educonnect(user) and user.eligibility == users_models.EligibilityType.UNDERAGE)
    )


# pylint: disable=too-many-return-statements
def get_next_subscription_step(user: users_models.User) -> typing.Optional[models.SubscriptionStep]:
    # TODO(viconnex): base the next step on the user.subscriptionState that will be added later on
    allowed_identity_check_methods = get_allowed_identity_check_methods(user)
    if not allowed_identity_check_methods:
        return models.SubscriptionStep.MAINTENANCE
    if not user.isEmailValidated:
        return models.SubscriptionStep.EMAIL_VALIDATION

    if not users_api.is_eligible_for_beneficiary_upgrade(user, user.eligibility):
        return None

    if user.eligibility == users_models.EligibilityType.AGE18:
        if not user.is_phone_validated and FeatureToggle.ENABLE_PHONE_VALIDATION.is_active():
            return models.SubscriptionStep.PHONE_VALIDATION

        user_profiling = fraud_repository.get_last_user_profiling_fraud_check(user)

        if not user_profiling:
            return models.SubscriptionStep.USER_PROFILING

        if fraud_api.is_risky_user_profile(user):
            return None

    if not has_completed_profile(user):
        return models.SubscriptionStep.PROFILE_COMPLETION

    if needs_to_perform_identity_check(user) and allowed_identity_check_methods:
        return models.SubscriptionStep.IDENTITY_CHECK

    if not fraud_api.has_performed_honor_statement(user, user.eligibility):
        return models.SubscriptionStep.HONOR_STATEMENT

    return None


def update_user_profile(
    user: users_models.User,
    address: typing.Optional[str],
    city: str,
    postal_code: str,
    activity: str,
    first_name: typing.Optional[str] = None,
    last_name: typing.Optional[str] = None,
    school_type: typing.Optional[users_models.SchoolTypeEnum] = None,
    phone_number: typing.Optional[str] = None,
    is_legacy_behaviour: typing.Optional[bool] = False,
) -> None:
    user_initial_roles = user.roles

    update_payload = {
        "address": address,
        "city": city,
        "postalCode": postal_code,
        "departementCode": PostalCode(postal_code).get_departement_code(),
        "activity": activity,
        "schoolType": school_type,
    }

    if first_name and not user.firstName:
        update_payload["firstName"] = first_name

    if last_name and not user.lastName:
        update_payload["lastName"] = last_name

    if is_legacy_behaviour:
        # TODO (viconnex): remove phone number update after app native mandatory version is >= 164
        if not user.phoneNumber and phone_number and not FeatureToggle.ENABLE_PHONE_VALIDATION.is_active():
            update_payload["phoneNumber"] = phone_number
        update_payload["hasCompletedIdCheck"] = True
        fraud_api.create_honor_statement_fraud_check(user, "legacy /beneficiary_information route")

    with pcapi_repository.transaction():
        users_models.User.query.filter(users_models.User.id == user.id).update(update_payload)
    db.session.refresh(user)

    if (
        not users_api.steps_to_become_beneficiary(user, user.eligibility)
        # the 2 following checks should be useless
        and fraud_api.has_user_performed_identity_check(user)
        and not fraud_api.is_user_fraudster(user)
    ):
        check_and_activate_beneficiary(user.id)
    else:
        users_api.update_external_user(user)

    new_user_roles = user.roles
    underage_user_has_been_activated = (
        users_models.UserRole.UNDERAGE_BENEFICIARY in new_user_roles
        and users_models.UserRole.UNDERAGE_BENEFICIARY not in user_initial_roles
    )

    logger.info(
        "User id check profile updated",
        extra={"user": user.id, "has_been_activated": user.has_beneficiary_role or underage_user_has_been_activated},
    )


def is_identity_check_with_document_method_allowed_for_underage(user: users_models.User) -> bool:

    if not FeatureToggle.ALLOW_IDCHECK_UNDERAGE_REGISTRATION.is_active():
        return False

    if (
        user.schoolType == users_models.SchoolTypeEnum.PUBLIC_HIGH_SCHOOL
        or user.schoolType == users_models.SchoolTypeEnum.PUBLIC_SECONDARY_SCHOOL
    ):
        return FeatureToggle.ALLOW_IDCHECK_REGISTRATION_FOR_EDUCONNECT_ELIGIBLE.is_active()
    return True


def get_allowed_identity_check_methods(user: users_models.User) -> list[models.IdentityCheckMethod]:
    allowed_methods = []

    if (
        user.eligibility == users_models.EligibilityType.UNDERAGE
        and FeatureToggle.ENABLE_NATIVE_EAC_INDIVIDUAL.is_active()
    ):
        if FeatureToggle.ENABLE_EDUCONNECT_AUTHENTICATION.is_active():
            allowed_methods.append(models.IdentityCheckMethod.EDUCONNECT)

        if is_identity_check_with_document_method_allowed_for_underage(user):
            if FeatureToggle.ENABLE_UBBLE.is_active() and _is_ubble_allowed_if_subscription_overflow(user):
                allowed_methods.append(models.IdentityCheckMethod.UBBLE)
            if not FeatureToggle.ENABLE_UBBLE.is_active():
                allowed_methods.append(models.IdentityCheckMethod.JOUVE)

    elif user.eligibility == users_models.EligibilityType.AGE18:
        if FeatureToggle.ALLOW_IDCHECK_REGISTRATION.is_active():
            if FeatureToggle.ENABLE_UBBLE.is_active() and _is_ubble_allowed_if_subscription_overflow(user):
                allowed_methods.append(models.IdentityCheckMethod.UBBLE)
            if not FeatureToggle.ENABLE_UBBLE.is_active():
                allowed_methods.append(models.IdentityCheckMethod.JOUVE)

    return allowed_methods


def _is_ubble_allowed_if_subscription_overflow(user: users_models.User) -> bool:
    if not FeatureToggle.ENABLE_UBBLE_SUBSCRIPTION_LIMITATION.is_active():
        return True

    future_age = users_utils.get_age_at_date(
        user.dateOfBirth,
        datetime.datetime.utcnow() + datetime.timedelta(days=settings.UBBLE_SUBSCRIPTION_LIMITATION_DAYS),
    )
    eligbility_ranges = users_constants.ELIGIBILITY_UNDERAGE_RANGE + [users_constants.ELIGIBILITY_AGE_18]
    eligbility_ranges = [age + 1 for age in eligbility_ranges]
    if future_age > user.age and future_age in eligbility_ranges:
        return True

    return False


def get_maintenance_page_type(user: users_models.User) -> typing.Optional[models.MaintenancePageType]:
    allowed_identity_check_methods = get_allowed_identity_check_methods(user)
    if allowed_identity_check_methods:
        return None

    if (
        user.eligibility == users_models.EligibilityType.AGE18
        and FeatureToggle.ENABLE_DMS_LINK_ON_MAINTENANCE_PAGE_FOR_AGE_18.is_active()
    ):
        return models.MaintenancePageType.WITH_DMS
    if (
        user.eligibility == users_models.EligibilityType.UNDERAGE
        and FeatureToggle.ENABLE_DMS_LINK_ON_MAINTENANCE_PAGE_FOR_UNDERAGE.is_active()
    ):
        return models.MaintenancePageType.WITH_DMS

    return models.MaintenancePageType.WITHOUT_DMS


def on_successful_application(
    user: users_models.User,
    source_data: fraud_models.IdentityCheckContent,
    source: BeneficiaryImportSources,
    eligibility_type: users_models.EligibilityType,
    application_id: typing.Optional[int] = None,
    source_id: typing.Optional[int] = None,
    third_party_id: typing.Optional[str] = None,
) -> None:
    users_api.update_user_information_from_external_source(user, source_data)

    # TODO (viconnex) remove when we also look for DMS files to know if the user has completed id check
    user.hasCompletedIdCheck = True

    pcapi_repository.repository.save(user)

    create_successfull_beneficiary_import(
        user=user,
        source=source,
        source_id=source_id,
        application_id=application_id,
        eligibility_type=eligibility_type,
        third_party_id=third_party_id,
    )

    if not users_api.steps_to_become_beneficiary(user, eligibility_type):
        activate_beneficiary(user)
    else:
        users_external.update_external_user(user)


def handle_validation_errors(
    user: users_models.User,
    reason_codes: list[fraud_models.FraudReasonCode],
):
    for error_code in reason_codes:
        if error_code == fraud_models.FraudReasonCode.ALREADY_BENEFICIARY:
            subscription_messages.on_already_beneficiary(user)
        if error_code == fraud_models.FraudReasonCode.NOT_ELIGIBLE:
            subscription_messages.on_not_eligible(user)
        if error_code == fraud_models.FraudReasonCode.DUPLICATE_USER:
            subscription_messages.on_duplicate_user(user)
        if error_code == fraud_models.FraudReasonCode.DUPLICATE_ID_PIECE_NUMBER:
            subscription_messages.on_duplicate_user(user)


# TODO (viconnex): move in a dms folder
def start_workflow(
    user: users_models.User, thirdparty_id: str, content: fraud_models.DMSContent
) -> fraud_models.BeneficiaryFraudCheck:
    user.submit_user_identity()
    pcapi_repository.repository.save(user)
    fraud_check = fraud_api.start_fraud_check(user, thirdparty_id, content)
    return fraud_check
