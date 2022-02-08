from dataclasses import dataclass
from datetime import date
from datetime import datetime
from datetime import timedelta
import logging
import typing
from typing import Optional

from dateutil.relativedelta import relativedelta
import sqlalchemy
from sqlalchemy import orm as sa_orm
from sqlalchemy.sql.functions import func

from pcapi.core.bookings.models import Booking
from pcapi.core.fraud import models as fraud_models
from pcapi.core.offerers.models import Offerer
from pcapi.core.offers.models import Offer
from pcapi.core.offers.models import Stock
from pcapi.core.users.models import Favorite
from pcapi.core.users.utils import sanitize_email
from pcapi.models import db
from pcapi.models.user_offerer import UserOfferer
from pcapi.repository import repository
from pcapi.utils import crypto

from . import constants
from . import exceptions
from . import models


logger = logging.getLogger(__name__)


HASHED_PLACEHOLDER = crypto.hash_password("placeholder")


def check_user_and_credentials(user: models.User, password: str) -> None:
    # Order is important to prevent end-user to guess user emails
    # We need to check email and password before checking email validation
    if not user:
        # Hash the given password, just like we would do if the user
        # existed. This avoids user enumeration by comparing server
        # response time.
        crypto.check_password(password, HASHED_PLACEHOLDER)
        raise exceptions.InvalidIdentifier()
    if not user.checkPassword(password) or not user.isActive:
        logging.info("Failed authentication attempt", extra={"user": user.id, "avoid_current_user": True})
        raise exceptions.InvalidIdentifier()
    if not user.isValidated or not user.isEmailValidated:
        raise exceptions.UnvalidatedAccount()


def get_user_with_credentials(identifier: str, password: str) -> models.User:
    user = find_user_by_email(identifier)
    check_user_and_credentials(user, password)
    return user


def _find_user_by_email_query(email: str):
    # FIXME (dbaty, 2021-05-02): remove call to `func.lower()` once
    # all emails have been sanitized in the database.
    return models.User.query.filter(func.lower(models.User.email) == sanitize_email(email))


def find_user_by_email(email: str) -> Optional[models.User]:
    return _find_user_by_email_query(email).one_or_none()


def find_pro_user_by_email(email: str) -> Optional[models.User]:
    return _find_user_by_email_query(email).filter(models.User.has_pro_role.is_(True)).one_or_none()


def get_user_with_valid_token(
    token_value: str, token_types: list[models.TokenType], use_token: bool = True
) -> Optional[models.User]:
    token = models.Token.query.filter(
        models.Token.value == token_value, models.Token.type.in_(token_types), models.Token.isUsed == False
    ).one_or_none()
    if not token:
        return None

    if token.expirationDate and token.expirationDate < datetime.now():
        return None

    if use_token:
        token.isUsed = True
        repository.save(token)

    return token.user


def get_newly_eligible_age_18_users(since: date) -> list[models.User]:
    """get users that are eligible between `since` (excluded) and now (included) and that have
    created their account before `since`"""
    today = datetime.combine(datetime.today(), datetime.min.time())
    since = datetime.combine(since, datetime.min.time())
    eligible_users = (
        models.User.query.outerjoin(UserOfferer)
        .filter(
            models.User.has_beneficiary_role == False,  # not already beneficiary
            models.User.has_admin_role == False,  # not an admin
            UserOfferer.userId.is_(None),  # not a pro
            models.User.dateOfBirth > today - relativedelta(years=(constants.ELIGIBILITY_AGE_18 + 1)),  # less than 19yo
            models.User.dateOfBirth <= today - relativedelta(years=constants.ELIGIBILITY_AGE_18),  # more than or 18yo
            models.User.dateOfBirth
            > since - relativedelta(years=constants.ELIGIBILITY_AGE_18),  # less than 18yo at since
            models.User.dateCreated < today,
        )
        .all()
    )
    return eligible_users


def get_favorites_for_offers(offer_ids: list[int]) -> list[models.Favorite]:
    return models.Favorite.query.filter(models.Favorite.offerId.in_(offer_ids)).all()


def does_validated_phone_exist(phone_number: str) -> bool:
    return bool(
        models.User.query.filter(models.User.phoneNumber == phone_number, models.User.is_phone_validated).count()
    )


def get_users_with_validated_attachment_by_offerer(offerer: Offerer) -> models.User:
    return (
        models.User.query.join(UserOfferer)
        .filter(UserOfferer.validationToken.is_(None), UserOfferer.offererId == offerer.id)
        .all()
    )


def get_earliest_identity_check_date_of_eligibility(
    user: models.User, eligibility: models.EligibilityType
) -> Optional[datetime]:
    return (
        db.session.query(sqlalchemy.func.min(fraud_models.BeneficiaryFraudCheck.dateCreated))
        .filter(
            fraud_models.BeneficiaryFraudCheck.type != fraud_models.FraudCheckType.INTERNAL_REVIEW,
            fraud_models.BeneficiaryFraudCheck.eligibilityType == eligibility,
            fraud_models.BeneficiaryFraudCheck.user == user,
        )
        .scalar()
    )


def get_inactive_favorites_for_notification() -> typing.Generator[Favorite, None, None]:
    """
    Find favorites that:
        * have been created three days ago;
        * have not been booked by the user;
        * are linked to an offer with some stock and that is not expired;
        * have not been marked as sent (notification).

    These favorites can be used to sent notifications to their users.
    This is why the three days ago rule: no need to send a notification
    to user that added a favorite a few hours ago (for example).
    """
    three_days_ago = date.today() - timedelta(days=3)

    return (
        Favorite.query.distinct(Favorite.id)  # remove duplicate rows explicitly
        .options(
            sa_orm.contains_eager(Favorite.offer).load_only(Offer.id, Offer.subcategoryId),
            sa_orm.contains_eager(Favorite.user).load_only(models.User.id),
        )
        .join(Offer)
        .join(Stock)
        .join(Booking, isouter=True)
        .filter(Favorite.extra["notification"] == None)
        .filter(Favorite.dateCreated <= three_days_ago)
        .filter(Stock.quantity > 0)
        .filter(sqlalchemy.not_(Stock.isExpired))
        .filter(Booking.id.is_(None))
        .yield_per(1_000)
    )


@dataclass
class SubcategoryCount:
    user_id: int
    subcategory: str
    count: int


def get_subcategories_count_per_user(
    user_ids: typing.Iterable[int], subcategory_ids: typing.Iterable[str]
) -> list[SubcategoryCount]:
    """
    For a subset of users and subcategories (offers), compute the number
    of booking each user has made for each category.
    """
    rows = (
        Booking.query.join(Stock)
        .join(Offer)
        .group_by(Booking.userId, Offer.subcategoryId)
        .filter(Booking.userId.in_(user_ids))
        .filter(Offer.subcategoryId.in_(subcategory_ids))
        .with_entities(Booking.userId, Offer.subcategoryId, func.count(Offer.subcategoryId))
    )

    return [SubcategoryCount(user_id=row[0], subcategory=row[1], count=row[2]) for row in rows]
