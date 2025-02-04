import logging

import googlemaps
import pydantic

from pcapi import settings
from pcapi.core.object_storage import delete_public_object
from pcapi.core.object_storage import store_public_object
from pcapi.core.offerers import models as offerers_models
from pcapi.models import db
from pcapi.utils import image_conversion


logger = logging.getLogger(__name__)


GOOGLE_PLACES_BANNER_STORAGE_FOLDER = settings.THUMBS_FOLDER_NAME + "/google_places"


class PlacePhoto(pydantic.BaseModel):
    height: int
    html_attributions: list[str]
    photo_reference: str
    width: int


class PlaceDetails(pydantic.BaseModel):
    name: str
    photos: list[PlacePhoto] | None = None


class FindPlaceCandidate(pydantic.BaseModel):
    place_id: str


class FindPlaceResponse(pydantic.BaseModel):
    candidates: list[FindPlaceCandidate]
    status: str


class PlaceResponse(pydantic.BaseModel):
    html_attributions: list[str]
    result: PlaceDetails
    status: str


def get_venues_without_photo(begin: int, end: int | None, limit: int | None = None) -> list[offerers_models.Venue]:
    query = (
        offerers_models.Venue.query.join(offerers_models.Offerer)
        .filter(
            offerers_models.Venue.isPermanent.is_(True),
            offerers_models.Venue.bannerUrl.is_(None),  # type: ignore [attr-defined]
            offerers_models.Venue.venueTypeCode != "Lieu administratif",
            offerers_models.Offerer.isActive.is_(True),
            offerers_models.Venue.id >= begin,
        )
        .order_by(offerers_models.Venue.id)
    )
    if end is not None:
        query = query.filter(offerers_models.Venue.id <= end)
    if limit is not None:
        query = query.limit(limit)
    venues = query.all()
    return venues


def get_place_id(name: str, address: str | None) -> str | None:
    gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
    address = address or ""
    result = FindPlaceResponse.model_validate(
        gmaps.find_place(input=name + address, input_type="textquery", fields=["place_id"])
    )
    if result.status != "OK" or not result.candidates:
        return None
    return result.candidates[0].place_id


def is_the_owner(name: str, photo: PlacePhoto) -> bool:
    for attr in photo.html_attributions:
        if name in attr:
            return True
    return False


def get_place_photos_and_owner(place_id: str) -> PlaceDetails | None:
    gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
    result = PlaceResponse.model_validate(gmaps.place(place_id=place_id, fields=["photo", "name"]))
    if result.status != "OK":
        return None
    return result.result


def get_owner_photo(photos: list[PlacePhoto], owner_name: str) -> PlacePhoto | None:
    for photo in photos:
        if is_the_owner(owner_name, photo):
            return photo
    return None


def save_photo_to_gcp(venue_id: int, photo: PlacePhoto, prefix: str) -> str:
    gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
    photos_result = gmaps.places_photo(
        photo_reference=photo.photo_reference,
        max_width=photo.width,
    )
    object_id = f"{prefix}{venue_id}.jpeg"
    data = bytes()
    for chunk in photos_result:
        if chunk:
            data += chunk
    store_public_object(
        GOOGLE_PLACES_BANNER_STORAGE_FOLDER,
        object_id,
        image_conversion.standardize_image(
            content=data,
            ratio=image_conversion.ImageRatio.LANDSCAPE,
        ),
        "image/jpeg",
    )
    return settings.OBJECT_STORAGE_URL + "/" + GOOGLE_PLACES_BANNER_STORAGE_FOLDER + "/" + object_id


def synchronize_venues_banners_with_google_places(
    start_venue_id: int, end_venue_id: int | None, limit: int | None
) -> None:
    venues_without_photos = get_venues_without_photo(start_venue_id, end_venue_id, limit)
    print("the number of venues is:", len(venues_without_photos))
    logger.info(
        "[gmaps_banner_synchro] synchronize_venues_banners_with_google_places %s %s %s: the number of venues tried: %s",
        start_venue_id,
        end_venue_id,
        limit,
        len(venues_without_photos),
    )
    nb_places_found = 0
    nb_places_with_photo = 0
    nb_places_with_owner_photo = 0
    for venue in venues_without_photos:
        if venue.googlePlacesInfo:
            nb_places_found += 1
        else:
            place_id = get_place_id(venue.name, venue.address)
            if not place_id:
                continue
            venue.googlePlacesInfo = offerers_models.GooglePlacesInfo(placeId=place_id)

        nb_places_found += 1
        place_details = get_place_photos_and_owner(venue.googlePlacesInfo.placeId)
        if not (place_details and place_details.photos):
            continue
        nb_places_with_photo += 1

        owner_photo = get_owner_photo(place_details.photos, place_details.name)
        if owner_photo:
            photo = owner_photo
            photo_prefix = "owner"
            nb_places_with_owner_photo += 1
        else:
            photo = place_details.photos[0]
            photo_prefix = ""
        try:
            venue.googlePlacesInfo.bannerUrl = save_photo_to_gcp(venue.id, photo, photo_prefix)
            venue.googlePlacesInfo.bannerMeta = photo.model_dump()
        except Exception as e:  # pylint: disable=broad-except
            logger.exception(
                "[gmaps_banner_synchro]venue id: %s error %s: ",
                venue.id,
                e,
                extra={"venue_id": venue.id, "error": e},
            )
            continue
    db.session.commit()
    logger.info(
        "Synchronized venues with Google Places",
        extra={
            "nb_places_fetched": len(venues_without_photos),
            "nb_places_found": nb_places_found,
            "nb_places_with_photo": nb_places_with_photo,
            "nb_places_with_owner_photo": nb_places_with_owner_photo,
        },
    )


def delete_venues_banners(start_venue_id: int, end_venue_id: int | None, limit: int | None) -> None:
    logger.info(
        "deleting old google places banners",
        extra={
            "begin": start_venue_id,
            "end": end_venue_id,
            "limit": limit,
        },
    )
    google_places_info_query = offerers_models.GooglePlacesInfo.query.filter(
        offerers_models.GooglePlacesInfo.venueId >= start_venue_id,
        offerers_models.GooglePlacesInfo.bannerUrl.is_not(None),
    ).order_by(offerers_models.GooglePlacesInfo.venueId)
    nb_deleted_banners = 0
    if end_venue_id is not None:
        google_places_info_query = google_places_info_query.filter(
            offerers_models.GooglePlacesInfo.venueId <= end_venue_id
        )
    if limit is not None:
        google_places_info_query = google_places_info_query.limit(limit)
    for place_info in google_places_info_query:
        try:
            delete_public_object(GOOGLE_PLACES_BANNER_STORAGE_FOLDER, place_info.bannerUrl.split("/")[-1])
        except Exception as e:  # pylint: disable=broad-except
            logger.exception(
                "error deleting google banner %s for venue %s: %s",
                place_info.bannerUrl,
                place_info.venueId,
                e,
                extra={"banner_url": place_info.bannerUrl, "venue_id": place_info.venueId, "error": e},
            )
            continue
        nb_deleted_banners += 1
        place_info.bannerUrl = None
        place_info.bannerMeta = None
    db.session.commit()
    logger.info(
        "deleted old google places banners",
        extra={
            "number of banners deleted": nb_deleted_banners,
        },
    )
