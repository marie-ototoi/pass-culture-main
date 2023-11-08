import datetime
import typing

from pcapi.core.categories import subcategories_v2
from pcapi.core.offerers.models import Venue
import pcapi.core.offers.models as offers_models
from pcapi.core.offers.utils import offer_app_link


Metadata = dict[str, typing.Any]
book_subcategories = [
    subcategories_v2.LIVRE_AUDIO_PHYSIQUE.id,
    subcategories_v2.TELECHARGEMENT_LIVRE_AUDIO.id,
    subcategories_v2.LIVRE_NUMERIQUE.id,
    subcategories_v2.LIVRE_PAPIER.id,
]


def _get_metadata_from_venue(venue: Venue) -> Metadata:
    return {
        "@type": "Place",
        "name": venue.name,
        "address": {
            "@type": "PostalAddress",
            "streetAddress": venue.address,
            "postalCode": venue.postalCode,
            "addressLocality": venue.city,
        },
        "geo": {
            "@type": "GeoCoordinates",
            "latitude": str(venue.latitude),
            "longitude": str(venue.longitude),
        },
    }


def _get_common_metadata_from_offer(offer: offers_models.Offer) -> Metadata:
    metadata: Metadata = {
        "@type": "Product",
        "name": offer.name,
    }

    if offer.description:
        metadata["description"] = offer.description

    if offer.image:
        metadata["image"] = offer.image.url

    if offer.stocks:
        metadata["offers"] = {
            "@type": "AggregateOffer",
            "priceCurrency": "EUR",
            "lowPrice": str(offer.min_price),
            "url": offer_app_link(offer),
        }

    return metadata


def _get_event_metadata_from_offer(offer: offers_models.Offer) -> Metadata:
    common_metadata = _get_common_metadata_from_offer(offer)

    event_metadata = {
        "@type": "Event",
        "location": _get_metadata_from_venue(offer.venue),
    }

    if offer.firstBeginningDatetime:
        firstBeginningDatetime: datetime.datetime = offer.firstBeginningDatetime
        event_metadata["startDate"] = firstBeginningDatetime.isoformat(timespec="minutes")

    event_metadata["eventAttendanceMode"] = (
        "OnlineEventAttendanceMode" if offer.isDigital else "OfflineEventAttendanceMode"
    )

    if offer.extraData and offer.extraData.get("releaseDate"):
        event_metadata["validFrom"] = str(offer.extraData["releaseDate"])

    return common_metadata | event_metadata


def _get_book_metadata_from_offer(offer: offers_models.Offer) -> Metadata:
    book_metadata: Metadata = {
        "additionalType": "Book",
    }

    extra_data = offer.extraData or {}
    if ean := extra_data.get("ean"):
        book_metadata["gtin13"] = ean
    if author := extra_data.get("author"):
        book_metadata["author"] = {
            "@type": "Person",
            "name": author,
        }

    return _get_common_metadata_from_offer(offer) | book_metadata


def get_metadata_from_offer(offer: offers_models.Offer) -> Metadata:
    context = {
        "@context": "https://schema.org",
    }

    if offer.isEvent:
        return context | _get_event_metadata_from_offer(offer)

    if offer.subcategory.id in book_subcategories:
        return context | _get_book_metadata_from_offer(offer)

    return context | _get_common_metadata_from_offer(offer)
