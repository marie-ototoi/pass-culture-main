from pcapi.connectors.dms import api as api_dms
from pcapi.core.fraud import models as fraud_models
from pcapi.core.fraud.api import _duplicate_user_fraud_item
from pcapi.core.fraud.api import duplicate_id_piece_number_fraud_item
from pcapi.core.fraud.models import FraudStatus
from pcapi.core.users.repository import find_user_by_email
from pcapi.repository.beneficiary_import_queries import get_already_processed_applications_ids
from pcapi.scripts.beneficiary.import_dms_users import DMSParsingError
from pcapi.scripts.beneficiary.import_dms_users import parse_beneficiary_information_graphql
from pcapi.scripts.beneficiary.import_dms_users import process_application


def import_test_procedure(procedure_id: int) -> None:
    existing_applications_ids = get_already_processed_applications_ids(procedure_id)
    client = api_dms.DMSGraphQLClient()
    applications = client.get_applications_with_details(procedure_id, api_dms.GraphQLApplicationStates.accepted)
    print("len(existing_applications_ids)", len(existing_applications_ids))
    duplicate_ids = []
    duplicates_name = []
    to_activate = []
    for application_details in applications:
        application_id = application_details["number"]
        if application_id in existing_applications_ids:
            continue
        try:
            information: fraud_models.IdCheckinformation = parse_beneficiary_information_graphql(
                application_details, procedure_id
            )
        except DMSParsingError as exc:
            print("DMSParsingError", application_id, exc.errors)
            continue
        except Exception as exc:  # pylint: disable=broad-except
            print("exception", application_id, exc)
            continue
        user = find_user_by_email(information.email)
        if not user:
            print("no user", application_id)
            continue
        if user.is_beneficiary:
            print("user already bene", user.id, application_id)
            continue
        duplicate_id_item = duplicate_id_piece_number_fraud_item(user, information.get_id_piece_number())
        if duplicate_id_item.status != FraudStatus.OK:
            duplicate_ids.append(user.id)
            continue
        duplicate_item = _duplicate_user_fraud_item(
            first_name=information.get_first_name(),
            last_name=information.get_last_name(),
            birth_date=information.get_birth_date(),
            excluded_user_id=user.id,
        )
        if duplicate_item.status != FraudStatus.OK:
            duplicates_name.append(user.id)
            continue
        to_activate.append(user.id)
        process_application(procedure_id, application_id, information)
