import logging

from sqlalchemy import Integer
from sqlalchemy.orm import load_only

from pcapi.core.fraud import models as fraud_models
from pcapi.models.beneficiary_import import BeneficiaryImport
from pcapi.models.beneficiary_import import BeneficiaryImportStatus
from pcapi.models.beneficiary_import_status import ImportStatus


logger = logging.getLogger(__name__)


# TODO: get_already_processed_applications_ids_from_beneficiary_imports is temporary.
#       It should be removed when all the current imports are done.
#       Check: 08/03/2022 @lixxday or #skwadak in slack
def get_already_processed_applications_ids(procedure_id: int) -> set[int]:
    return get_already_processed_applications_ids_from_beneficiary_imports(
        procedure_id
    ) | get_already_processed_applications_ids_from_fraud_checks(procedure_id)


def get_already_processed_applications_ids_from_beneficiary_imports(procedure_id: int) -> set[int]:
    return {
        beneficiary_import.applicationId
        for beneficiary_import in BeneficiaryImport.query.join(BeneficiaryImportStatus)
        .filter(
            BeneficiaryImportStatus.status.in_(
                [ImportStatus.CREATED, ImportStatus.REJECTED, ImportStatus.DUPLICATE, ImportStatus.ERROR]
            )
        )
        .options(load_only(BeneficiaryImport.applicationId))
        .filter(BeneficiaryImport.sourceId == procedure_id)
        .all()
    }


def get_already_processed_applications_ids_from_fraud_checks(procedure_id: int) -> set[int]:
    fraud_check_qs = fraud_models.BeneficiaryFraudCheck.query.filter(
        fraud_models.BeneficiaryFraudCheck.type == fraud_models.FraudCheckType.DMS,
        fraud_models.BeneficiaryFraudCheck.resultContent["procedure_id"].astext.cast(Integer) == procedure_id,
        fraud_models.BeneficiaryFraudCheck.status.in_(
            [
                fraud_models.FraudCheckStatus.KO,
                fraud_models.FraudCheckStatus.OK,
                fraud_models.FraudCheckStatus.SUSPICIOUS,
                fraud_models.FraudCheckStatus.CANCELED,
                fraud_models.FraudCheckStatus.ERROR,
            ]
        ),
    )
    fraud_check_ids = {
        int(fraud_check.thirdPartyId) for fraud_check in fraud_check_qs.options(load_only("thirdPartyId")).all()
    }
    orphans_qs = fraud_models.OrphanDmsApplication.query.filter(
        fraud_models.OrphanDmsApplication.process_id == procedure_id
    )
    orphans_ids = {orphan.application_id for orphan in orphans_qs.options(load_only("application_id")).all()}

    return fraud_check_ids | orphans_ids
