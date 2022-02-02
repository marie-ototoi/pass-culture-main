from datetime import datetime

import sqlalchemy

from pcapi.core.fraud.api import _duplicate_user_fraud_item
from pcapi.core.fraud.api import create_honor_statement_fraud_check
from pcapi.core.fraud.api import duplicate_id_piece_number_fraud_item
from pcapi.core.fraud.models import BeneficiaryFraudCheck
from pcapi.core.fraud.models import FraudCheckStatus
from pcapi.core.fraud.models import FraudCheckType
from pcapi.core.fraud.models import FraudStatus
from pcapi.core.subscription import api as subscription_api
from pcapi.core.users import models as users_models
from pcapi.core.users import utils as users_utils
from pcapi.models import db
from pcapi.models.beneficiary_import import BeneficiaryImport
from pcapi.models.beneficiary_import import BeneficiaryImportSources
from pcapi.repository import repository
from pcapi.repository.user_queries import matching


def categorize_dms_ko():
    checks: list[BeneficiaryFraudCheck] = BeneficiaryFraudCheck.query.filter(
        BeneficiaryFraudCheck.type == FraudCheckType.DMS,
        BeneficiaryFraudCheck.status == FraudCheckStatus.KO,
    ).all()
    underage_generalisations = []
    age_19_yo = []
    no_registration = []
    not_eligibility_matters = []
    age_more_than_19_yo = []
    already_bene = []
    for check in checks:
        data = check.source_data()
        if check.user.is_beneficiary:
            already_bene.append(check)
            continue
        if data.get_eligibility_type() is None:
            if data.get_registration_datetime() is None:
                no_registration.append(check)
                continue
            birth_date = data.get_birth_date()
            age_at_registration = users_utils.get_age_at_date(birth_date, data.get_registration_datetime())
            if age_at_registration > 19 or age_at_registration < 15:
                age_more_than_19_yo.append(check)
                continue
            bene_import = BeneficiaryImport.query.filter(
                BeneficiaryImport.beneficiary == check.user, BeneficiaryImport.applicationId == int(check.thirdPartyId)
            ).first()
            if not bene_import:
                print("no-import", check.userId)
            if age_at_registration in [15, 16, 17]:
                underage_generalisations.append((check, bene_import.sourceId))
            if age_at_registration == 19:
                age_19_yo.append((check, bene_import.sourceId))
        else:
            not_eligibility_matters.append(check)
    print("underage_generalisations", len(underage_generalisations))
    print("age_19_yo", len(age_19_yo))
    print("no_registration", len(no_registration))
    print("not_eligibility_matters", len(not_eligibility_matters))
    print("age_more_than_19_yo", len(age_more_than_19_yo))
    print("already_bene", len(already_bene))
    return (
        underage_generalisations,
        age_19_yo,
        no_registration,
        not_eligibility_matters,
        age_more_than_19_yo,
        already_bene,
    )


def categorize_fraud_check_contents(items: list[tuple[BeneficiaryFraudCheck, int]]):
    duplicates_id = []
    duplicates_name = []
    active_deposit = []
    activable = []
    for check, procedure_id in items:
        content = check.source_data()
        duplicate_id_item = duplicate_id_piece_number_fraud_item(check.user, content.get_id_piece_number())
        if duplicate_id_item.status != FraudStatus.OK:
            duplicates_id.append(check)
            continue
        duplicate_item = _duplicate_user_fraud_item(
            first_name=content.get_first_name(),
            last_name=content.get_last_name(),
            birth_date=content.get_birth_date(),
            excluded_user_id=check.userId,
        )
        if duplicate_item.status != FraudStatus.OK:
            duplicates_name.append(check)
            continue
        if check.user.has_active_deposit:
            active_deposit.append(check)
            continue
        activable.append((check, procedure_id))
    print("duplicates_id", len(duplicates_id))
    print("duplicates_name", len(duplicates_name))
    print("active_deposit", len(active_deposit))
    print("activable", len(activable))
    return duplicates_id, duplicates_name, active_deposit, activable


def force_import(items: list[tuple[BeneficiaryFraudCheck, int]]):
    activated_user_ids = []
    activated_user_ids_not_19 = []
    not_activated_user_ids = []
    failed_user_ids = []
    already_bene = []
    duplicates_id = []
    duplicates_name = []
    active_deposit = []
    for check, procedure_id in items:
        content = check.source_data()
        birth_date = content.get_birth_date()
        age_at_registration = users_utils.get_age_at_date(birth_date, content.get_registration_datetime())
        if age_at_registration in [15, 16, 17]:
            reason = "the DMS file was registrated during 15-17 generalisation and the user was therefore not eligible"
            if users_utils.get_age_at_date(birth_date, datetime.now()) == 18:
                eligibility = users_models.EligibilityType.AGE18
            else:
                eligibility = users_models.EligibilityType.UNDERAGE
        elif age_at_registration == 18:
            eligibility = users_models.EligibilityType.AGE18
            reason = "the DMS file was registrated when the user was 18 yo but was not considered eligible"
        elif age_at_registration == 19:
            eligibility = users_models.EligibilityType.AGE18
            reason = "the DMS file was registrated when the user was 19 yo"
        else:
            print(check.userId, "age", age_at_registration)
            continue
        user = check.user
        if user.is_beneficiary:
            already_bene.append(user.id)
            continue
        duplicate_id_item = duplicate_id_piece_number_fraud_item(check.user, content.get_id_piece_number())
        if duplicate_id_item.status != FraudStatus.OK:
            duplicates_id.append(check)
            continue
        duplicate_item = _duplicate_user_fraud_item(
            first_name=content.get_first_name(),
            last_name=content.get_last_name(),
            birth_date=content.get_birth_date(),
            excluded_user_id=check.userId,
        )
        if duplicate_item.status != FraudStatus.OK:
            duplicates_name.append(check)
            continue
        if check.user.has_active_deposit:
            active_deposit.append(check)
            continue
        new_fraud_check = BeneficiaryFraudCheck(
            user=user,
            type=FraudCheckType.DMS,
            thirdPartyId=check.thirdPartyId,
            resultContent=check.resultContent,
            eligibilityType=eligibility,
            status=FraudCheckStatus.OK,
            reason=reason,
        )
        repository.save(new_fraud_check)
        create_honor_statement_fraud_check(user, "honor statement contained in DMS application", eligibility)
        try:
            subscription_api.on_successful_application(
                user=user,
                source_data=content,
                eligibility_type=eligibility,
                application_id=int(check.thirdPartyId),
                source_id=procedure_id,
                source=BeneficiaryImportSources.demarches_simplifiees,
            )
            db.session.refresh(user)
            if user.is_beneficiary:
                if age_at_registration == 19:
                    activated_user_ids.append(user.id)
                else:
                    activated_user_ids_not_19.append(user.id)
            else:
                not_activated_user_ids.append(user.id)
        except Exception as e:
            failed_user_ids.append(user.id)
            print("exception on activation", check.id, user.id, e)
            db.session.rollback()
    print("already_bene", len(already_bene))
    print("activated_user_ids", len(activated_user_ids))
    print("activated_user_ids_not_19", len(activated_user_ids_not_19))
    print("not_activated_user_ids", len(not_activated_user_ids))
    print("failed_user_ids", len(failed_user_ids))
    print("duplicates_id", len(duplicates_id))
    print("duplicates_name", len(duplicates_name))
    print("active_deposit", len(active_deposit))
    return (
        already_bene,
        activated_user_ids,
        activated_user_ids_not_19,
        not_activated_user_ids,
        failed_user_ids,
        duplicates_id,
        duplicates_name,
        active_deposit,
    )
