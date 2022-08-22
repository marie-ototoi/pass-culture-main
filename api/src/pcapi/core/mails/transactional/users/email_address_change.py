from pcapi.core import mails
from pcapi.core.mails.models.sendinblue_models import SendinblueTransactionalEmailData
from pcapi.core.mails.transactional.sendinblue_template_ids import TransactionalEmail
from pcapi.core.users.models import User


def get_information_email_change_data(first_name: str) -> SendinblueTransactionalEmailData:
    return SendinblueTransactionalEmailData(
        template=TransactionalEmail.EMAIL_CHANGE_REQUEST.value,
        params={
            "FIRSTNAME": first_name,
        },
    )


def send_information_email_change_email(user: User) -> bool:
    data = get_information_email_change_data(user.firstName)  # type: ignore [arg-type]
    return mails.send(recipients=[user.email], data=data)


def get_confirmation_email_change_data(first_name: str, confirmation_link: str) -> SendinblueTransactionalEmailData:
    return SendinblueTransactionalEmailData(
        template=TransactionalEmail.EMAIL_CHANGE_CONFIRMATION.value,
        params={"FIRSTNAME": first_name, "CONFIRMATION_LINK": confirmation_link},
    )


def send_confirmation_email_change_email(user: User, new_email: str, confirmation_link: str) -> bool:
    data = get_confirmation_email_change_data(user.firstName, confirmation_link)  # type: ignore [arg-type]
    return mails.send(recipients=[new_email], data=data)


def send_pro_confirmation_email_change_email(new_email: str, confirmation_link: str) -> bool:
    data = get_pro_confirmation_email_change_data(confirmation_link)
    return mails.send(recipients=[new_email], data=data)


def get_pro_confirmation_email_change_data(confirmation_link: str) -> SendinblueTransactionalEmailData:
    return SendinblueTransactionalEmailData(
        template=TransactionalEmail.PRO_EMAIL_CHANGE_CONFIRMATION.value,
        params={"CONFIRMATION_LINK": confirmation_link},
    )


def send_pro_information_email_change_email(user: User, new_email: str) -> bool:
    data = get_pro_information_email_change_data(new_email, user.email)
    return mails.send(recipients=[user.email], data=data)


def get_pro_information_email_change_data(new_email: str, old_email: str) -> SendinblueTransactionalEmailData:
    return SendinblueTransactionalEmailData(
        template=TransactionalEmail.PRO_EMAIL_CHANGE_REQUEST.value,
        params={"NEW_EMAIL": new_email, "OLD_EMAIL": old_email},
    )
