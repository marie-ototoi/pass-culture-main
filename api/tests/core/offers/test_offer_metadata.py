import datetime

import pytest

from pcapi.core.categories import subcategories_v2
import pcapi.core.offers.factories as offers_factories
from pcapi.core.offers.offer_metadata import get_metadata_from_offer


pytestmark = pytest.mark.usefixtures("db_session")


class OfferMetadataTest:
    def should_always_have_a_context(self):
        offer = offers_factories.OfferFactory()

        metadata = get_metadata_from_offer(offer)

        assert metadata["@context"] == "https://schema.org"

    def should_always_have_a_name(self):
        offer = offers_factories.OfferFactory(
            name="Naheulbeuk Tome 1",
        )

        metadata = get_metadata_from_offer(offer)

        assert metadata["name"] == "Naheulbeuk Tome 1"

    def should_can_have_an_image(self):
        offer = offers_factories.OfferFactory()
        offers_factories.MediationFactory(id=111, offer=offer, thumbCount=1)

        metadata = get_metadata_from_offer(offer)

        assert metadata["image"] == "http://localhost/storage/thumbs/mediations/N4"

    def should_can_have_no_image(self):
        offer = offers_factories.OfferFactory()

        metadata = get_metadata_from_offer(offer)

        assert "image" not in metadata

    def test_can_have_a_description(self):
        offer = offers_factories.OfferFactory(description="Pass valable partout")

        metadata = get_metadata_from_offer(offer)

        assert metadata["description"] == "Pass valable partout"

    def test_can_have_no_description(self):
        offer = offers_factories.OfferFactory(description=None)

        metadata = get_metadata_from_offer(offer)

        assert "description" not in metadata

    class OfferTest:
        def should_have_an_offer(self):
            offer = offers_factories.OfferFactory()
            offers_factories.StockFactory(offer=offer, price=5.10)

            metadata = get_metadata_from_offer(offer)

            assert metadata["offers"]["@type"] == "AggregateOffer"

        def should_have_a_low_price(self):
            offer = offers_factories.OfferFactory()
            offers_factories.StockFactory(offer=offer, price=5.10)
            offers_factories.StockFactory(offer=offer, price=2)

            metadata = get_metadata_from_offer(offer)

            assert metadata["offers"]["lowPrice"] == "2.00"

        def should_have_a_price_currency(self):
            offer = offers_factories.OfferFactory()
            offers_factories.StockFactory(offer=offer, price=5.10)

            metadata = get_metadata_from_offer(offer)

            assert metadata["offers"]["priceCurrency"] == "EUR"

    class GivenAnEventTest:
        def should_describe_an_event(self):
            offer = offers_factories.EventOfferFactory()

            metadata = get_metadata_from_offer(offer)

            assert metadata["@type"] == "Event"

        def should_describe_an_event_for_a_concert(self):
            offer = offers_factories.OfferFactory(subcategoryId=subcategories_v2.CONCERT.id)

            metadata = get_metadata_from_offer(offer)

            assert metadata["@type"] == "Event"

        def should_describe_an_event_for_a_festival(self):
            offer = offers_factories.OfferFactory(subcategoryId=subcategories_v2.FESTIVAL_MUSIQUE.id)

            metadata = get_metadata_from_offer(offer)

            assert metadata["@type"] == "Event"

        def should_define_a_start_date(self):
            stock = offers_factories.EventStockFactory(beginningDatetime=datetime.datetime(2023, 5, 3, 12, 39, 0))

            metadata = get_metadata_from_offer(stock.offer)

            assert metadata["startDate"] == "2023-05-03T12:39"

        def should_have_a_location(self):
            offer = offers_factories.EventOfferFactory(
                venue__name="Le Poney qui tousse",
                venue__address="Rue du Poney qui tousse",
                venue__postalCode="75001",
                venue__city="Boulgourville",
                venue__latitude="47.097456",
                venue__longitude="-1.270040",
            )

            metadata = get_metadata_from_offer(offer)

            assert metadata["location"] == {
                "@type": "Place",
                "name": "Le Poney qui tousse",
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": "Rue du Poney qui tousse",
                    "postalCode": "75001",
                    "addressLocality": "Boulgourville",
                },
                "geo": {
                    "@type": "GeoCoordinates",
                    "latitude": "47.09746",
                    "longitude": "-1.27004",
                },
            }

        def should_have_an_url(self):
            offer = offers_factories.EventOfferFactory(id=72180399)

            offers_factories.StockFactory(offer=offer)

            metadata = get_metadata_from_offer(offer)

            assert metadata["offers"]["url"] == "https://webapp-v2.example.com/offre/72180399"

        def should_have_online_event_attendance_mode(self):
            offer = offers_factories.EventOfferFactory(url="https://passculture.app/offre/72180399")

            metadata = get_metadata_from_offer(offer)

            assert metadata["eventAttendanceMode"] == "OnlineEventAttendanceMode"

        def should_have_offline_event_attendance_mode(self):
            offer = offers_factories.EventOfferFactory()

            metadata = get_metadata_from_offer(offer)

            assert metadata["eventAttendanceMode"] == "OfflineEventAttendanceMode"

        def should_have_valid_from_date(self):
            offer = offers_factories.EventOfferFactory(extraData={"releaseDate": "2000-01-01"})

            metadata = get_metadata_from_offer(offer)

            assert metadata["validFrom"] == "2000-01-01"

    class GivenABookTest:
        @pytest.mark.parametrize(
            "subcategoryId",
            [
                subcategories_v2.LIVRE_PAPIER.id,
                subcategories_v2.LIVRE_AUDIO_PHYSIQUE.id,
                subcategories_v2.TELECHARGEMENT_LIVRE_AUDIO.id,
                subcategories_v2.LIVRE_NUMERIQUE.id,
            ],
        )
        def should_describe_a_book_as_additional_type(self, subcategoryId):
            offer = offers_factories.OfferFactory(subcategoryId=subcategoryId)

            metadata = get_metadata_from_offer(offer)

            assert metadata["additionalType"] == "Book"

        def should_define_an_author(self):
            offer = offers_factories.OfferFactory(
                subcategoryId=subcategories_v2.LIVRE_PAPIER.id, extraData={"author": "John Doe"}
            )

            metadata = get_metadata_from_offer(offer)

            assert metadata["author"] == {"@type": "Person", "name": "John Doe"}

        def should_define_an_isbn(self):
            offer = offers_factories.OfferFactory(
                subcategoryId=subcategories_v2.LIVRE_PAPIER.id, extraData={"ean": 9782371266124}
            )

            metadata = get_metadata_from_offer(offer)

            assert metadata["gtin13"] == 9782371266124

    class GivenAThingTest:
        def should_describe_a_product(self):
            offer = offers_factories.ThingOfferFactory()

            metadata = get_metadata_from_offer(offer)

            assert metadata["@type"] == "Product"
