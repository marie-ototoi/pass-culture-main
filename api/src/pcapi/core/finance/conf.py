import decimal
from enum import Enum

from pcapi.core.offers import models as offers_models

from . import models


GRANT_18_VALIDITY_IN_YEARS = 2

GRANTED_DEPOSIT_AMOUNT_15 = decimal.Decimal(20)
GRANTED_DEPOSIT_AMOUNT_16 = decimal.Decimal(30)
GRANTED_DEPOSIT_AMOUNT_17 = decimal.Decimal(30)
GRANTED_DEPOSIT_AMOUNT_18_v1 = decimal.Decimal(500)
GRANTED_DEPOSIT_AMOUNT_18_v2 = decimal.Decimal(300)

GRANT_18_DIGITAL_CAP_V1 = decimal.Decimal(200)
GRANT_18_DIGITAL_CAP_V2 = decimal.Decimal(100)
GRANT_18_PHYSICAL_CAP_V1 = decimal.Decimal(200)
GRANT_18_PHYSICAL_CAP_V2 = None

WALLIS_AND_FUTUNA_DEPARTMENT_CODE = "986"


GRANTED_DEPOSIT_AMOUNTS_FOR_UNDERAGE_BY_AGE = {
    15: GRANTED_DEPOSIT_AMOUNT_15,
    16: GRANTED_DEPOSIT_AMOUNT_16,
    17: GRANTED_DEPOSIT_AMOUNT_17,
}

GRANTED_DEPOSIT_AMOUNTS_FOR_18_BY_VERSION = {
    1: GRANTED_DEPOSIT_AMOUNT_18_v1,  # not used anymore, still present in database
    2: GRANTED_DEPOSIT_AMOUNT_18_v2,
}


RECREDIT_TYPE_AGE_MAPPING = {
    16: models.RecreditType.RECREDIT_16,
    17: models.RecreditType.RECREDIT_17,
}

RECREDIT_TYPE_AMOUNT_MAPPING = {
    models.RecreditType.RECREDIT_16: GRANTED_DEPOSIT_AMOUNT_16,
    models.RecreditType.RECREDIT_17: GRANTED_DEPOSIT_AMOUNT_17,
}


def digital_cap_applies_to_offer(offer: offers_models.Offer) -> bool:
    return offer.isDigital and offer.subcategory.is_digital_deposit


def physical_cap_applies_to_offer(offer: offers_models.Offer) -> bool:
    return not offer.isDigital and offer.subcategory.is_physical_deposit


class SpecificCaps:
    DIGITAL_CAP = None
    PHYSICAL_CAP = None

    def __init__(self, digital_cap: decimal.Decimal | None, physical_cap: decimal.Decimal | None) -> None:
        self.DIGITAL_CAP = digital_cap
        self.PHYSICAL_CAP = physical_cap

    def digital_cap_applies(self, offer: offers_models.Offer) -> bool:
        return digital_cap_applies_to_offer(offer) and bool(self.DIGITAL_CAP)

    def physical_cap_applies(self, offer: offers_models.Offer) -> bool:
        return physical_cap_applies_to_offer(offer) and bool(self.PHYSICAL_CAP)


# TODO(fseguin|dbaty, 2022-01-11): maybe merge with core.categories.subcategories.ReimbursementRuleChoices ?
class RuleGroups(Enum):
    STANDARD = dict(
        label="Barème général",
        position=1,
    )
    BOOK = dict(
        label="Barème livres",
        position=2,
    )
    NOT_REIMBURSED = dict(
        label="Barème non remboursé",
        position=3,
    )
    CUSTOM = dict(
        label="Barème dérogatoire",
        position=4,
    )
    DEPRECATED = dict(
        label="Barème désuet",
        position=5,
    )
