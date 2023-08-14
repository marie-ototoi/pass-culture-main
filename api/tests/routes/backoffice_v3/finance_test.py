import datetime

from flask import url_for
import pytest

from pcapi.core import testing
from pcapi.core.bookings import factories as bookings_factories
from pcapi.core.finance import factories as finance_factories
from pcapi.core.finance import models as finance_models
from pcapi.core.history import factories as history_factories
from pcapi.core.history import models as history_models
from pcapi.core.offerers import factories as offerers_factories
from pcapi.core.offers import factories as offers_factories
from pcapi.core.permissions import models as perm_models
from pcapi.core.testing import assert_num_queries
from pcapi.routes.backoffice_v3.finance.blueprint import _cancel_finance_incident

from .helpers import html_parser
from .helpers.get import GetEndpointHelper
from .helpers.post import PostEndpointHelper


pytestmark = [
    pytest.mark.usefixtures("db_session"),
    pytest.mark.backoffice_v3,
]


class ListIncidentsTest(GetEndpointHelper):
    endpoint = "backoffice_v3_web.finance_incident.list_incidents"
    needed_permission = perm_models.Permissions.READ_INCIDENTS

    expected_num_queries = 0
    expected_num_queries += 1  # Fetch Session
    expected_num_queries += 1  # Fetch User
    expected_num_queries += 1  # Fetch Finance Incidents

    def test_list_incidents_without_filter(self, authenticated_client):
        incidents = finance_factories.FinanceIncidentFactory.create_batch(10)

        url = url_for(self.endpoint)

        with testing.assert_num_queries(self.expected_num_queries):
            response = authenticated_client.get(url)
            assert response.status_code == 200

        rows = html_parser.extract_table_rows(response.data)
        assert len(rows) == len(incidents)
        assert rows[0]["ID"] == str(incidents[0].id)
        assert rows[0]["Statut de l'incident"] == "Créé"
        assert rows[0]["Type d'incident"] == "Trop Perçu"


class GetIncidentCancellationFormTest(GetEndpointHelper):
    endpoint = "backoffice_v3_web.finance_incident.get_finance_incident_cancellation_form"
    endpoint_kwargs = {"finance_incident_id": 1}
    needed_permission = perm_models.Permissions.MANAGE_INCIDENTS

    def test_get_incident_cancellation_form(self, legit_user, authenticated_client):
        incident = finance_factories.FinanceIncidentFactory()
        url = url_for(self.endpoint, finance_incident_id=incident.id)
        response = authenticated_client.get(url)

        assert response.status_code == 200


class CancelIncidentTest(PostEndpointHelper):
    endpoint = "backoffice_v3_web.finance_incident.cancel_finance_incident"
    endpoint_kwargs = {"finance_incident_id": 1}
    needed_permission = perm_models.Permissions.MANAGE_INCIDENTS

    def test_cancel_incident(self, legit_user, authenticated_client):
        incident = finance_factories.FinanceIncidentFactory()
        self.form_data = {"comment": "L'incident n'est pas conforme"}

        response = self.post_to_endpoint(authenticated_client, finance_incident_id=incident.id, form=self.form_data)

        assert response.status_code == 200

        assert (
            finance_models.FinanceIncident.query.filter(
                finance_models.FinanceIncident.status == finance_models.IncidentStatus.CREATED
            ).count()
            == 0
        )

        badges = html_parser.extract(response.data, tag="span", class_="badge")
        assert "Annulé" in badges

        action_history = history_models.ActionHistory.query.one()
        assert action_history.actionType == history_models.ActionType.FINANCE_INCIDENT_CANCELLED
        assert action_history.authorUser == legit_user
        assert action_history.comment == self.form_data["comment"]

    def test_cancel_already_cancelled_incident(self, authenticated_client):
        incident = finance_factories.FinanceIncidentFactory(status=finance_models.IncidentStatus.CANCELLED)
        self.form_data = {"comment": "L'incident n'est pas conforme"}

        response = self.post_to_endpoint(authenticated_client, finance_incident_id=incident.id, form=self.form_data)

        assert response.status_code == 200

        assert "L'incident a déjà été annulé" in html_parser.extract_alert(response.data)
        assert history_models.ActionHistory.query.count() == 0

    def test_cancel_already_validated_incident(self, authenticated_client):
        incident = finance_factories.FinanceIncidentFactory(status=finance_models.IncidentStatus.VALIDATED)
        self.form_data = {"comment": "L'incident n'est pas conforme"}

        response = self.post_to_endpoint(authenticated_client, finance_incident_id=incident.id, form=self.form_data)

        assert response.status_code == 200

        assert "Impossible d'annuler un incident déjà validé" in html_parser.extract_alert(response.data)
        assert history_models.ActionHistory.query.count() == 0


class GetIncidentTest(GetEndpointHelper):
    endpoint = "backoffice_v3_web.finance_incident.get_incident"
    endpoint_kwargs = {"finance_incident_id": 1}
    needed_permission = perm_models.Permissions.READ_INCIDENTS
    expected_num_queries = 0
    expected_num_queries += 1  # Fetch Session
    expected_num_queries += 1  # Fetch User
    expected_num_queries += 1  # Fetch Incidents infos
    expected_num_queries += 1  # Fetch Reimbursement point infos

    def test_get_incident(self, authenticated_client, finance_incident):
        url = url_for(self.endpoint, finance_incident_id=finance_incident.id)

        with assert_num_queries(self.expected_num_queries):
            response = authenticated_client.get(url)
            assert response.status_code == 200

        content = html_parser.content_as_text(response.data)

        assert f"ID : {finance_incident.id}" in content
        assert f" Lieu porteur de l'offre : {finance_incident.venue.name}" in content
        assert f"Incident créé par : {finance_incident.details['author']}" in content


class GetIncidentCreationFormTest(PostEndpointHelper):
    endpoint = "backoffice_v3_web.finance_incident.get_incident_creation_form"
    needed_permission = perm_models.Permissions.MANAGE_INCIDENTS

    error_message = "Seules les réservations ayant le statut 'remboursée' et correspondant au même lieu peuvent faire l'objet d'un incident"

    expected_num_queries = 7

    def test_get_incident_creation_for_one_booking_form(self, authenticated_client):
        venue = offerers_factories.VenueFactory()
        offer = offers_factories.OfferFactory(venue=venue)
        stock = offers_factories.StockFactory(offer=offer)
        booking = bookings_factories.ReimbursedBookingFactory(stock=stock)
        object_ids = str(booking.id)

        with assert_num_queries(self.expected_num_queries):
            response = self.post_to_endpoint(authenticated_client, form={"object_ids": object_ids})

        assert response.status_code == 200
        additionnal_data_text = html_parser.extract_cards_text(response.data)[0]
        assert f"Lieu : {venue.name}" in additionnal_data_text
        assert f"ID de la réservation : {booking.id}" in additionnal_data_text
        assert f"Statut de la réservation : {booking.status.name}" in additionnal_data_text
        assert f"Contremarque : {booking.token}" in additionnal_data_text
        assert f"Nom de l'offre : {offer.name}" in additionnal_data_text
        assert f"Bénéficiaire : {booking.user.full_name}" in additionnal_data_text

    def test_get_incident_creation_for_multiple_bookings_form(self, authenticated_client):
        venue = offerers_factories.VenueFactory()
        offer = offers_factories.OfferFactory(venue=venue)
        stock = offers_factories.StockFactory(offer=offer)
        selected_bookings = [
            bookings_factories.ReimbursedBookingFactory(stock=stock),
            bookings_factories.ReimbursedBookingFactory(stock=stock),
        ]
        object_ids = ",".join([str(booking.id) for booking in selected_bookings])

        with assert_num_queries(self.expected_num_queries):
            response = self.post_to_endpoint(authenticated_client, form={"object_ids": object_ids})

        assert response.status_code == 200
        additionnal_data_text = html_parser.extract_cards_text(response.data)[0]
        assert f"Lieu : {venue.name}" in additionnal_data_text
        assert f"Nombre de réservations : {len(selected_bookings)}" in additionnal_data_text

    def test_display_error_if_booking_not_reimbursed(self, authenticated_client):
        booking = bookings_factories.UsedBookingFactory()
        object_ids = str(booking.id)

        with assert_num_queries(self.expected_num_queries):
            response = self.post_to_endpoint(authenticated_client, form={"object_ids": object_ids})

        assert self.error_message in html_parser.content_as_text(response.data)

    def test_display_error_if_bookings_from_different_venues_selected(self, authenticated_client):
        selected_bookings = [
            bookings_factories.ReimbursedBookingFactory(),
            bookings_factories.ReimbursedBookingFactory(),
        ]
        object_ids = ",".join(str(booking.id) for booking in selected_bookings)

        with assert_num_queries(self.expected_num_queries):
            response = self.post_to_endpoint(authenticated_client, form={"object_ids": object_ids})

        assert self.error_message in html_parser.content_as_text(response.data)


class CreateIncidentTest(PostEndpointHelper):
    endpoint = "backoffice_v3_web.finance_incident.create_incident"
    needed_permission = perm_models.Permissions.MANAGE_INCIDENTS

    def test_create_incident_from_one_booking(self, legit_user, authenticated_client):
        pricing = finance_factories.PricingFactory(status=finance_models.PricingStatus.INVOICED)
        booking = bookings_factories.ReimbursedBookingFactory(pricings=[pricing])

        object_ids = str(booking.id)

        response = self.post_to_endpoint(
            authenticated_client,
            form={
                "total_amount": booking.amount,
                "origin": "Origine de la demande",
                "kind": finance_models.IncidentType.OVERPAYMENT.name,
                "object_ids": object_ids,
            },
        )

        assert response.status_code == 301
        assert finance_models.FinanceIncident.query.count() == 1
        assert finance_models.BookingFinanceIncident.query.count() == 1
        booking_finance_incident = finance_models.BookingFinanceIncident.query.first()
        assert booking_finance_incident.newTotalAmount == int(
            booking.amount * 100
        )  # incident amount is stored as cents

        action_history = history_models.ActionHistory.query.one()
        assert action_history.actionType == history_models.ActionType.FINANCE_INCIDENT_CREATED
        assert action_history.authorUser == legit_user
        assert action_history.comment == "Origine de la demande"

    def test_not_creating_incident_if_already_exists(self, authenticated_client):
        booking = bookings_factories.ReimbursedBookingFactory()
        finance_factories.IndividualBookingFinanceIncidentFactory(booking=booking)
        object_ids = str(booking.id)

        response = self.post_to_endpoint(
            authenticated_client,
            form={
                "total_amount": booking.amount,
                "origin": "Origine de la demande",
                "kind": finance_models.IncidentType.OVERPAYMENT.name,
                "object_ids": object_ids,
            },
        )

        assert response.status_code == 301
        assert finance_models.FinanceIncident.query.count() == 1  # didn't create new incident

        assert history_models.ActionHistory.query.count() == 0

    def test_create_incident_from_multiple_booking(self, legit_user, authenticated_client):
        venue = offerers_factories.VenueFactory()
        offer = offers_factories.OfferFactory(venue=venue)
        stock = offers_factories.StockFactory(offer=offer)
        selected_bookings = [
            bookings_factories.ReimbursedBookingFactory(
                stock=stock, pricings=[finance_factories.PricingFactory(status=finance_models.PricingStatus.INVOICED)]
            ),
            bookings_factories.ReimbursedBookingFactory(
                stock=stock, pricings=[finance_factories.PricingFactory(status=finance_models.PricingStatus.INVOICED)]
            ),
        ]
        object_ids = ",".join([str(booking.id) for booking in selected_bookings])
        total_booking_amount = sum(booking.amount for booking in selected_bookings)

        response = self.post_to_endpoint(
            authenticated_client,
            form={
                "total_amount": total_booking_amount,
                "origin": "Origine de la demande",
                "kind": finance_models.IncidentType.OVERPAYMENT.name,
                "object_ids": object_ids,
            },
        )

        assert response.status_code == 301
        assert finance_models.FinanceIncident.query.count() == 1
        finance_incident = finance_models.FinanceIncident.query.first()
        assert finance_incident.details["origin"] == "Origine de la demande"
        assert finance_models.BookingFinanceIncident.query.count() == 2

        action_history = history_models.ActionHistory.query.one()
        assert action_history.actionType == history_models.ActionType.FINANCE_INCIDENT_CREATED
        assert action_history.authorUser == legit_user
        assert action_history.comment == "Origine de la demande"


class GetIncidentHistoryTest(GetEndpointHelper):
    endpoint = "backoffice_v3_web.finance_incident.get_history"
    endpoint_kwargs = {"finance_incident_id": 1}
    needed_permission = perm_models.Permissions.READ_INCIDENTS

    def test_get_incident_history(self, legit_user, authenticated_client):
        finance_incident = finance_factories.FinanceIncidentFactory()
        action = history_factories.ActionHistoryFactory(
            financeIncident=finance_incident,
            actionType=history_models.ActionType.FINANCE_INCIDENT_CREATED,
            actionDate=datetime.datetime.utcnow() + datetime.timedelta(days=-1),
        )
        _cancel_finance_incident(finance_incident, comment="Je décide d'annuler l'incident")

        response = authenticated_client.get(url_for(self.endpoint, finance_incident_id=finance_incident.id))
        assert response.status_code == 200

        rows = html_parser.extract_table_rows(response.data)
        assert len(rows) == 2
        iterator_actions = iter(rows)
        cancel_action = next(iterator_actions)
        creation_action = next(iterator_actions)
        assert cancel_action["Type"] == history_models.ActionType.FINANCE_INCIDENT_CANCELLED.value
        assert creation_action["Type"] == history_models.ActionType.FINANCE_INCIDENT_CREATED.value
        assert creation_action["Date/Heure"].startswith(action.actionDate.strftime("Le %d/%m/%Y à "))
        assert creation_action["Commentaire"] == action.comment
        assert creation_action["Auteur"] == action.authorUser.full_name
