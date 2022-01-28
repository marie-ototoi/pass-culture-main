from pcapi.core.fraud.models import BeneficiaryFraudCheck
from pcapi.core.fraud.models import FraudCheckStatus
from pcapi.core.fraud.models import FraudCheckType
from pcapi.core.users.models import User
from pcapi.repository import repository


def re_import_id_piece_number():
    fraud_checks = BeneficiaryFraudCheck.query.filter(
        BeneficiaryFraudCheck.type == FraudCheckType.UBBLE,
        BeneficiaryFraudCheck.status == FraudCheckStatus.OK,
    ).all()
    print(f"Total number of fraud checks : {len(fraud_checks)}")
    filtered_fraud_checks = [fc for fc in fraud_checks if fc.user.is_beneficiary and not fc.user.idPieceNumber]
    print(f"Number of fraud checks with user beneficiary and not updated : {len(filtered_fraud_checks)}")
    already_saved = []
    to_save = {}
    duplicates_in_to_save = {}
    missing_ids_user_id = []
    for fraud_check in filtered_fraud_checks:
        id_document_number = fraud_check.source_data().id_document_number
        if not id_document_number:
            missing_ids_user_id.append(fraud_check.userId)
            continue
        user_with_same_id = User.query.filter(User.idPieceNumber == id_document_number).first()
        if user_with_same_id:
            already_saved.append((fraud_check.userId, user_with_same_id.id))
            continue
        if id_document_number in to_save:
            if id_document_number in duplicates_in_to_save:
                duplicates_in_to_save[id_document_number].update((to_save[id_document_number], fraud_check.userId))
            else:
                duplicates_in_to_save[id_document_number] = {to_save[id_document_number], fraud_check.userId}
            continue
        to_save[id_document_number] = fraud_check.userId
    return to_save, already_saved, duplicates_in_to_save, missing_ids_user_id


def save_id_pn(to_save: dict):
    new_to_save = {}
    several_id_pn = []
    for id_piece_number, user_id in to_save.items():
        if id_piece_number in duplicates_in_to_save and len(duplicates_in_to_save[id_piece_number]) > 1:
            print("not saving", id_piece_number, duplicates_in_to_save[id_piece_number])
            continue
        if user_id in new_to_save:
            print("several ids", user_id)
            several_id_pn.append(user_id)
            continue
        new_to_save[user_id] = id_piece_number
    k = 0
    ids = sorted(list(new_to_save.keys()))
    print("several_id", several_id_pn)
    print("len ids to update", len(ids))
    already_id_pn = []
    while k < len(ids):
        print("index", k)
        updated = []
        users = User.query.filter(User.id.in_(ids[k : k + 1000])).all()
        for user in users:
            if user.idPieceNumber:
                print("already idPieceNumber", user.id)
                already_id_pn.append(user.id)
                continue
            user.idPieceNumber = new_to_save[user.id]
            updated.append(user)
        repository.save(*updated)
        k += 1000
        print("updated", len(updated))
