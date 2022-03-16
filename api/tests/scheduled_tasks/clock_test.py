from datetime import datetime
from datetime import timedelta

import pytest

from pcapi.core.bookings import constants
from pcapi.core.bookings import factories as bookings_factories
from pcapi.core.bookings.models import BookingStatus
from pcapi.core.offers import factories as offers_factories
from pcapi.core.testing import override_settings
from pcapi.core.users import factories as users_factories
from pcapi.notifications.push import testing
from pcapi.scheduled_tasks.clock import pc_notify_users_bookings_not_retrieved
from pcapi.scheduled_tasks.clock import pc_send_tomorrow_events_notifications


@pytest.mark.usefixtures("db_session")
def test_pc_send_tomorrow_events_notifications_only_to_individual_bookings_users():
    """
    Test that each stock that is linked to an offer that occurs tomorrow and
    creates a job that will send a notification to all of the stock's users
    with a valid (not cancelled) booking, for individual bookings only.
    """
    tomorrow = datetime.now() + timedelta(days=1)
    stock_tomorrow = offers_factories.EventStockFactory(beginningDatetime=tomorrow, offer__name="my_offer")

    next_week = datetime.now() + timedelta(days=7)
    stock_next_week = offers_factories.EventStockFactory(beginningDatetime=next_week)

    user1 = users_factories.BeneficiaryGrant18Factory()
    user2 = users_factories.BeneficiaryGrant18Factory()

    # should be fetched
    bookings_factories.IndividualBookingFactory(stock=stock_tomorrow, user=user1)

    # should not be fetched: cancelled
    bookings_factories.IndividualBookingFactory(stock=stock_tomorrow, status=BookingStatus.CANCELLED, user=user2)

    # should not be fetched: educational
    bookings_factories.EducationalBookingFactory(stock=stock_tomorrow, user=user2)

    # should not be fetched: next week
    bookings_factories.IndividualBookingFactory(stock=stock_next_week, user=user2)

    pc_send_tomorrow_events_notifications()

    assert len(testing.requests) == 1
    assert all(data["message"]["title"] == "my_offer, c'est demain !" for data in testing.requests)

    user_ids = {user_id for data in testing.requests for user_id in data["user_ids"]}
    assert user_ids == {user1.id}


@pytest.mark.usefixtures("db_session")
@override_settings(SOON_EXPIRING_BOOKINGS_DAYS_BEFORE_EXPIRATION=3)
def test_pc_notify_users_bookings_not_retrieved() -> None:
    user = users_factories.BeneficiaryGrant18Factory()
    stock = offers_factories.ThingStockFactory()
    creation_date = datetime.now() - constants.BOOKINGS_AUTO_EXPIRY_DELAY + timedelta(days=3)

    # booking that will expire in three days
    booking = bookings_factories.IndividualBookingFactory(user=user, stock=stock, dateCreated=creation_date)

    pc_notify_users_bookings_not_retrieved()
    assert len(testing.requests) == 1

    data = testing.requests[0]
    assert data["user_ids"] == [booking.userId]
    assert data["message"]["title"] == "Tu n'as pas récupéré ta réservation"
    assert (
        data["message"]["body"] == f'Vite, il ne te reste plus que 3 jours pour récupérer "{booking.stock.offer.name}"'
    )
