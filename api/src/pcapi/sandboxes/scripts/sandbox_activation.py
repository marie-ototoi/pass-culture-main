from pcapi.core.categories import subcategories
import pcapi.core.offerers.factories as offerers_factories
from pcapi.model_creators.specific_creators import create_offer_with_thing_product
from pcapi.model_creators.specific_creators import create_stock_with_thing_offer
from pcapi.repository import repository


def save_sandbox() -> None:
    offerer = offerers_factories.OffererFactory()
    venue = offerers_factories.VirtualVenueFactory(offerer)
    offer = create_offer_with_thing_product(venue, thing_subcategory_id=subcategories.ACTIVATION_THING.id)
    stock = create_stock_with_thing_offer(offerer, venue, offer=offer, price=0, quantity=10000)
    repository.save(stock)
