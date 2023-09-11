import logging
import typing

import pydantic.v1 as pydantic

from pcapi.connectors.serialization.titelive_serializers import GenreTitelive
from pcapi.connectors.serialization.titelive_serializers import TiteliveMusicArticle
from pcapi.connectors.serialization.titelive_serializers import TiteliveMusicOeuvre
from pcapi.connectors.serialization.titelive_serializers import TiteliveProductSearchResponse
from pcapi.connectors.titelive import TiteliveBase
from pcapi.core.categories import subcategories_v2 as subcategories
from pcapi.core.offers import models as offers_models
from pcapi.domain import music_types

from .constants import MUSIC_SLUG_BY_GTL_ID
from .titelive_api import TiteliveSearch


logger = logging.getLogger(__name__)


class TiteliveMusicSearch(TiteliveSearch[TiteliveMusicOeuvre]):
    titelive_base = TiteliveBase.MUSIC

    def deserialize_titelive_search_json(
        self, titelive_json_response: dict[str, typing.Any]
    ) -> TiteliveProductSearchResponse[TiteliveMusicOeuvre]:
        return pydantic.parse_obj_as(TiteliveProductSearchResponse[TiteliveMusicOeuvre], titelive_json_response)

    def upsert_titelive_result_in_dict(
        self, titelive_search_result: TiteliveMusicOeuvre, products_by_ean: dict[str, offers_models.Product]
    ) -> dict[str, offers_models.Product]:
        title = titelive_search_result.titre
        genre_titelive = get_genre_titelive(titelive_search_result)
        for article in titelive_search_result.article:
            ean = article.gencod
            product = products_by_ean.get(ean)
            if product is None:
                products_by_ean[ean] = self.create_product(article, title, genre_titelive)
            else:
                products_by_ean[ean] = self.update_product(article, title, genre_titelive, product)

        return products_by_ean

    def create_product(
        self, article: TiteliveMusicArticle, title: str, genre: GenreTitelive | None
    ) -> offers_models.Product:
        return offers_models.Product(
            description=article.resume,
            extraData=build_music_extra_data(article, genre),
            idAtProviders=article.gencod,
            lastProvider=self.provider,
            name=title,
            subcategoryId=parse_titelive_product_format(article.codesupport),
        )

    def update_product(
        self, article: TiteliveMusicArticle, title: str, genre: GenreTitelive | None, product: offers_models.Product
    ) -> offers_models.Product:
        product.description = article.resume
        if product.extraData is None:
            product.extraData = offers_models.OfferExtraData()
        product.extraData.update(build_music_extra_data(article, genre))
        product.idAtProviders = article.gencod
        product.name = title
        product.subcategoryId = parse_titelive_product_format(article.codesupport)

        return product


def get_genre_titelive(titelive_search_result: TiteliveMusicOeuvre) -> GenreTitelive | None:
    titelive_gtl = next((article.gtl for article in titelive_search_result.article if article.gtl is not None), None)
    if not titelive_gtl:
        logger.warning("Genre Titelive not found for music %s", titelive_search_result.titre)
        return None

    most_precise_genre = max(titelive_gtl.first.values(), key=lambda g: g.code)
    return most_precise_genre


def build_music_extra_data(article: TiteliveMusicArticle, genre: GenreTitelive | None) -> offers_models.OfferExtraData:
    gtl_id = genre.code if genre else None
    music_type, music_subtype = parse_titelive_music_genre(gtl_id)

    return offers_models.OfferExtraData(
        artist=article.artiste,
        author=article.compositeur,
        comment=article.commentaire,
        date_parution=article.dateparution.isoformat() if article.dateparution else None,
        dispo=article.dispo,
        distributeur=article.distributeur,
        ean=article.gencod,
        editeur=article.editeur,
        gtl_id=gtl_id,
        music_label=article.label,
        musicSubType=str(music_subtype.code),
        musicType=str(music_type.code),
        nb_galettes=article.nb_galettes,
        performer=article.interprete,
    )


def parse_titelive_music_genre(gtl_id: str | None) -> tuple[music_types.MusicType, music_types.MusicSubType]:
    music_slug = (
        MUSIC_SLUG_BY_GTL_ID.get(gtl_id, music_types.OTHER_SHOW_TYPE_SLUG)
        if gtl_id
        else music_types.OTHER_SHOW_TYPE_SLUG
    )
    return (
        music_types.MUSIC_TYPES_BY_SLUG[music_slug],
        music_types.MUSIC_SUB_TYPES_BY_SLUG[music_slug],
    )


def parse_titelive_product_format(codesupport: str) -> str:
    return subcategories.SUPPORT_PHYSIQUE_MUSIQUE.id
