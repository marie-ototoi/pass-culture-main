from pcapi.core.fraud import models as fraud_models
from pcapi.core.users import models as users_models


def reimport_users(user_ids):
    for user_id in user_ids:
        user = users_models.User.query.get(user_id)
        if user.is_beneficiary:
            print("already bene")
            continue
        dms_apps = fraud_models.BeneficiaryFraudCheck.query.filter_by(
            userId=user_id, type=fraud_models.FraudCheckType.DMS
        ).all()
        if len(dms_apps) > 1:
            print("several------------", user_id)
            continue
        if not dms_apps:
            print("no app++++++++++++++", user_id)
            continue
        fraud_check = dms_apps[0]
        print(fraud_check.thirdPartyId)
