import dataclasses
from datetime import datetime
from decimal import Decimal
import enum
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import BigInteger
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import relationship
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.schema import Index
from sqlalchemy.sql.sqltypes import Boolean
from sqlalchemy.sql.sqltypes import Numeric

from pcapi.core.bookings import exceptions as booking_exceptions
from pcapi.core.educational import exceptions
from pcapi.models import Model
from pcapi.models.offer_mixin import AccessibilityMixin
from pcapi.models.offer_mixin import OfferValidationStatus
from pcapi.models.offer_mixin import StatusMixin
from pcapi.models.offer_mixin import ValidationMixin
from pcapi.models.pc_object import PcObject


class StudentLevels(enum.Enum):
    COLLEGE4 = "Collège - 4e"
    COLLEGE3 = "Collège - 3e"
    CAP1 = "CAP - 1re année"
    CAP2 = "CAP - 2e année"
    GENERAL2 = "Lycée - Seconde"
    GENERAL1 = "Lycée - Première"
    GENERAL0 = "Lycée - Terminale"


class EducationalBookingStatus(enum.Enum):
    REFUSED = "REFUSED"


class Ministry(enum.Enum):
    EDUCATION_NATIONALE = "MENjs"
    MER = "MMe"
    AGRICULTURE = "MAg"
    ARMEES = "MAr"


class CollectiveBooking(PcObject, Model):
    pass


class CollectiveOffer(PcObject, ValidationMixin, AccessibilityMixin, StatusMixin, Model):
    __tablename__ = "collective_offer"

    # add 3 mixin validation, status accessibilite

    id: int = Column(BigInteger, primary_key=True, autoincrement=True)

    isActive = Column(Boolean, nullable=False, server_default=sa.sql.expression.true(), default=True)

    venueId = sa.Column(sa.BigInteger, sa.ForeignKey("venue.id"), nullable=False, index=True)

    venue = sa.orm.relationship("Venue", foreign_keys=[venueId], backref="offers")

    name = sa.Column(sa.String(140), nullable=False)

    bookingEmail = sa.Column(sa.String(120), nullable=True)

    description = sa.Column(sa.Text, nullable=True)

    durationMinutes = sa.Column(sa.Integer, nullable=True)

    dateCreated = sa.Column(sa.DateTime, nullable=False, default=datetime.utcnow)

    subcategoryId = sa.Column(sa.Text, nullable=False, index=True)

    dateUpdated: datetime = sa.Column(sa.DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow)

    students: list[str] = sa.Column(
        MutableList.as_mutable(postgresql.ARRAY(sa.Enum(StudentLevels))),
        nullable=False,
        server_default="{}",
    )

    contactEmail = sa.Column(sa.String(120), nullable=False)

    contactPhone = sa.Column(sa.String(20), nullable=False)

    offerVenue = Column("jsonData", postgresql.JSONB)

    @sa.ext.hybrid.hybrid_property
    def isSoldOut(self):
        # todo redefinir
        for stock in self.stocks:
            if (
                not stock.isSoftDeleted
                and (stock.beginningDatetime is None or stock.beginningDatetime > datetime.utcnow())
                and (stock.remainingQuantity == "unlimited" or stock.remainingQuantity > 0)
            ):
                return False
        return True

    @isSoldOut.expression
    def isSoldOut(cls):  # pylint: disable=no-self-argument
        # TODO redefine
        return (
            ~sa.exists()
            .where(CollectiveStock.offerId == cls.id)
            .where(CollectiveStock.isSoftDeleted.is_(False))
            .where(
                sa.or_(CollectiveStock.beginningDatetime > sa.func.now(), CollectiveStock.beginningDatetime.is_(None))
            )
            .where(sa.or_(CollectiveStock.remainingQuantity.is_(None), CollectiveStock.remainingQuantity > 0))
        )

    @property
    def isBookable(self) -> bool:
        # TODO redifinir
        for stock in self.stocks:
            if stock.isBookable:
                return True
        return False

    @property
    def isReleased(self) -> bool:
        return (
            self.isActive
            and self.validation == OfferValidationStatus.APPROVED
            and self.venue.isValidated
            and self.venue.managingOfferer.isActive
            and self.venue.managingOfferer.isValidated
        )

    @sa.ext.hybrid.hybrid_property
    def hasBookingLimitDatetimesPassed(self) -> bool:
        if self.activeStocks:
            return all(stock.hasBookingLimitDatetimePassed for stock in self.activeStocks)
        return False

    @hasBookingLimitDatetimesPassed.expression
    def hasBookingLimitDatetimesPassed(cls):  # pylint: disable=no-self-argument
        return sa.and_(
            sa.exists().where(CollectiveStock.offerId == cls.id).where(CollectiveStock.isSoftDeleted.is_(False)),
            ~sa.exists()
            .where(CollectiveStock.offerId == cls.id)
            .where(CollectiveStock.isSoftDeleted.is_(False))
            .where(CollectiveStock.hasBookingLimitDatetimePassed.is_(False)),
        )


class CollectiveStock(PcObject, Model):
    pass


class EducationalInstitution(PcObject, Model):
    __tablename__ = "educational_institution"

    id: int = Column(BigInteger, primary_key=True, autoincrement=True)

    institutionId: str = Column(String(30), nullable=False, unique=True, index=True)


class EducationalYear(PcObject, Model):
    __tablename__ = "educational_year"

    id: int = Column(BigInteger, primary_key=True, autoincrement=True)

    adageId: str = Column(String(30), unique=True, nullable=False)

    beginningDate: datetime = Column(DateTime, nullable=False)

    expirationDate: datetime = Column(DateTime, nullable=False)


class EducationalDeposit(PcObject, Model):
    __tablename__ = "educational_deposit"

    TEMPORARY_FUND_AVAILABLE_RATIO = 0.8

    id: int = Column(BigInteger, primary_key=True, autoincrement=True)

    educationalInstitutionId = Column(BigInteger, ForeignKey("educational_institution.id"), index=True, nullable=False)

    educationalInstitution: EducationalInstitution = relationship(
        EducationalInstitution, foreign_keys=[educationalInstitutionId], backref="deposits"
    )

    educationalYearId = Column(String(30), ForeignKey("educational_year.adageId"), index=True, nullable=False)

    educationalYear: EducationalYear = relationship(
        EducationalYear, foreign_keys=[educationalYearId], backref="deposits"
    )

    amount: Decimal = Column(Numeric(10, 2), nullable=False)

    dateCreated: datetime = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())

    isFinal: bool = Column(Boolean, nullable=False, default=True)

    ministry = Column(
        Enum(Ministry),
        nullable=True,
    )

    def get_amount(self) -> Decimal:
        return round(self.amount * Decimal(self.TEMPORARY_FUND_AVAILABLE_RATIO), 2) if not self.isFinal else self.amount

    def check_has_enough_fund(self, total_amount_after_booking: Decimal) -> None:
        if self.amount < total_amount_after_booking:
            raise exceptions.InsufficientFund()

        if self.get_amount() < total_amount_after_booking and not self.isFinal:
            raise exceptions.InsufficientTemporaryFund()

        return


class EducationalRedactor(PcObject, Model):

    __tablename__ = "educational_redactor"

    id: int = Column(BigInteger, primary_key=True, autoincrement=True)

    email: str = Column(String(120), nullable=False, unique=True, index=True)

    firstName: str = Column(String(128), nullable=True)

    lastName: str = Column(String(128), nullable=True)

    civility: str = Column(String(20), nullable=True)

    educationalBookings = relationship(
        "EducationalBooking",
        back_populates="educationalRedactor",
    )


class EducationalBooking(PcObject, Model):
    __tablename__ = "educational_booking"

    id: int = Column(BigInteger, primary_key=True, autoincrement=True)

    educationalInstitutionId = Column(BigInteger, ForeignKey("educational_institution.id"), nullable=False)
    educationalInstitution: EducationalInstitution = relationship(
        EducationalInstitution, foreign_keys=[educationalInstitutionId], backref="educationalBookings"
    )

    educationalYearId = Column(String(30), ForeignKey("educational_year.adageId"), nullable=False)
    educationalYear: EducationalYear = relationship(EducationalYear, foreign_keys=[educationalYearId])

    Index("ix_educational_booking_educationalYear_and_institution", educationalYearId, educationalInstitutionId)

    status = Column(
        "status",
        Enum(EducationalBookingStatus),
        nullable=True,
    )

    confirmationDate: Optional[datetime] = Column(DateTime, nullable=True)
    confirmationLimitDate = Column(DateTime, nullable=True)

    booking = relationship(
        "Booking",
        back_populates="educationalBooking",
        uselist=False,
        lazy="joined",
        innerjoin=True,
    )

    educationalRedactorId = Column(
        BigInteger,
        ForeignKey("educational_redactor.id"),
        nullable=False,
        index=True,
    )
    educationalRedactor: EducationalRedactor = relationship(
        EducationalRedactor,
        back_populates="educationalBookings",
        uselist=False,
    )

    def has_confirmation_limit_date_passed(self) -> bool:
        return bool(self.confirmationLimitDate and self.confirmationLimitDate <= datetime.utcnow())

    def mark_as_refused(self) -> None:
        from pcapi.core.bookings import models as bookings_models

        if (
            self.booking.status != bookings_models.BookingStatus.PENDING
            and self.booking.cancellationLimitDate <= datetime.utcnow()
        ):
            raise exceptions.EducationalBookingNotRefusable()

        try:
            self.booking.cancel_booking()
            self.booking.cancellationReason = bookings_models.BookingCancellationReasons.REFUSED_BY_INSTITUTE
        except booking_exceptions.BookingIsAlreadyUsed:
            raise exceptions.EducationalBookingNotRefusable()
        except booking_exceptions.BookingIsAlreadyCancelled:
            raise exceptions.EducationalBookingAlreadyCancelled()

        self.status = EducationalBookingStatus.REFUSED


@dataclasses.dataclass
class AdageApiResult:
    sent_data: dict
    response: dict
    success: bool
