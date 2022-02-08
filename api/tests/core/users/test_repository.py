from datetime import date
from datetime import datetime
from datetime import timedelta

from freezegun import freeze_time
import pytest

from pcapi.core.bookings import factories as bookings_factories
from pcapi.core.offerers import factories as offerers_factories
from pcapi.core.offers import factories as offers_factories
from pcapi.core.users import exceptions
from pcapi.core.users import factories as users_factories
from pcapi.core.users import repository
from pcapi.core.users.models import UserRole
from pcapi.core.users.repository import get_users_with_validated_attachment_by_offerer


pytestmark = pytest.mark.usefixtures("db_session")


class CheckUserAndCredentialsTest:
    def test_unknown_user(self):
        with pytest.raises(exceptions.InvalidIdentifier):
            repository.check_user_and_credentials(None, "doe")

    def test_user_with_invalid_password(self):
        user = users_factories.UserFactory.build(isActive=True)
        with pytest.raises(exceptions.InvalidIdentifier):
            repository.check_user_and_credentials(user, "123")

    def test_inactive_user_with_invalid_password(self):
        user = users_factories.UserFactory.build(isActive=False)
        with pytest.raises(exceptions.InvalidIdentifier):
            repository.check_user_and_credentials(user, "123")

    def test_user_pending_validation_wrong_password(self):
        user = users_factories.UserFactory.build(isActive=True, validationToken="123")
        with pytest.raises(exceptions.InvalidIdentifier):
            repository.check_user_and_credentials(user, "doe")

    def test_user_pending_email_validation_wrong_password(self):
        user = users_factories.UserFactory.build(isActive=True, isEmailValidated=False)
        with pytest.raises(exceptions.InvalidIdentifier):
            repository.check_user_and_credentials(user, "doe")

    def test_with_inactive_user(self):
        user = users_factories.UserFactory.build(isActive=False)
        with pytest.raises(exceptions.InvalidIdentifier):
            repository.check_user_and_credentials(user, users_factories.DEFAULT_PASSWORD)

    def test_user_pending_validation(self):
        user = users_factories.UserFactory.build(isActive=True, validationToken="123")
        with pytest.raises(exceptions.UnvalidatedAccount):
            repository.check_user_and_credentials(user, users_factories.DEFAULT_PASSWORD)

    def test_user_pending_email_validation(self):
        user = users_factories.UserFactory.build(isActive=True, isEmailValidated=False)
        with pytest.raises(exceptions.UnvalidatedAccount):
            repository.check_user_and_credentials(user, users_factories.DEFAULT_PASSWORD)

    def test_user_with_valid_password(self):
        user = users_factories.UserFactory.build(isActive=True)
        repository.check_user_and_credentials(user, users_factories.DEFAULT_PASSWORD)


class GetNewlyEligibleUsersTest:
    @freeze_time("2018-01-01")
    def test_eligible_user(self):
        user_already_18 = users_factories.UserFactory(
            dateOfBirth=datetime(1999, 12, 31), dateCreated=datetime(2017, 12, 1)
        )
        user_just_18 = users_factories.UserFactory(
            dateOfBirth=datetime(2000, 1, 1),
            dateCreated=datetime(2017, 12, 31),
        )
        user_just_18_ex_underage_beneficiary = users_factories.UserFactory(
            dateOfBirth=datetime(2000, 1, 1),
            dateCreated=datetime(2017, 12, 1),
            roles=[UserRole.UNDERAGE_BENEFICIARY],
        )
        # Possible beneficiary that registered too late
        users_factories.UserFactory(dateOfBirth=datetime(2000, 1, 1), dateCreated=datetime(2018, 1, 1))
        # Admin
        users_factories.AdminFactory(dateOfBirth=datetime(2000, 1, 1), dateCreated=datetime(2018, 1, 1))
        # Pro
        pro_user = users_factories.ProFactory(dateOfBirth=datetime(2000, 1, 1), dateCreated=datetime(2018, 1, 1))
        offers_factories.UserOffererFactory(user=pro_user)
        # User not yet 18
        users_factories.UserFactory(dateOfBirth=datetime(2000, 1, 2), dateCreated=datetime(2017, 12, 1))

        # Users 18 on the day `since` should not appear, nor those that are not 18 yet
        users = repository.get_newly_eligible_age_18_users(since=date(2017, 12, 31))
        assert set(users) == {user_just_18, user_just_18_ex_underage_beneficiary}
        users = repository.get_newly_eligible_age_18_users(since=date(2017, 12, 30))
        assert set(users) == {user_just_18, user_just_18_ex_underage_beneficiary, user_already_18}


class GetApplicantOfOffererUnderValidationTest:
    def test_return_user_with_validated_attachment(self):
        # Given
        applicant = users_factories.UserFactory()
        user_who_asked_for_attachment = users_factories.UserFactory()
        applied_offerer = offerers_factories.OffererFactory(validationToken="TOKEN")
        offers_factories.UserOffererFactory(offerer=applied_offerer, user=applicant)
        offers_factories.UserOffererFactory(
            offerer=applied_offerer, user=user_who_asked_for_attachment, validationToken="OTHER_TOKEN"
        )

        # When
        applicants_found = get_users_with_validated_attachment_by_offerer(applied_offerer)

        # Then
        assert len(applicants_found) == 1
        assert applicants_found[0].id == applicant.id


class GetUsersInactiveFavoritesTest:
    def test_get_favorites(self):
        """
        Test that the function returns the one and only expected
        favorite within all the other ones.
        """
        three_days_ago = date.today() - timedelta(days=3)
        user = users_factories.BeneficiaryGrant18Factory()

        stock = offers_factories.EventStockFactory()
        expected_favorite = users_factories.FavoriteFactory(offer=stock.offer, user=user, dateCreated=three_days_ago)

        # 1. Notification for this favorite already sent
        stock = offers_factories.EventStockFactory()
        users_factories.FavoriteFactory(
            offer=stock.offer, user=user, dateCreated=three_days_ago, extra={"notification": date.today()}
        )

        # 2. Favorite created less than three days ago
        stock = offers_factories.EventStockFactory()
        users_factories.FavoriteFactory(offer=stock.offer, user=user)

        # 3. Favorite linked to an offer that has no stock left
        stock = offers_factories.EventStockFactory(quantity=0)
        users_factories.FavoriteFactory(offer=stock.offer, user=user)

        # 4. Favorite linked to an expired offer
        stock = offers_factories.EventStockFactory(beginningDatetime=three_days_ago)
        users_factories.FavoriteFactory(offer=stock.offer, user=user)

        # 5. Favorite linked to an offer that have already been booked
        offer = offers_factories.DigitalOfferFactory()
        stock = offers_factories.StockFactory(offer=offer)
        bookings_factories.BookingFactory(stock=stock, user=user)
        users_factories.FavoriteFactory(offer=offer, user=user)

        res = list(repository.get_inactive_favorites_for_notification())
        assert res == [expected_favorite]

    def test_no_favorites(self):
        """
        Test that the function does not crash and returns nothing
        """
        assert not list(repository.get_inactive_favorites_for_notification())


class GetSubcategoriesCountPerUserTest:
    def test_get_subcategories_count_per_user(self):
        stock = offers_factories.ThingStockFactory()
        subcategory_ids = {stock.offer.subcategoryId}

        users = users_factories.BeneficiaryGrant18Factory.create_batch(3)
        user_ids = {user.id for user in users}

        # For each user, create a different number of bookings
        for idx, user in enumerate(users, start=1):
            bookings_factories.BookingFactory.create_batch(idx, stock=stock, user=user)

        res = repository.get_subcategories_count_per_user(user_ids, subcategory_ids)
        res = sorted(res, key=lambda x: x.user_id)

        assert res == [
            repository.SubcategoryCount(user_id=user.id, subcategory=stock.offer.subcategoryId, count=count)
            for count, user in enumerate(users, start=1)
        ]
