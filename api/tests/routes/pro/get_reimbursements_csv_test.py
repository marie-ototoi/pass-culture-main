import csv
import datetime
from io import StringIO
import urllib.parse

import pytest

from pcapi.core.bookings import models as bookings_models
from pcapi.core.educational import models as educational_models
import pcapi.core.finance.factories as finance_factories
import pcapi.core.finance.models as finance_models
import pcapi.core.offerers.factories as offerers_factories
from pcapi.core.offers import models as offers_models
from pcapi.core.testing import assert_num_queries
from pcapi.core.testing import override_features
import pcapi.core.users.factories as users_factories
from pcapi.routes.serialization.reimbursement_csv_serialize import ReimbursementDetails
from pcapi.utils.date import utc_datetime_to_department_timezone


@pytest.mark.usefixtures("db_session")
def test_with_venue_filter(client):
    period = datetime.date(2021, 1, 1), datetime.date(2021, 1, 15)
    offerer = offerers_factories.OffererFactory()
    venue1 = offerers_factories.VenueFactory(managingOfferer=offerer, pricing_point="self")
    venue2 = offerers_factories.VenueFactory(managingOfferer=offerer, pricing_point=venue1)
    for venue in (venue1, venue2):
        finance_factories.PaymentStatusFactory(
            payment__booking__stock__offer__venue=venue,
            status=finance_models.TransactionStatus.SENT,
            payment__transactionLabel="pass Culture Pro - remboursement 1ère quinzaine 01-21",
            date=datetime.datetime(2021, 1, 1),
        )
    pro = users_factories.ProFactory()
    offerers_factories.UserOffererFactory(user=pro, offerer=offerer)

    # When
    client = client.with_session_auth(pro.email)
    response = client.get(
        "/reimbursements/csv?"
        + urllib.parse.urlencode(
            {
                "reimbursementPeriodBeginningDate": period[0].isoformat(),
                "reimbursementPeriodEndingDate": period[1].isoformat(),
                "venueId": venue1.id,
            }
        )
    )

    # Then
    assert response.status_code == 200
    assert response.headers["Content-type"] == "text/csv; charset=utf-8;"
    assert response.headers["Content-Disposition"] == "attachment; filename=remboursements_pass_culture.csv"
    rows = response.data.decode("utf-8").splitlines()
    assert len(rows) == 1 + 1  # header + payments


@pytest.mark.usefixtures("db_session")
def test_with_reimbursement_period_filter(client):
    period = datetime.date(2021, 1, 1), datetime.date(2021, 1, 15)
    user_offerer = offerers_factories.UserOffererFactory()
    offerer = user_offerer.offerer
    pro = user_offerer.user
    finance_factories.PaymentStatusFactory(
        payment__booking__stock__offer__venue__managingOfferer=offerer,
        payment__booking__stock__offer__venue__pricing_point="self",
        status=finance_models.TransactionStatus.SENT,
        payment__transactionLabel="pass Culture Pro - remboursement 1ère quinzaine 01-21",
        date=datetime.datetime(2021, 1, 1),  # in requested period
    )
    finance_factories.PaymentStatusFactory(
        payment__booking__stock__offer__venue__managingOfferer=offerer,
        payment__booking__stock__offer__venue__pricing_point="self",
        status=finance_models.TransactionStatus.SENT,
        payment__transactionLabel="xxx",
        date=datetime.datetime(2020, 12, 1),  # before requested period
    )
    finance_factories.PaymentStatusFactory(
        payment__booking__stock__offer__venue__managingOfferer=offerer,
        payment__booking__stock__offer__venue__pricing_point="self",
        status=finance_models.TransactionStatus.SENT,
        payment__transactionLabel="pass Culture Pro - remboursement 2ème quinzaine 01-21",
        date=datetime.datetime(2021, 1, 4),  # in requested period
    )
    finance_factories.PaymentStatusFactory(
        payment__booking__stock__offer__venue__managingOfferer=offerer,
        payment__booking__stock__offer__venue__pricing_point="self",
        status=finance_models.TransactionStatus.SENT,
        payment__transactionLabel="xxx",
        date=datetime.datetime(2021, 2, 1),  # after requested period
    )

    # When
    client = client.with_session_auth(pro.email)
    response = client.get(
        "/reimbursements/csv?"
        + urllib.parse.urlencode(
            {
                "reimbursementPeriodBeginningDate": period[0].isoformat(),
                "reimbursementPeriodEndingDate": period[1].isoformat(),
            }
        )
    )

    # Then
    assert response.status_code == 200
    assert response.headers["Content-type"] == "text/csv; charset=utf-8;"
    assert response.headers["Content-Disposition"] == "attachment; filename=remboursements_pass_culture.csv"
    rows = response.data.decode("utf-8").splitlines()
    assert len(rows) == 1 + 2  # header + payments


@pytest.mark.usefixtures("db_session")
def test_without_reimbursement_period(client):
    user_offerer = offerers_factories.UserOffererFactory()
    pro = user_offerer.user

    # When
    response = client.with_session_auth(pro.email).get("/reimbursements/csv")

    # Then
    assert response.status_code == 400
    assert response.json["reimbursementPeriodBeginningDate"] == [
        "Vous devez renseigner une date au format ISO (ex. 2021-12-24)"
    ]
    assert response.json["reimbursementPeriodEndingDate"] == [
        "Vous devez renseigner une date au format ISO (ex. 2021-12-24)"
    ]


@pytest.mark.usefixtures("db_session")
def test_admin_can_access_reimbursements_data_with_venue_filter(client):
    # Given
    period = datetime.date(2021, 1, 1), datetime.date(2021, 1, 15)
    admin = users_factories.AdminFactory()
    user_offerer = offerers_factories.UserOffererFactory()
    offerer = user_offerer.offerer
    status = finance_factories.PaymentStatusFactory(
        payment__booking__stock__offer__venue__managingOfferer=offerer,
        payment__booking__stock__offer__venue__pricing_point="self",
        status=finance_models.TransactionStatus.SENT,
        payment__transactionLabel="pass Culture Pro - remboursement 1ère quinzaine 06-21",
        date=datetime.datetime(2021, 1, 1),
    )
    venue = status.payment.booking.venue

    # When
    client = client.with_session_auth(admin.email)
    response = client.get(
        "/reimbursements/csv?"
        + urllib.parse.urlencode(
            {
                "reimbursementPeriodBeginningDate": period[0].isoformat(),
                "reimbursementPeriodEndingDate": period[1].isoformat(),
                "venueId": venue.id,
            }
        )
    )

    # Then
    assert response.status_code == 200
    assert response.headers["Content-type"] == "text/csv; charset=utf-8;"
    assert response.headers["Content-Disposition"] == "attachment; filename=remboursements_pass_culture.csv"
    rows = response.data.decode("utf-8").splitlines()
    assert len(rows) == 2  # header + payments


@pytest.mark.usefixtures("db_session")
def test_admin_cannot_access_reimbursements_data_without_venue_filter(client):
    # Given
    period = datetime.date(2021, 1, 1), datetime.date(2021, 1, 15)
    admin = users_factories.AdminFactory()

    # When
    client = client.with_session_auth(admin.email)
    response = client.get(
        "/reimbursements/csv?"
        + urllib.parse.urlencode(
            {
                "reimbursementPeriodBeginningDate": period[0].isoformat(),
                "reimbursementPeriodEndingDate": period[1].isoformat(),
            }
        )
    )

    # Then
    assert response.status_code == 400


### Old bankInformation journey (with pricings) ###


@pytest.mark.usefixtures("db_session")
@override_features(WIP_ENABLE_NEW_BANK_DETAILS_JOURNEY=False)
def test_with_venue_filter_old_bank_information_journey_with_pricings(client):
    beginning_date_iso_format = (datetime.date.today() - datetime.timedelta(days=2)).isoformat()
    ending_date_iso_format = (datetime.date.today() + datetime.timedelta(days=2)).isoformat()
    offerer = offerers_factories.OffererFactory()
    venue1 = offerers_factories.VenueFactory(managingOfferer=offerer, pricing_point="self")
    finance_factories.BankInformationFactory(venue=venue1)
    venue2 = offerers_factories.VenueFactory(managingOfferer=offerer, pricing_point=venue1)
    finance_factories.BankInformationFactory(venue=venue2)
    batch = finance_factories.CashflowBatchFactory()

    for venue in (venue1, venue2):
        invoice = finance_factories.InvoiceFactory(reimbursementPoint=venue, date=datetime.date.today())
        cashflow = finance_factories.CashflowFactory(
            batch=batch, creationDate=datetime.date.today(), reimbursementPoint=venue, invoices=[invoice]
        )
        finance_factories.PricingFactory(
            booking__stock__offer__venue=venue, status=finance_models.PricingStatus.INVOICED, cashflows=[cashflow]
        )
    pro = users_factories.ProFactory()
    offerers_factories.UserOffererFactory(user=pro, offerer=offerer)

    # When
    with assert_num_queries(14):
        response = client.with_session_auth(pro.email).get(
            f"/reimbursements/csv?reimbursementPeriodBeginningDate={beginning_date_iso_format}&reimbursementPeriodEndingDate={ending_date_iso_format}&venueId={venue1.id}"
        )
        assert response.status_code == 200

    # Then
    assert response.headers["Content-type"] == "text/csv; charset=utf-8;"
    assert response.headers["Content-Disposition"] == "attachment; filename=remboursements_pass_culture.csv"
    reader = csv.DictReader(StringIO(response.data.decode("utf-8-sig")), delimiter=";")
    assert reader.fieldnames == ReimbursementDetails.LEGACY_JOURNEY_CSV_HEADER
    rows = list(reader)
    assert len(rows) == 1
    row = rows[0]

    fortnight = "2nde" if datetime.date.today().day > 15 else "1ère"
    invoice = finance_models.Invoice.query.filter(finance_models.Invoice.reimbursementPointId == venue1.id).one()
    batch = finance_models.CashflowBatch.query.one()
    offer = offers_models.Offer.query.filter(offers_models.Offer.venueId == venue1.id).one()
    booking = bookings_models.Booking.query.filter(bookings_models.Booking.venueId == venue1.id).one()
    pricing = finance_models.Pricing.query.filter(finance_models.Pricing.bookingId == booking.id).one()

    assert f"{fortnight} quinzaine" in row["Réservations concernées par le remboursement"]
    assert row["Date du justificatif"] == invoice.date.strftime("%Y-%m-%d")
    assert row["N° du justificatif"] == invoice.reference
    assert row["N° de virement"] == batch.label
    assert row["Point de remboursement"] == venue1.common_name
    assert row["Adresse du point de remboursement"] == f"{venue1.address} {venue1.postalCode} {venue1.city}"
    assert row["SIRET du point de remboursement"] == venue1.siret
    assert row["IBAN"] == venue1.bankInformation.iban
    assert row["Raison sociale du lieu"] == venue1.name
    assert row["Adresse du lieu"] == f"{venue1.address} {venue1.postalCode} {venue1.city}"
    assert row["SIRET du lieu"] == venue1.siret
    assert row["Nom de l'offre"] == offer.name
    assert row["N° de réservation (offre collective)"] == ""
    assert row["Nom (offre collective)"] == ""
    assert row["Prénom (offre collective)"] == ""
    assert row["Nom de l'établissement (offre collective)"] == ""
    assert row["Date de l'évènement (offre collective)"] == ""
    assert row["Contremarque"] == booking.token
    assert row["Date de validation de la réservation"] == booking.dateUsed.strftime("%Y-%m-%d %H:%M:%S")
    assert row["Intitulé du tarif"] == ""
    assert row["Montant de la réservation"] == str(booking.amount).replace(".", ",")
    assert row["Barème"].replace("\xa0", " ") == "100 %"
    assert row["Montant remboursé"] == "{:.2f}".format(-pricing.amount / 100).replace(".", ",")


@pytest.mark.usefixtures("db_session")
@override_features(WIP_ENABLE_NEW_BANK_DETAILS_JOURNEY=False)
def test_with_reimbursement_period_filter_old_bank_information_journey_with_pricings(client):
    beginning_date_iso_format = (datetime.date.today() - datetime.timedelta(days=2)).isoformat()
    ending_date_iso_format = (datetime.date.today() + datetime.timedelta(days=2)).isoformat()
    offerer = offerers_factories.OffererFactory()
    venue = offerers_factories.VenueFactory(managingOfferer=offerer, pricing_point="self")
    finance_factories.BankInformationFactory(venue=venue)
    batch = finance_factories.CashflowBatchFactory()
    pro = users_factories.ProFactory()
    offerers_factories.UserOffererFactory(user=pro, offerer=offerer)

    # Within the reimbursement period filter
    invoice_1 = finance_factories.InvoiceFactory(reimbursementPoint=venue, date=datetime.date.today())
    cashflow_1 = finance_factories.CashflowFactory(
        batch=batch, creationDate=datetime.date.today(), reimbursementPoint=venue, invoices=[invoice_1]
    )
    finance_factories.PricingFactory(
        booking__stock__offer__venue=venue,
        booking__dateUsed=datetime.date.today() - datetime.timedelta(days=1),
        status=finance_models.PricingStatus.INVOICED,
        cashflows=[cashflow_1],
    )
    finance_factories.PricingFactory(
        booking__stock__offer__venue=venue,
        booking__dateUsed=datetime.date.today() - datetime.timedelta(days=1),
        status=finance_models.PricingStatus.INVOICED,
        cashflows=[cashflow_1],
    )

    # Outside the reimbursement period filter
    invoice_2 = finance_factories.InvoiceFactory(
        reimbursementPoint=venue, date=datetime.date.today() - datetime.timedelta(days=5)
    )
    cashflow_2 = finance_factories.CashflowFactory(
        batch=batch,
        creationDate=datetime.date.today() - datetime.timedelta(days=5),
        reimbursementPoint=venue,
        invoices=[invoice_2],
    )
    finance_factories.PricingFactory(
        booking__stock__offer__venue=venue,
        booking__dateUsed=datetime.date.today() - datetime.timedelta(days=4),
        status=finance_models.PricingStatus.INVOICED,
        cashflows=[cashflow_2],
    )
    finance_factories.PricingFactory(
        booking__stock__offer__venue=venue,
        booking__dateUsed=datetime.date.today() - datetime.timedelta(days=4),
        status=finance_models.PricingStatus.INVOICED,
        cashflows=[cashflow_2],
    )

    # When
    with assert_num_queries(14):
        response = client.with_session_auth(pro.email).get(
            f"/reimbursements/csv?reimbursementPeriodBeginningDate={beginning_date_iso_format}&reimbursementPeriodEndingDate={ending_date_iso_format}&venueId={venue.id}"
        )
        assert response.status_code == 200
    # Then
    assert response.headers["Content-type"] == "text/csv; charset=utf-8;"
    assert response.headers["Content-Disposition"] == "attachment; filename=remboursements_pass_culture.csv"
    reader = csv.DictReader(StringIO(response.data.decode("utf-8-sig")), delimiter=";")
    assert reader.fieldnames == ReimbursementDetails.LEGACY_JOURNEY_CSV_HEADER
    rows = list(reader)
    assert len(rows) == 2

    bookings = (
        bookings_models.Booking.query.filter(bookings_models.Booking.venueId == venue.id)
        .order_by(bookings_models.Booking.dateUsed.desc(), bookings_models.Booking.id.desc())
        .all()
    )

    for row, booking in zip(rows, bookings):
        fortnight = "2nde" if datetime.date.today().day > 15 else "1ère"
        pricing = finance_models.Pricing.query.filter(finance_models.Pricing.bookingId == booking.id).one()
        cashflow = pricing.cashflows[0]
        invoice = cashflow.invoices[0]
        offer = booking.stock.offer
        batch = finance_models.CashflowBatch.query.one()

        assert f"{fortnight} quinzaine" in row["Réservations concernées par le remboursement"]
        assert row["Date du justificatif"] == invoice.date.strftime("%Y-%m-%d")
        assert row["N° du justificatif"] == invoice.reference
        assert row["N° de virement"] == batch.label
        assert row["Point de remboursement"] == venue.common_name
        assert row["Adresse du point de remboursement"] == f"{venue.address} {venue.postalCode} {venue.city}"
        assert row["SIRET du point de remboursement"] == venue.siret
        assert row["IBAN"] == venue.bankInformation.iban
        assert row["Raison sociale du lieu"] == venue.name
        assert row["Adresse du lieu"] == f"{venue.address} {venue.postalCode} {venue.city}"
        assert row["SIRET du lieu"] == venue.siret
        assert row["Nom de l'offre"] == offer.name
        assert row["N° de réservation (offre collective)"] == ""
        assert row["Nom (offre collective)"] == ""
        assert row["Prénom (offre collective)"] == ""
        assert row["Nom de l'établissement (offre collective)"] == ""
        assert row["Date de l'évènement (offre collective)"] == ""
        assert row["Contremarque"] == booking.token
        assert row["Date de validation de la réservation"] == booking.dateUsed.strftime("%Y-%m-%d %H:%M:%S")
        assert row["Intitulé du tarif"] == ""
        assert row["Montant de la réservation"] == str(booking.amount).replace(".", ",")
        assert row["Barème"].replace("\xa0", " ") == "100 %"
        assert row["Montant remboursé"] == "{:.2f}".format(-pricing.amount / 100).replace(".", ",")


@pytest.mark.usefixtures("db_session")
def test_with_venue_filter_old_bank_information_journey_with_pricings_and_collective_use_case(client):
    beginning_date_iso_format = (datetime.date.today() - datetime.timedelta(days=2)).isoformat()
    ending_date_iso_format = (datetime.date.today() + datetime.timedelta(days=2)).isoformat()
    offerer = offerers_factories.OffererFactory()
    venue1 = offerers_factories.VenueFactory(managingOfferer=offerer, pricing_point="self")
    finance_factories.BankInformationFactory(venue=venue1)
    venue2 = offerers_factories.VenueFactory(managingOfferer=offerer, pricing_point=venue1)
    finance_factories.BankInformationFactory(venue=venue2)
    batch = finance_factories.CashflowBatchFactory()

    for venue in (venue1, venue2):
        invoice = finance_factories.InvoiceFactory(reimbursementPoint=venue, date=datetime.date.today())
        cashflow = finance_factories.CashflowFactory(
            batch=batch, creationDate=datetime.date.today(), reimbursementPoint=venue, invoices=[invoice]
        )
        finance_factories.CollectivePricingFactory(
            collectiveBooking__collectiveStock__collectiveOffer__venue=venue,
            status=finance_models.PricingStatus.INVOICED,
            cashflows=[cashflow],
        )
    pro = users_factories.ProFactory()
    offerers_factories.UserOffererFactory(user=pro, offerer=offerer)

    # When
    with assert_num_queries(14):
        response = client.with_session_auth(pro.email).get(
            f"/reimbursements/csv?reimbursementPeriodBeginningDate={beginning_date_iso_format}&reimbursementPeriodEndingDate={ending_date_iso_format}&venueId={venue1.id}"
        )
        assert response.status_code == 200

    # Then
    assert response.headers["Content-type"] == "text/csv; charset=utf-8;"
    assert response.headers["Content-Disposition"] == "attachment; filename=remboursements_pass_culture.csv"
    reader = csv.DictReader(StringIO(response.data.decode("utf-8-sig")), delimiter=";")
    assert reader.fieldnames == ReimbursementDetails.LEGACY_JOURNEY_CSV_HEADER
    rows = list(reader)
    assert len(rows) == 1
    row = rows[0]

    fortnight = "2nde" if datetime.date.today().day > 15 else "1ère"
    invoice = finance_models.Invoice.query.filter(finance_models.Invoice.reimbursementPointId == venue1.id).one()
    batch = finance_models.CashflowBatch.query.one()
    collective_offer = educational_models.CollectiveOffer.query.filter(
        educational_models.CollectiveOffer.venueId == venue1.id
    ).one()
    collective_booking = educational_models.CollectiveBooking.query.filter(
        educational_models.CollectiveBooking.venueId == venue1.id
    ).one()
    redactor = educational_models.EducationalRedactor.query.filter(
        educational_models.EducationalRedactor.id == collective_booking.educationalRedactorId
    ).one()
    institution = educational_models.EducationalInstitution.query.filter(
        educational_models.EducationalInstitution.id == collective_booking.educationalInstitutionId
    ).one()
    pricing = finance_models.Pricing.query.filter(
        finance_models.Pricing.collectiveBookingId == collective_booking.id
    ).one()

    assert f"{fortnight} quinzaine" in row["Réservations concernées par le remboursement"]
    assert row["Date du justificatif"] == invoice.date.strftime("%Y-%m-%d")
    assert row["N° du justificatif"] == invoice.reference
    assert row["N° de virement"] == batch.label
    assert row["Point de remboursement"] == venue1.common_name
    assert row["Adresse du point de remboursement"] == f"{venue1.address} {venue1.postalCode} {venue1.city}"
    assert row["SIRET du point de remboursement"] == venue1.siret
    assert row["IBAN"] == venue1.bankInformation.iban
    assert row["Raison sociale du lieu"] == venue1.name
    assert row["Adresse du lieu"] == f"{venue1.address} {venue1.postalCode} {venue1.city}"
    assert row["SIRET du lieu"] == venue1.siret
    assert row["Nom de l'offre"] == collective_offer.name
    assert row["N° de réservation (offre collective)"] == str(collective_booking.id)
    assert row["Nom (offre collective)"] == redactor.lastName
    assert row["Prénom (offre collective)"] == redactor.firstName
    assert row["Nom de l'établissement (offre collective)"] == institution.name
    assert row["Date de l'évènement (offre collective)"] == utc_datetime_to_department_timezone(
        collective_booking.collectiveStock.beginningDatetime, venue1.departementCode
    ).strftime("%d/%m/%Y %H:%M")
    assert row["Contremarque"] == ""
    assert row["Date de validation de la réservation"] == collective_booking.dateUsed.strftime("%Y-%m-%d %H:%M:%S")
    assert row["Intitulé du tarif"] == ""
    assert row["Montant de la réservation"] == str(collective_booking.collectiveStock.price).replace(".", ",")
    assert row["Barème"].replace("\xa0", " ") == "100 %"
    assert row["Montant remboursé"] == "{:.2f}".format(-pricing.amount / 100).replace(".", ",")


@pytest.mark.usefixtures("db_session")
def test_with_reimbursement_period_filter_old_bank_information_journey_with_pricings_collective_use_case(client):
    beginning_date_iso_format = (datetime.date.today() - datetime.timedelta(days=2)).isoformat()
    ending_date_iso_format = (datetime.date.today() + datetime.timedelta(days=2)).isoformat()
    offerer = offerers_factories.OffererFactory()
    venue = offerers_factories.VenueFactory(managingOfferer=offerer, pricing_point="self")
    finance_factories.BankInformationFactory(venue=venue)
    batch = finance_factories.CashflowBatchFactory()
    pro = users_factories.ProFactory()
    offerers_factories.UserOffererFactory(user=pro, offerer=offerer)

    # Within the reimbursement period filter
    invoice_1 = finance_factories.InvoiceFactory(reimbursementPoint=venue, date=datetime.date.today())
    cashflow_1 = finance_factories.CashflowFactory(
        batch=batch, creationDate=datetime.date.today(), reimbursementPoint=venue, invoices=[invoice_1]
    )
    finance_factories.CollectivePricingFactory(
        collectiveBooking__collectiveStock__collectiveOffer__venue=venue,
        collectiveBooking__dateUsed=datetime.date.today() - datetime.timedelta(days=1),
        status=finance_models.PricingStatus.INVOICED,
        cashflows=[cashflow_1],
    )
    finance_factories.CollectivePricingFactory(
        collectiveBooking__collectiveStock__collectiveOffer__venue=venue,
        collectiveBooking__dateUsed=datetime.date.today() - datetime.timedelta(days=1),
        status=finance_models.PricingStatus.INVOICED,
        cashflows=[cashflow_1],
    )

    # Outside the reimbursement period filter
    invoice_2 = finance_factories.InvoiceFactory(
        reimbursementPoint=venue, date=datetime.date.today() - datetime.timedelta(days=5)
    )
    cashflow_2 = finance_factories.CashflowFactory(
        batch=batch,
        creationDate=datetime.date.today() - datetime.timedelta(days=5),
        reimbursementPoint=venue,
        invoices=[invoice_2],
    )
    finance_factories.CollectivePricingFactory(
        collectiveBooking__collectiveStock__collectiveOffer__venue=venue,
        collectiveBooking__dateUsed=datetime.date.today() - datetime.timedelta(days=4),
        status=finance_models.PricingStatus.INVOICED,
        cashflows=[cashflow_2],
    )
    finance_factories.CollectivePricingFactory(
        collectiveBooking__collectiveStock__collectiveOffer__venue=venue,
        collectiveBooking__dateUsed=datetime.date.today() - datetime.timedelta(days=4),
        status=finance_models.PricingStatus.INVOICED,
        cashflows=[cashflow_2],
    )

    # When
    with assert_num_queries(14):
        response = client.with_session_auth(pro.email).get(
            f"/reimbursements/csv?reimbursementPeriodBeginningDate={beginning_date_iso_format}&reimbursementPeriodEndingDate={ending_date_iso_format}&venueId={venue.id}"
        )
        assert response.status_code == 200

    # Then
    assert response.headers["Content-type"] == "text/csv; charset=utf-8;"
    assert response.headers["Content-Disposition"] == "attachment; filename=remboursements_pass_culture.csv"
    reader = csv.DictReader(StringIO(response.data.decode("utf-8-sig")), delimiter=";")
    assert reader.fieldnames == ReimbursementDetails.LEGACY_JOURNEY_CSV_HEADER
    rows = list(reader)
    assert len(rows) == 2

    collective_bookings = (
        educational_models.CollectiveBooking.query.filter(educational_models.CollectiveBooking.venueId == venue.id)
        .order_by(educational_models.CollectiveBooking.dateUsed.desc(), educational_models.CollectiveBooking.id.desc())
        .all()
    )

    for row, collective_booking in zip(rows, collective_bookings):
        fortnight = "2nde" if datetime.date.today().day > 15 else "1ère"
        pricing = finance_models.Pricing.query.filter(
            finance_models.Pricing.collectiveBookingId == collective_booking.id
        ).one()
        cashflow = pricing.cashflows[0]
        invoice = cashflow.invoices[0]
        collective_offer = collective_booking.collectiveStock.collectiveOffer
        redactor = collective_booking.educationalRedactor
        institution = collective_booking.educationalInstitution
        batch = finance_models.CashflowBatch.query.one()

        assert f"{fortnight} quinzaine" in row["Réservations concernées par le remboursement"]
        assert row["Date du justificatif"] == invoice.date.strftime("%Y-%m-%d")
        assert row["N° du justificatif"] == invoice.reference
        assert row["N° de virement"] == batch.label
        assert row["Adresse du point de remboursement"] == f"{venue.address} {venue.postalCode} {venue.city}"
        assert row["SIRET du point de remboursement"] == venue.siret
        assert row["IBAN"] == venue.bankInformation.iban
        assert row["Raison sociale du lieu"] == venue.name
        assert row["Adresse du lieu"] == f"{venue.address} {venue.postalCode} {venue.city}"
        assert row["SIRET du lieu"] == venue.siret
        assert row["Nom de l'offre"] == collective_offer.name
        assert row["N° de réservation (offre collective)"] == str(collective_booking.id)
        assert row["Nom (offre collective)"] == redactor.lastName
        assert row["Prénom (offre collective)"] == redactor.firstName
        assert row["Nom de l'établissement (offre collective)"] == institution.name
        assert row["Date de l'évènement (offre collective)"] == utc_datetime_to_department_timezone(
            collective_booking.collectiveStock.beginningDatetime, venue.departementCode
        ).strftime("%d/%m/%Y %H:%M")
        assert row["Contremarque"] == ""
        assert row["Date de validation de la réservation"] == collective_booking.dateUsed.strftime("%Y-%m-%d %H:%M:%S")
        assert row["Intitulé du tarif"] == ""
        assert row["Montant de la réservation"] == str(collective_booking.collectiveStock.price).replace(".", ",")
        assert row["Barème"].replace("\xa0", " ") == "100 %"
        assert row["Montant remboursé"] == "{:.2f}".format(-pricing.amount / 100).replace(".", ",")


### New bankAccount journey (with pricings) ###


@pytest.mark.usefixtures("db_session")
@override_features(WIP_ENABLE_NEW_BANK_DETAILS_JOURNEY=True)
def test_with_venue_filter_new_bank_account_journey_with_pricings(client):
    beginning_date_iso_format = (datetime.date.today() - datetime.timedelta(days=2)).isoformat()
    ending_date_iso_format = (datetime.date.today() + datetime.timedelta(days=2)).isoformat()
    offerer = offerers_factories.OffererFactory()
    venue1 = offerers_factories.VenueFactory(managingOfferer=offerer, pricing_point="self")
    bank_account_1 = finance_factories.BankAccountFactory(offerer=offerer)
    offerers_factories.VenueBankAccountLinkFactory(
        venue=venue1, bankAccount=bank_account_1, timespan=(datetime.datetime.utcnow(),)
    )

    venue2 = offerers_factories.VenueFactory(managingOfferer=offerer, pricing_point=venue1)
    bank_account_2 = finance_factories.BankAccountFactory(offerer=offerer)
    offerers_factories.VenueBankAccountLinkFactory(
        venue=venue2, bankAccount=bank_account_2, timespan=(datetime.datetime.utcnow(),)
    )

    batch = finance_factories.CashflowBatchFactory()

    for bank_account, venue in zip((bank_account_1, bank_account_2), (venue1, venue2)):
        invoice = finance_factories.InvoiceFactory(bankAccount=bank_account, date=datetime.date.today())
        cashflow = finance_factories.CashflowFactory(
            batch=batch, creationDate=datetime.date.today(), bankAccount=bank_account, invoices=[invoice]
        )
        finance_factories.PricingFactory(
            booking__stock__offer__venue=venue, status=finance_models.PricingStatus.INVOICED, cashflows=[cashflow]
        )
    pro = users_factories.ProFactory()
    offerers_factories.UserOffererFactory(user=pro, offerer=offerer)

    # When
    with assert_num_queries(14):
        response = client.with_session_auth(pro.email).get(
            f"/reimbursements/csv?reimbursementPeriodBeginningDate={beginning_date_iso_format}&reimbursementPeriodEndingDate={ending_date_iso_format}&venueId={venue1.id}"
        )
        assert response.status_code == 200

    # Then
    assert response.headers["Content-type"] == "text/csv; charset=utf-8;"
    assert response.headers["Content-Disposition"] == "attachment; filename=remboursements_pass_culture.csv"
    reader = csv.DictReader(StringIO(response.data.decode("utf-8-sig")), delimiter=";")
    assert reader.fieldnames == ReimbursementDetails.NEW_JOURNEY_CSV_HEADER
    rows = list(reader)
    assert len(rows) == 1
    row = rows[0]

    fortnight = "2nde" if datetime.date.today().day > 15 else "1ère"
    invoice = finance_models.Invoice.query.filter(finance_models.Invoice.bankAccountId == bank_account_1.id).one()
    batch = finance_models.CashflowBatch.query.one()
    offer = offers_models.Offer.query.filter(offers_models.Offer.venueId == venue1.id).one()
    booking = bookings_models.Booking.query.filter(bookings_models.Booking.venueId == venue1.id).one()
    pricing = finance_models.Pricing.query.filter(finance_models.Pricing.bookingId == booking.id).one()

    assert f"{fortnight} quinzaine" in row["Réservations concernées par le remboursement"]
    assert row["Date du justificatif"] == invoice.date.strftime("%Y-%m-%d")
    assert row["N° du justificatif"] == invoice.reference
    assert row["N° de virement"] == batch.label
    assert row["Intitulé du compte bancaire"] == bank_account_1.label
    assert row["SIRET du lieu"] == venue1.siret
    assert row["IBAN"] == bank_account_1.iban
    assert row["Raison sociale du lieu"] == venue1.name
    assert row["Adresse du lieu"] == f"{venue1.address} {venue1.postalCode} {venue1.city}"
    assert row["SIRET du lieu"] == venue1.siret
    assert row["Nom de l'offre"] == offer.name
    assert row["N° de réservation (offre collective)"] == ""
    assert row["Nom (offre collective)"] == ""
    assert row["Prénom (offre collective)"] == ""
    assert row["Nom de l'établissement (offre collective)"] == ""
    assert row["Date de l'évènement (offre collective)"] == ""
    assert row["Contremarque"] == booking.token
    assert row["Date de validation de la réservation"] == booking.dateUsed.strftime("%Y-%m-%d %H:%M:%S")
    assert row["Intitulé du tarif"] == ""
    assert row["Montant de la réservation"] == str(booking.amount).replace(".", ",")
    assert row["Barème"].replace("\xa0", " ") == "100 %"
    assert row["Montant remboursé"] == "{:.2f}".format(-pricing.amount / 100).replace(".", ",")


@pytest.mark.usefixtures("db_session")
@override_features(WIP_ENABLE_NEW_BANK_DETAILS_JOURNEY=True)
def test_with_reimbursement_period_filter_new_bank_account_journey_with_pricings(client):
    beginning_date_iso_format = (datetime.date.today() - datetime.timedelta(days=2)).isoformat()
    ending_date_iso_format = (datetime.date.today() + datetime.timedelta(days=2)).isoformat()
    offerer = offerers_factories.OffererFactory()
    venue = offerers_factories.VenueFactory(managingOfferer=offerer, pricing_point="self")
    bank_account = finance_factories.BankAccountFactory(offerer=offerer)
    offerers_factories.VenueBankAccountLinkFactory(venue=venue, bankAccount=bank_account)
    batch = finance_factories.CashflowBatchFactory()
    pro = users_factories.ProFactory()
    offerers_factories.UserOffererFactory(user=pro, offerer=offerer)

    # Within the reimbursement period filter
    invoice_1 = finance_factories.InvoiceFactory(bankAccount=bank_account, date=datetime.date.today())
    cashflow_1 = finance_factories.CashflowFactory(
        batch=batch, creationDate=datetime.date.today(), bankAccount=bank_account, invoices=[invoice_1]
    )
    finance_factories.PricingFactory(
        booking__stock__offer__venue=venue,
        booking__dateUsed=datetime.date.today() - datetime.timedelta(days=1),
        status=finance_models.PricingStatus.INVOICED,
        cashflows=[cashflow_1],
    )
    finance_factories.PricingFactory(
        booking__stock__offer__venue=venue,
        booking__dateUsed=datetime.date.today() - datetime.timedelta(days=1),
        status=finance_models.PricingStatus.INVOICED,
        cashflows=[cashflow_1],
    )

    # Outside the reimbursement period filter
    invoice_2 = finance_factories.InvoiceFactory(
        bankAccount=bank_account, date=datetime.date.today() - datetime.timedelta(days=5)
    )
    cashflow_2 = finance_factories.CashflowFactory(
        batch=batch,
        creationDate=datetime.date.today() - datetime.timedelta(days=5),
        bankAccount=bank_account,
        invoices=[invoice_2],
    )
    finance_factories.PricingFactory(
        booking__stock__offer__venue=venue,
        booking__dateUsed=datetime.date.today() - datetime.timedelta(days=4),
        status=finance_models.PricingStatus.INVOICED,
        cashflows=[cashflow_2],
    )
    finance_factories.PricingFactory(
        booking__stock__offer__venue=venue,
        booking__dateUsed=datetime.date.today() - datetime.timedelta(days=4),
        status=finance_models.PricingStatus.INVOICED,
        cashflows=[cashflow_2],
    )

    # When
    with assert_num_queries(14):
        response = client.with_session_auth(pro.email).get(
            f"/reimbursements/csv?reimbursementPeriodBeginningDate={beginning_date_iso_format}&reimbursementPeriodEndingDate={ending_date_iso_format}&venueId={venue.id}"
        )
        assert response.status_code == 200

    # Then
    assert response.headers["Content-type"] == "text/csv; charset=utf-8;"
    assert response.headers["Content-Disposition"] == "attachment; filename=remboursements_pass_culture.csv"
    reader = csv.DictReader(StringIO(response.data.decode("utf-8-sig")), delimiter=";")
    assert reader.fieldnames == ReimbursementDetails.NEW_JOURNEY_CSV_HEADER
    rows = list(reader)
    assert len(rows) == 2

    bookings = (
        bookings_models.Booking.query.filter(bookings_models.Booking.venueId == venue.id)
        .order_by(bookings_models.Booking.dateUsed.desc(), bookings_models.Booking.id.desc())
        .all()
    )

    for row, booking in zip(rows, bookings):
        fortnight = "2nde" if datetime.date.today().day > 15 else "1ère"
        pricing = finance_models.Pricing.query.filter(finance_models.Pricing.bookingId == booking.id).one()
        cashflow = pricing.cashflows[0]
        invoice = cashflow.invoices[0]
        offer = booking.stock.offer
        batch = finance_models.CashflowBatch.query.one()

        assert f"{fortnight} quinzaine" in row["Réservations concernées par le remboursement"]
        assert row["Date du justificatif"] == invoice.date.strftime("%Y-%m-%d")
        assert row["N° du justificatif"] == invoice.reference
        assert row["N° de virement"] == batch.label
        assert row["Intitulé du compte bancaire"] == bank_account.label
        assert row["SIRET du lieu"] == venue.siret
        assert row["IBAN"] == bank_account.iban
        assert row["Raison sociale du lieu"] == venue.name
        assert row["Adresse du lieu"] == f"{venue.address} {venue.postalCode} {venue.city}"
        assert row["SIRET du lieu"] == venue.siret
        assert row["Nom de l'offre"] == offer.name
        assert row["N° de réservation (offre collective)"] == ""
        assert row["Nom (offre collective)"] == ""
        assert row["Prénom (offre collective)"] == ""
        assert row["Nom de l'établissement (offre collective)"] == ""
        assert row["Date de l'évènement (offre collective)"] == ""
        assert row["Contremarque"] == booking.token
        assert row["Date de validation de la réservation"] == booking.dateUsed.strftime("%Y-%m-%d %H:%M:%S")
        assert row["Intitulé du tarif"] == ""
        assert row["Montant de la réservation"] == str(booking.amount).replace(".", ",")
        assert row["Barème"].replace("\xa0", " ") == "100 %"
        assert row["Montant remboursé"] == "{:.2f}".format(-pricing.amount / 100).replace(".", ",")


@pytest.mark.usefixtures("db_session")
@override_features(WIP_ENABLE_NEW_BANK_DETAILS_JOURNEY=True)
def test_with_venue_filter_new_bank_account_journey_with_pricings_collective_use_case(client):
    beginning_date_iso_format = (datetime.date.today() - datetime.timedelta(days=2)).isoformat()
    ending_date_iso_format = (datetime.date.today() + datetime.timedelta(days=2)).isoformat()
    offerer = offerers_factories.OffererFactory()
    venue1 = offerers_factories.VenueFactory(managingOfferer=offerer, pricing_point="self")
    bank_account_1 = finance_factories.BankAccountFactory(offerer=offerer)
    offerers_factories.VenueBankAccountLinkFactory(
        venue=venue1, bankAccount=bank_account_1, timespan=(datetime.datetime.utcnow(),)
    )

    venue2 = offerers_factories.VenueFactory(managingOfferer=offerer, pricing_point=venue1)
    bank_account_2 = finance_factories.BankAccountFactory(offerer=offerer)
    offerers_factories.VenueBankAccountLinkFactory(
        venue=venue2, bankAccount=bank_account_2, timespan=(datetime.datetime.utcnow(),)
    )

    batch = finance_factories.CashflowBatchFactory()

    for bank_account, venue in zip((bank_account_1, bank_account_2), (venue1, venue2)):
        invoice = finance_factories.InvoiceFactory(bankAccount=bank_account, date=datetime.date.today())
        cashflow = finance_factories.CashflowFactory(
            batch=batch, creationDate=datetime.date.today(), bankAccount=bank_account, invoices=[invoice]
        )
        finance_factories.CollectivePricingFactory(
            collectiveBooking__collectiveStock__collectiveOffer__venue=venue,
            status=finance_models.PricingStatus.INVOICED,
            cashflows=[cashflow],
        )
    pro = users_factories.ProFactory()
    offerers_factories.UserOffererFactory(user=pro, offerer=offerer)

    # When
    with assert_num_queries(14):
        response = client.with_session_auth(pro.email).get(
            f"/reimbursements/csv?reimbursementPeriodBeginningDate={beginning_date_iso_format}&reimbursementPeriodEndingDate={ending_date_iso_format}&venueId={venue1.id}"
        )
        assert response.status_code == 200

    # Then
    assert response.headers["Content-type"] == "text/csv; charset=utf-8;"
    assert response.headers["Content-Disposition"] == "attachment; filename=remboursements_pass_culture.csv"
    reader = csv.DictReader(StringIO(response.data.decode("utf-8-sig")), delimiter=";")
    assert reader.fieldnames == ReimbursementDetails.NEW_JOURNEY_CSV_HEADER
    rows = list(reader)
    assert len(rows) == 1
    row = rows[0]

    fortnight = "2nde" if datetime.date.today().day > 15 else "1ère"
    invoice = finance_models.Invoice.query.filter(finance_models.Invoice.bankAccountId == bank_account_1.id).one()
    batch = finance_models.CashflowBatch.query.one()
    collective_offer = educational_models.CollectiveOffer.query.filter(
        educational_models.CollectiveOffer.venueId == venue1.id
    ).one()
    collective_booking = educational_models.CollectiveBooking.query.filter(
        educational_models.CollectiveBooking.venueId == venue1.id
    ).one()
    pricing = finance_models.Pricing.query.filter(
        finance_models.Pricing.collectiveBookingId == collective_booking.id
    ).one()
    redactor = collective_booking.educationalRedactor
    institution = collective_booking.educationalInstitution

    assert f"{fortnight} quinzaine" in row["Réservations concernées par le remboursement"]
    assert row["Date du justificatif"] == invoice.date.strftime("%Y-%m-%d")
    assert row["N° du justificatif"] == invoice.reference
    assert row["N° de virement"] == batch.label
    assert row["Intitulé du compte bancaire"] == bank_account_1.label
    assert row["SIRET du lieu"] == venue1.siret
    assert row["IBAN"] == bank_account_1.iban
    assert row["Raison sociale du lieu"] == venue1.name
    assert row["Adresse du lieu"] == f"{venue1.address} {venue1.postalCode} {venue1.city}"
    assert row["SIRET du lieu"] == venue1.siret
    assert row["Nom de l'offre"] == collective_offer.name
    assert row["N° de réservation (offre collective)"] == str(collective_booking.id)
    assert row["Nom (offre collective)"] == redactor.lastName
    assert row["Prénom (offre collective)"] == redactor.firstName
    assert row["Nom de l'établissement (offre collective)"] == institution.name
    assert row["Date de l'évènement (offre collective)"] == utc_datetime_to_department_timezone(
        collective_booking.collectiveStock.beginningDatetime, venue1.departementCode
    ).strftime("%d/%m/%Y %H:%M")
    assert row["Contremarque"] == ""
    assert row["Date de validation de la réservation"] == collective_booking.dateUsed.strftime("%Y-%m-%d %H:%M:%S")
    assert row["Intitulé du tarif"] == ""
    assert row["Montant de la réservation"] == str(collective_booking.collectiveStock.price).replace(".", ",")
    assert row["Barème"].replace("\xa0", " ") == "100 %"
    assert row["Montant remboursé"] == "{:.2f}".format(-pricing.amount / 100).replace(".", ",")


@pytest.mark.usefixtures("db_session")
@override_features(WIP_ENABLE_NEW_BANK_DETAILS_JOURNEY=True)
def test_with_reimbursement_period_filter_new_bank_account_journey_with_pricings_collective_use_case(client):
    beginning_date_iso_format = (datetime.date.today() - datetime.timedelta(days=2)).isoformat()
    ending_date_iso_format = (datetime.date.today() + datetime.timedelta(days=2)).isoformat()
    offerer = offerers_factories.OffererFactory()
    venue = offerers_factories.VenueFactory(managingOfferer=offerer, pricing_point="self")
    bank_account = finance_factories.BankAccountFactory(offerer=offerer)
    offerers_factories.VenueBankAccountLinkFactory(venue=venue, bankAccount=bank_account)
    batch = finance_factories.CashflowBatchFactory()
    pro = users_factories.ProFactory()
    offerers_factories.UserOffererFactory(user=pro, offerer=offerer)

    # Within the reimbursement period filter
    invoice_1 = finance_factories.InvoiceFactory(bankAccount=bank_account, date=datetime.date.today())
    cashflow_1 = finance_factories.CashflowFactory(
        batch=batch, creationDate=datetime.date.today(), bankAccount=bank_account, invoices=[invoice_1]
    )
    finance_factories.CollectivePricingFactory(
        collectiveBooking__collectiveStock__collectiveOffer__venue=venue,
        collectiveBooking__dateUsed=datetime.date.today() - datetime.timedelta(days=1),
        status=finance_models.PricingStatus.INVOICED,
        cashflows=[cashflow_1],
    )
    finance_factories.CollectivePricingFactory(
        collectiveBooking__collectiveStock__collectiveOffer__venue=venue,
        collectiveBooking__dateUsed=datetime.date.today() - datetime.timedelta(days=1),
        status=finance_models.PricingStatus.INVOICED,
        cashflows=[cashflow_1],
    )

    # Outside the reimbursement period filter
    invoice_2 = finance_factories.InvoiceFactory(
        bankAccount=bank_account, date=datetime.date.today() - datetime.timedelta(days=5)
    )
    cashflow_2 = finance_factories.CashflowFactory(
        batch=batch,
        creationDate=datetime.date.today() - datetime.timedelta(days=5),
        bankAccount=bank_account,
        invoices=[invoice_2],
    )
    finance_factories.CollectivePricingFactory(
        collectiveBooking__collectiveStock__collectiveOffer__venue=venue,
        collectiveBooking__dateUsed=datetime.date.today() - datetime.timedelta(days=4),
        status=finance_models.PricingStatus.INVOICED,
        cashflows=[cashflow_2],
    )
    finance_factories.CollectivePricingFactory(
        collectiveBooking__collectiveStock__collectiveOffer__venue=venue,
        collectiveBooking__dateUsed=datetime.date.today() - datetime.timedelta(days=4),
        status=finance_models.PricingStatus.INVOICED,
        cashflows=[cashflow_2],
    )

    # When
    with assert_num_queries(14):
        response = client.with_session_auth(pro.email).get(
            f"/reimbursements/csv?reimbursementPeriodBeginningDate={beginning_date_iso_format}&reimbursementPeriodEndingDate={ending_date_iso_format}&venueId={venue.id}"
        )
        assert response.status_code == 200

    # Then
    assert response.headers["Content-type"] == "text/csv; charset=utf-8;"
    assert response.headers["Content-Disposition"] == "attachment; filename=remboursements_pass_culture.csv"
    reader = csv.DictReader(StringIO(response.data.decode("utf-8-sig")), delimiter=";")
    assert reader.fieldnames == ReimbursementDetails.NEW_JOURNEY_CSV_HEADER
    rows = list(reader)
    assert len(rows) == 2

    collective_bookings = (
        educational_models.CollectiveBooking.query.filter(educational_models.CollectiveBooking.venueId == venue.id)
        .order_by(educational_models.CollectiveBooking.dateUsed.desc(), educational_models.CollectiveBooking.id.desc())
        .all()
    )

    for row, collective_booking in zip(rows, collective_bookings):
        fortnight = "2nde" if datetime.date.today().day > 15 else "1ère"
        pricing = finance_models.Pricing.query.filter(
            finance_models.Pricing.collectiveBookingId == collective_booking.id
        ).one()
        cashflow = pricing.cashflows[0]
        invoice = cashflow.invoices[0]
        collective_offer = collective_booking.collectiveStock.collectiveOffer
        redactor = collective_booking.educationalRedactor
        institution = collective_booking.educationalInstitution
        batch = finance_models.CashflowBatch.query.one()

        assert f"{fortnight} quinzaine" in row["Réservations concernées par le remboursement"]
        assert row["Date du justificatif"] == invoice.date.strftime("%Y-%m-%d")
        assert row["N° du justificatif"] == invoice.reference
        assert row["N° de virement"] == batch.label
        assert row["Intitulé du compte bancaire"] == bank_account.label
        assert row["SIRET du lieu"] == venue.siret
        assert row["IBAN"] == bank_account.iban
        assert row["Raison sociale du lieu"] == venue.name
        assert row["Adresse du lieu"] == f"{venue.address} {venue.postalCode} {venue.city}"
        assert row["SIRET du lieu"] == venue.siret
        assert row["Nom de l'offre"] == collective_offer.name
        assert row["N° de réservation (offre collective)"] == str(collective_booking.id)
        assert row["Nom (offre collective)"] == redactor.lastName
        assert row["Prénom (offre collective)"] == redactor.firstName
        assert row["Nom de l'établissement (offre collective)"] == institution.name
        assert row["Date de l'évènement (offre collective)"] == utc_datetime_to_department_timezone(
            collective_booking.collectiveStock.beginningDatetime, venue.departementCode
        ).strftime("%d/%m/%Y %H:%M")
        assert row["Contremarque"] == ""
        assert row["Date de validation de la réservation"] == collective_booking.dateUsed.strftime("%Y-%m-%d %H:%M:%S")
        assert row["Intitulé du tarif"] == ""
        assert row["Montant de la réservation"] == str(collective_booking.collectiveStock.price).replace(".", ",")
        assert row["Barème"].replace("\xa0", " ") == "100 %"
        assert row["Montant remboursé"] == "{:.2f}".format(-pricing.amount / 100).replace(".", ",")
