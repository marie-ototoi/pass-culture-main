from datetime import datetime, timedelta

import pytest
from freezegun import freeze_time

from models import Offer, Thing, Event, PcObject, ApiErrors, EventOccurrence
from tests.conftest import clean_database
from utils.test_utils import create_event_occurrence, create_thing, create_thing_offer, create_offerer, create_venue

now = datetime.utcnow()
two_days_ago = now - timedelta(days=2)
four_days_ago = now - timedelta(days=4)
five_days_from_now = now + timedelta(days=5)
ten_days_from_now = now + timedelta(days=10)


@pytest.mark.standalone
def test_date_range_is_empty_if_offer_is_on_a_thing():
    # given
    offer = Offer()
    offer.thing = Thing()
    offer.eventOccurrences = []

    # then
    assert offer.dateRange == []


@pytest.mark.standalone
def test_date_range_matches_the_occurrence_if_only_one_occurrence():
    # given
    offer = Offer()
    offer.event = Event()
    offer.eventOccurrences = [
        create_event_occurrence(offer, beginning_datetime=two_days_ago, end_datetime=five_days_from_now)
    ]

    # then
    assert offer.dateRange == [two_days_ago, five_days_from_now]


@pytest.mark.standalone
def test_date_range_starts_at_first_beginning_date_time_and_ends_at_last_end_date_time():
    # given
    offer = Offer()
    offer.event = Event()
    offer.eventOccurrences = [
        create_event_occurrence(offer, beginning_datetime=two_days_ago, end_datetime=five_days_from_now),
        create_event_occurrence(offer, beginning_datetime=four_days_ago, end_datetime=five_days_from_now),
        create_event_occurrence(offer, beginning_datetime=four_days_ago, end_datetime=ten_days_from_now),
        create_event_occurrence(offer, beginning_datetime=two_days_ago, end_datetime=ten_days_from_now)
    ]

    # then
    assert offer.dateRange == [four_days_ago, ten_days_from_now]


@pytest.mark.standalone
def test_date_range_is_empty_if_event_has_no_event_occurrences():
    # given
    offer = Offer()
    offer.event = Event()
    offer.eventOccurrences = []

    # then
    assert offer.dateRange == []


@clean_database
@pytest.mark.standalone
def test_offer_error_when_thing_is_digital_but_venue_not_virtual(app):
    # Given
    digital_thing = create_thing(thing_type='ThingType.JEUX_VIDEO', url='http://mygame.fr/offre')
    offerer = create_offerer()
    physical_venue = create_venue(offerer)
    PcObject.check_and_save(physical_venue)
    offer = create_thing_offer(physical_venue, digital_thing)

    # When
    with pytest.raises(ApiErrors) as errors:
        PcObject.check_and_save(offer)

    # Then
    assert errors.value.errors['venue'] == ['Une offre numérique doit obligatoirement être associée au lieu "Offre en ligne"']


@freeze_time('2018-09-01 10:10:10')
def test_offer_as_dict_returns_dateRange_in_ISO_8601():
    # Given
    eventOccurrence = EventOccurrence()
    eventOccurrence.beginningDatetime = now
    eventOccurrence.endDatetime = now + timedelta(hours=3)
    offer = Offer()
    offer.eventOccurrences = [eventOccurrence]
    # When
    offer_dict = offer._asdict()
    # Then
    print(offer_dict)
    assert offer_dict['ateRange'] == ['2018-09-01T10:10:10Z', '2018-09-01T10:13:10Z']
