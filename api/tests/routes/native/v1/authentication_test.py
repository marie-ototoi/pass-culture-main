import copy
from datetime import datetime
import logging
from unittest.mock import patch
import uuid

from flask_jwt_extended import decode_token
from flask_jwt_extended.utils import create_access_token
from flask_jwt_extended.utils import create_refresh_token
from freezegun import freeze_time
import pytest

from pcapi import settings
from pcapi.connectors.dms import api as api_dms
from pcapi.connectors.dms import models as dms_models
from pcapi.core import token as token_utils
from pcapi.core.fraud import factories as fraud_factories
from pcapi.core.history import factories as history_factories
import pcapi.core.mails.testing as mails_testing
from pcapi.core.mails.transactional.sendinblue_template_ids import TransactionalEmail
from pcapi.core.subscription import api as subscription_api
from pcapi.core.testing import override_features
from pcapi.core.testing import override_settings
from pcapi.core.users import constants as users_constants
from pcapi.core.users import exceptions as users_exceptions
from pcapi.core.users import factories as users_factories
from pcapi.core.users import testing as sendinblue_testing
from pcapi.core.users.models import AccountState
from pcapi.core.users.models import LoginDeviceHistory
from pcapi.core.users.models import SingleSignOn
from pcapi.core.users.models import Token
from pcapi.core.users.models import TrustedDevice
from pcapi.models import db
import pcapi.notifications.push.testing as bash_testing
from pcapi.routes.native.v1 import authentication
from pcapi.utils import crypto

from tests.scripts.beneficiary.fixture import make_single_application


pytestmark = pytest.mark.usefixtures("db_session")


class SigninTest:
    def test_account_is_active_account_state(self, client, caplog):
        data = {"identifier": "user@test.com", "password": settings.TEST_DEFAULT_PASSWORD}
        users_factories.UserFactory(email=data["identifier"], password=data["password"], isActive=True)

        with caplog.at_level(logging.INFO):
            response = client.post("/native/v1/signin", json=data)
        assert response.status_code == 200
        assert response.json["accountState"] == AccountState.ACTIVE.value
        assert "Successful authentication attempt" in caplog.messages

    def test_account_suspended_upon_user_request_account_state(self, client):
        data = {"identifier": "user@test.com", "password": settings.TEST_DEFAULT_PASSWORD}
        user = users_factories.UserFactory(email=data["identifier"], password=data["password"], isActive=False)
        history_factories.SuspendedUserActionHistoryFactory(
            user=user, reason=users_constants.SuspensionReason.UPON_USER_REQUEST
        )

        response = client.post("/native/v1/signin", json=data)
        assert response.status_code == 200
        assert response.json["accountState"] == AccountState.SUSPENDED_UPON_USER_REQUEST.value

    def test_account_suspended_by_user_for_suspicious_login_account_state(self, client):
        data = {"identifier": "user@test.com", "password": settings.TEST_DEFAULT_PASSWORD}
        user = users_factories.UserFactory(email=data["identifier"], password=data["password"], isActive=False)
        history_factories.SuspendedUserActionHistoryFactory(
            user=user, reason=users_constants.SuspensionReason.SUSPICIOUS_LOGIN_REPORTED_BY_USER
        )

        response = client.post("/native/v1/signin", json=data)
        assert response.status_code == 200
        assert response.json["accountState"] == AccountState.SUSPICIOUS_LOGIN_REPORTED_BY_USER.value

    def test_account_deleted_account_state(self, client):
        data = {"identifier": "user@test.com", "password": settings.TEST_DEFAULT_PASSWORD}
        user = users_factories.UserFactory(email=data["identifier"], password=data["password"], isActive=False)
        history_factories.SuspendedUserActionHistoryFactory(user=user, reason=users_constants.SuspensionReason.DELETED)

        response = client.post("/native/v1/signin", json=data)
        assert response.status_code == 400
        assert response.json["code"] == "ACCOUNT_DELETED"

    def test_allow_inactive_user_sign(self, client):
        data = {"identifier": "user@test.com", "password": settings.TEST_DEFAULT_PASSWORD}
        users_factories.UserFactory(email=data["identifier"], password=data["password"], isActive=False)

        response = client.post("/native/v1/signin", json=data)
        assert response.status_code == 200

    def test_user_logs_in_and_refreshes_token(self, client):
        data = {"identifier": "user@test.com", "password": settings.TEST_DEFAULT_PASSWORD}
        user = users_factories.UserFactory(email=data["identifier"], password=data["password"])

        # Get the refresh and access token
        response = client.post("/native/v1/signin", json=data)
        assert response.status_code == 200
        assert response.json["refreshToken"]
        assert response.json["accessToken"]

        refresh_token = response.json["refreshToken"]
        access_token = response.json["accessToken"]

        # Ensure the access token is valid
        client.auth_header = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/native/v1/me")
        assert response.status_code == 200

        # Ensure the access token contains user.id
        decoded = decode_token(access_token)
        assert decoded["user_claims"]["user_id"] == user.id

        # Ensure the refresh token can generate a new access token
        client.auth_header = {"Authorization": f"Bearer {refresh_token}"}
        response = client.post("/native/v1/refresh_access_token", json={})
        assert response.status_code == 200, response.json
        assert response.json["accessToken"]
        access_token = response.json["accessToken"]

        # Ensure the new access token is valid
        client.auth_header = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/native/v1/me")
        assert response.status_code == 200

        # Ensure the new access token contains user.id
        decoded = decode_token(access_token)
        assert decoded["user_claims"]["user_id"] == user.id

    def test_user_logs_in_with_wrong_password(self, client, caplog):
        data = {"identifier": "user@test.com", "password": settings.TEST_DEFAULT_PASSWORD}
        users_factories.UserFactory(email=data["identifier"], password=data["password"])

        # signin with invalid password and ensures the result messsage is generic
        data["password"] = data["password"][:-2]
        with caplog.at_level(logging.INFO):
            response = client.post("/native/v1/signin", json=data)
        assert response.status_code == 400
        assert response.json == {"general": ["Identifiant ou Mot de passe incorrect"]}
        assert "Failed authentication attempt" in caplog.messages

    def test_unknown_user_logs_in(self, client, caplog):
        data = {"identifier": "user@test.com", "password": settings.TEST_DEFAULT_PASSWORD}

        # signin with invalid password and ensures the result messsage is generic
        with caplog.at_level(logging.INFO):
            response = client.post("/native/v1/signin", json=data)
        assert response.status_code == 400
        assert response.json == {"general": ["Identifiant ou Mot de passe incorrect"]}
        assert "Failed authentication attempt" in caplog.messages

    def test_user_logs_in_with_missing_fields(self, client):
        response = client.post("/native/v1/signin", json={})
        assert response.status_code == 400
        assert response.json == {
            "identifier": ["Ce champ est obligatoire"],
            "password": ["Ce champ est obligatoire"],
        }

    @override_features(ENABLE_NATIVE_APP_RECAPTCHA=False)
    @override_settings(RECAPTCHA_IGNORE_VALIDATION=0)
    @patch("pcapi.connectors.api_recaptcha.get_token_validation_and_score")
    def should_not_check_recaptcha_when_feature_flag_is_disabled(self, mocked_recaptcha_validation, client):
        mocked_recaptcha_validation.return_value = {"success": False, "error-codes": []}
        data = {
            "identifier": "user@test.com",
            "password": settings.TEST_DEFAULT_PASSWORD,
            "token": "invalid_token",
        }
        users_factories.UserFactory(email=data["identifier"], password=data["password"])

        response = client.post("/native/v1/signin", json=data)

        assert response.status_code == 200

    @override_settings(RECAPTCHA_IGNORE_VALIDATION=0)
    @patch("pcapi.connectors.api_recaptcha.get_token_validation_and_score")
    @pytest.mark.parametrize("error", ["invalid-input-response", "timeout-or-duplicate"])
    def test_fail_when_recaptcha_token_is_invalid(self, mocked_recaptcha_validation, error, client):
        mocked_recaptcha_validation.return_value = {"success": False, "error-codes": [error]}
        data = {
            "identifier": "user@test.com",
            "password": settings.TEST_DEFAULT_PASSWORD,
            "token": "invalid_token",
        }
        users_factories.UserFactory(email=data["identifier"], password=data["password"])

        response = client.post("/native/v1/signin", json=data)

        assert response.status_code == 401
        assert response.json == {"token": "Le token est invalide"}

    @override_settings(RECAPTCHA_IGNORE_VALIDATION=0)
    def test_fail_when_recaptcha_token_is_missing(self, client):
        data = {
            "identifier": "user@test.com",
            "password": settings.TEST_DEFAULT_PASSWORD,
        }
        users_factories.UserFactory(email=data["identifier"], password=data["password"])

        response = client.post("/native/v1/signin", json=data)

        assert response.status_code == 401
        assert response.json == {"token": "Le token est invalide"}

    @patch("pcapi.connectors.api_recaptcha.check_recaptcha_token_is_valid")
    def test_success_when_recaptcha_token_is_valid(self, mocked_check_recaptcha_token_is_valid, client):
        data = {
            "identifier": "user@test.com",
            "password": settings.TEST_DEFAULT_PASSWORD,
            "token": "valid_token",
        }
        users_factories.UserFactory(email=data["identifier"], password=data["password"])

        response = client.post("/native/v1/signin", json=data)

        mocked_check_recaptcha_token_is_valid.assert_called()
        assert response.status_code == 200

    @freeze_time("2020-03-15")
    def test_refresh_token_route_updates_user_last_connection_date(self, client):
        data = {"identifier": "user@test.com", "password": settings.TEST_DEFAULT_PASSWORD}
        user = users_factories.UserFactory(
            email=data["identifier"], password=data["password"], lastConnectionDate=datetime(1990, 1, 1)
        )

        refresh_token = create_refresh_token(identity=user.email)

        client.auth_header = {"Authorization": f"Bearer {refresh_token}"}
        refresh_response = client.post("/native/v1/refresh_access_token")
        assert refresh_response.status_code == 200

        assert user.lastConnectionDate == datetime(2020, 3, 15)
        assert len(sendinblue_testing.sendinblue_requests) == 1


class SSOSigninTest:
    valid_user = {
        "iss": "https://accounts.google.com",
        "azp": "427121120704-5r71oe05dt37jlsbg2d19hmhtk79bqat.apps.googleusercontent.com",
        "aud": "427121120704-5r71oe05dt37jlsbg2d19hmhtk79bqat.apps.googleusercontent.com",
        "sub": "100428144463745704968",
        "hd": "passculture.app",
        "email": "docteur.cuesta@passculture.app",
        "email_verified": True,
        "at_hash": "i8lKXlAVDYjKc6Krwsledg",
        "nonce": "k5Iy6eENx1AsYy20W405",
        "name": "Docteur Cuesta",
        "picture": "https://lh3.googleusercontent.com/a/ACg8ocKymVDJZjhFOcIEmgMMKs8h5hnzP3R6K64Qz3m4eEtf=s96-c",
        "given_name": "Docteur",
        "family_name": "Cuesta",
        "locale": "fr",
        "iat": 1697811815,
        "exp": 1697815415,
    }

    @patch("pcapi.routes.native.v1.authentication.oauth.google.parse_id_token")
    @patch("pcapi.routes.native.v1.authentication.oauth.google.fetch_access_token")
    @override_features(WIP_ENABLE_GOOGLE_SSO=True)
    def test_account_is_active(self, _mock_fetch_access_token, mock_parse_id_token, client, caplog):
        users_factories.SingleSignOnFactory(
            ssoUserId=self.valid_user["sub"], user__email=self.valid_user["email"], user__isActive=True
        )
        mock_parse_id_token.return_value = self.valid_user

        with caplog.at_level(logging.INFO):
            response = client.post("/native/v1/oauth/google/authorize", json={"authorizationCode": "4/google_code"})

        assert response.status_code == 200
        assert response.json["accountState"] == AccountState.ACTIVE.value
        assert "Successful authentication attempt" in caplog.messages

    @patch("pcapi.routes.native.v1.authentication.oauth.google.parse_id_token")
    @patch("pcapi.routes.native.v1.authentication.oauth.google.fetch_access_token")
    @override_features(WIP_ENABLE_GOOGLE_SSO=True)
    def test_account_is_deleted(self, _mock_fetch_access_token, mock_parse_id_token, client):
        user = users_factories.UserFactory(email=self.valid_user["email"], isActive=False)
        users_factories.SingleSignOnFactory(user=user, ssoUserId=self.valid_user["sub"])
        history_factories.SuspendedUserActionHistoryFactory(user=user, reason=users_constants.SuspensionReason.DELETED)
        mock_parse_id_token.return_value = self.valid_user

        response = client.post("/native/v1/oauth/google/authorize", json={"authorizationCode": "4/google_code"})

        assert response.status_code == 400
        assert response.json["code"] == "ACCOUNT_DELETED"

    @patch("pcapi.routes.native.v1.authentication.oauth.google.parse_id_token")
    @patch("pcapi.routes.native.v1.authentication.oauth.google.fetch_access_token")
    @override_features(WIP_ENABLE_GOOGLE_SSO=True)
    def test_account_does_not_exist(self, _mock_fetch_access_token, mock_parse_id_token, client, caplog):
        mock_parse_id_token.return_value = self.valid_user

        with caplog.at_level(logging.INFO):
            response = client.post("/native/v1/oauth/google/authorize", json={"authorizationCode": "4/google_code"})

        assert response.status_code == 401
        assert response.json == {"email": "unknown"}
        assert "Failed authentication attempt" in caplog.messages

    @patch("pcapi.routes.native.v1.authentication.oauth.google.parse_id_token")
    @patch("pcapi.routes.native.v1.authentication.oauth.google.fetch_access_token")
    @override_features(WIP_ENABLE_GOOGLE_SSO=True)
    def test_single_sign_on_ignores_email_if_found(self, _mock_fetch_access_token, mock_parse_id_token, client):
        user = users_factories.UserFactory(email="another@email.com", isActive=True)
        users_factories.SingleSignOnFactory(user=user, ssoUserId=self.valid_user["sub"])
        mock_parse_id_token.return_value = self.valid_user

        response = client.post("/native/v1/oauth/google/authorize", json={"authorizationCode": "4/google_code"})

        assert response.status_code == 200

    @patch("pcapi.routes.native.v1.authentication.oauth.google.parse_id_token")
    @patch("pcapi.routes.native.v1.authentication.oauth.google.fetch_access_token")
    @override_features(WIP_ENABLE_GOOGLE_SSO=True)
    def test_single_sign_on_inserts_sso_method_if_email_found(
        self, _mock_fetch_access_token, mock_parse_id_token, client
    ):
        user = users_factories.UserFactory(email=self.valid_user["email"], isActive=True)
        mock_parse_id_token.return_value = self.valid_user

        response = client.post("/native/v1/oauth/google/authorize", json={"authorizationCode": "4/google_code"})

        assert response.status_code == 200

        created_sso = SingleSignOn.query.filter(SingleSignOn.user == user, SingleSignOn.ssoProvider == "google").one()
        assert created_sso.ssoUserId == self.valid_user["sub"]

    @patch("pcapi.routes.native.v1.authentication.oauth.google.parse_id_token")
    @patch("pcapi.routes.native.v1.authentication.oauth.google.fetch_access_token")
    @override_features(WIP_ENABLE_GOOGLE_SSO=True)
    def test_single_sign_on_raises_if_email_not_validated(self, _mock_fetch_access_token, mock_parse_id_token, client):
        users_factories.UserFactory(email=self.valid_user["email"], isActive=True)
        unvalidated_email_google_user = copy.deepcopy(self.valid_user)
        unvalidated_email_google_user["email_verified"] = False
        mock_parse_id_token.return_value = unvalidated_email_google_user

        response = client.post("/native/v1/oauth/google/authorize", json={"authorizationCode": "4/google_code"})

        assert response.status_code == 400

    @patch("pcapi.routes.native.v1.authentication.oauth.google.parse_id_token")
    @patch("pcapi.routes.native.v1.authentication.oauth.google.fetch_access_token")
    @override_features(WIP_ENABLE_GOOGLE_SSO=True)
    def test_single_sign_on_does_not_duplicate_ssos(self, _mock_fetch_access_token, mock_parse_id_token, client):
        single_sign_on = users_factories.SingleSignOnFactory(ssoUserId=self.valid_user["sub"])
        mock_parse_id_token.return_value = self.valid_user

        response = client.post("/native/v1/oauth/google/authorize", json={"authorizationCode": "4/google_code"})

        assert response.status_code == 200
        assert SingleSignOn.query.filter(SingleSignOn.user == single_sign_on.user).count() == 1

    @patch("pcapi.routes.native.v1.authentication.oauth.google.parse_id_token")
    @patch("pcapi.routes.native.v1.authentication.oauth.google.fetch_access_token")
    @override_features(WIP_ENABLE_GOOGLE_SSO=True)
    def test_single_sign_on_raises_if_another_sso_is_already_configured(
        self, _mock_fetch_access_token, mock_parse_id_token, client
    ):
        users_factories.SingleSignOnFactory(user__email=self.valid_user["email"])
        mock_parse_id_token.return_value = self.valid_user

        response = client.post("/native/v1/oauth/google/authorize", json={"authorizationCode": "4/google_code"})

        assert response.status_code == 400
        assert SingleSignOn.query.filter(SingleSignOn.ssoUserId == self.valid_user["sub"]).count() == 0

    def test_sso_is_feature_flagged(self, client):
        response = client.post("/native/v1/oauth/google/authorize", json={"code": "4/google_code"})

        assert response.status_code == 400


class TrustedDeviceFeatureTest:
    data = {
        "identifier": "user@test.com",
        "password": settings.TEST_DEFAULT_PASSWORD,
        "deviceInfo": {
            "deviceId": "2E429592-2446-425F-9A62-D6983F375B3B",
            "source": "iPhone 13",
            "os": "iOS",
        },
    }
    headers = {"X-City": "Paris", "X-Country": "France"}
    one_month_in_seconds = 31 * 24 * 60 * 60
    one_year_in_seconds = 366 * 24 * 60 * 60

    @override_features(WIP_ENABLE_TRUSTED_DEVICE=True)
    def test_save_login_device_history_on_signin(self, client):
        users_factories.UserFactory(email=self.data["identifier"], password=self.data["password"], isActive=True)

        client.post("/native/v1/signin", json=self.data, headers=self.headers)

        login_device = LoginDeviceHistory.query.one()

        assert login_device.deviceId == self.data["deviceInfo"]["deviceId"]
        assert login_device.source == "iPhone 13"
        assert login_device.os == "iOS"
        assert login_device.location == "Paris, France"

    @override_features(WIP_ENABLE_TRUSTED_DEVICE=True)
    def should_not_save_login_device_history_on_signin_when_no_device_info(self, client):
        users_factories.UserFactory(email=self.data["identifier"], password=self.data["password"], isActive=True)

        client.post("/native/v1/signin", json={**self.data, "deviceInfo": None})

        assert LoginDeviceHistory.query.count() == 0

    @override_features(WIP_ENABLE_TRUSTED_DEVICE=False)
    def should_not_save_login_device_history_when_feature_flag_is_disabled(self, client):
        users_factories.UserFactory(email=self.data["identifier"], password=self.data["password"], isActive=True)

        client.post("/native/v1/signin", json=self.data)

        assert LoginDeviceHistory.query.count() == 0

    @override_features(WIP_ENABLE_TRUSTED_DEVICE=True)
    def test_save_login_device_as_trusted_device_on_second_signin_with_same_device(self, client):
        user = users_factories.UserFactory(email=self.data["identifier"], password=self.data["password"], isActive=True)

        client.post("/native/v1/signin", json=self.data)
        client.post("/native/v1/signin", json=self.data)

        trusted_device = TrustedDevice.query.filter(TrustedDevice.deviceId == self.data["deviceInfo"]["deviceId"]).one()
        assert user.trusted_devices == [trusted_device]

    @override_features(WIP_ENABLE_TRUSTED_DEVICE=False)
    def should_not_save_login_device_as_trusted_device_on_second_signin_when_feature_flag_is_inactive(
        self,
        client,
    ):
        user = users_factories.UserFactory(email=self.data["identifier"], password=self.data["password"], isActive=True)

        client.post("/native/v1/signin", json=self.data)
        client.post("/native/v1/signin", json=self.data)

        assert TrustedDevice.query.count() == 0
        assert user.trusted_devices == []

    @override_features(WIP_ENABLE_TRUSTED_DEVICE=True)
    def should_not_save_login_device_as_trusted_device_on_second_signin_when_using_different_devices(self, client):
        first_device = {
            "deviceId": "2E429592-2446-425F-9A62-D6983F375B3B",
            "source": "iPhone 13",
            "os": "iOS",
        }
        second_device = {
            "deviceId": "5F810092-1832-9A32-5B30-P2112F375G3G",
            "source": "Chrome",
            "os": "Mac OS",
        }
        user = users_factories.UserFactory(email=self.data["identifier"], password=self.data["password"], isActive=True)

        client.post("/native/v1/signin", json={**self.data, "deviceInfo": first_device})
        client.post("/native/v1/signin", json={**self.data, "deviceInfo": second_device})

        assert TrustedDevice.query.count() == 0
        assert user.trusted_devices == []

    @override_features(
        WIP_ENABLE_TRUSTED_DEVICE=True,
        WIP_ENABLE_SUSPICIOUS_EMAIL_SEND=True,
    )
    def should_send_email_when_login_is_suspicious(self, client):
        users_factories.UserFactory(email=self.data["identifier"], password=self.data["password"], isActive=True)

        client.post("/native/v1/signin", json=self.data, headers=self.headers)

        assert len(mails_testing.outbox) == 1
        assert mails_testing.outbox[0].sent_data["template"] == TransactionalEmail.SUSPICIOUS_LOGIN.value.__dict__
        assert mails_testing.outbox[0].sent_data["params"]["LOCATION"] == "Paris, France"
        assert mails_testing.outbox[0].sent_data["params"]["OS"] == "iOS"
        assert mails_testing.outbox[0].sent_data["params"]["SOURCE"] == "iPhone 13"
        assert mails_testing.outbox[0].sent_data["params"]["LOGIN_DATE"]
        assert mails_testing.outbox[0].sent_data["params"]["LOGIN_TIME"]
        assert mails_testing.outbox[0].sent_data["params"]["ACCOUNT_SECURING_LINK"]

    @override_features(
        WIP_ENABLE_TRUSTED_DEVICE=True,
        WIP_ENABLE_SUSPICIOUS_EMAIL_SEND=True,
    )
    def should_send_limited_number_of_emails_when_login_is_suspicious(self, client):
        users_factories.UserFactory(email=self.data["identifier"], password=self.data["password"], isActive=True)

        for _ in range(authentication.MAX_SUSPICIOUS_LOGIN_EMAILS + 1):
            data = copy.deepcopy(self.data)
            data["deviceInfo"]["deviceId"] = str(uuid.uuid4()).upper()
            client.post("/native/v1/signin", json=data, headers=self.headers)

        assert len(mails_testing.outbox) == authentication.MAX_SUSPICIOUS_LOGIN_EMAILS

    @override_features(
        WIP_ENABLE_TRUSTED_DEVICE=True,
        WIP_ENABLE_SUSPICIOUS_EMAIL_SEND=True,
    )
    def should_send_suspicious_login_email_to_user_suspended_upon_request(self, client):
        user = users_factories.UserFactory(email=self.data["identifier"], password=self.data["password"])
        history_factories.SuspendedUserActionHistoryFactory(
            user=user, reason=users_constants.SuspensionReason.UPON_USER_REQUEST
        )

        client.post("/native/v1/signin", json=self.data, headers=self.headers)

        assert len(mails_testing.outbox) == 1
        assert mails_testing.outbox[0].sent_data["template"] == TransactionalEmail.SUSPICIOUS_LOGIN.value.__dict__

    @override_features(
        WIP_ENABLE_TRUSTED_DEVICE=True,
        WIP_ENABLE_SUSPICIOUS_EMAIL_SEND=True,
    )
    @pytest.mark.parametrize(
        "reason",
        [
            users_constants.SuspensionReason.FRAUD_SUSPICION,
            users_constants.SuspensionReason.FRAUD_HACK,
            users_constants.SuspensionReason.SUSPENSION_FOR_INVESTIGATION_TEMP,
            users_constants.SuspensionReason.FRAUD_USURPATION,
        ],
    )
    def should_not_send_suspicious_login_email_to_suspended_user(self, client, reason):
        user = users_factories.UserFactory(
            email=self.data["identifier"], password=self.data["password"], isActive=False
        )
        history_factories.SuspendedUserActionHistoryFactory(user=user, reason=reason)

        client.post("/native/v1/signin", json=self.data, headers=self.headers)

        assert len(mails_testing.outbox) == 0

    @override_features(
        WIP_ENABLE_TRUSTED_DEVICE=True,
        WIP_ENABLE_SUSPICIOUS_EMAIL_SEND=True,
    )
    def should_extend_refresh_token_lifetime_when_logging_in_with_a_trusted_device(self, client):
        user = users_factories.UserFactory(email=self.data["identifier"], password=self.data["password"], isActive=True)
        users_factories.TrustedDeviceFactory(user=user, deviceId=self.data["deviceInfo"]["deviceId"])

        response = client.post("/native/v1/signin", json=self.data)

        decoded_refresh_token = decode_token(response.json["refreshToken"])
        token_issue_date = decoded_refresh_token["iat"]
        token_expiration_date = decoded_refresh_token["exp"]
        refresh_token_lifetime = token_expiration_date - token_issue_date

        assert refresh_token_lifetime == settings.JWT_REFRESH_TOKEN_EXTENDED_EXPIRES

    @override_features(
        WIP_ENABLE_TRUSTED_DEVICE=True,
        WIP_ENABLE_SUSPICIOUS_EMAIL_SEND=True,
    )
    def should_not_extend_refresh_token_lifetime_when_logging_in_from_unknown_device(self, client):
        users_factories.UserFactory(email=self.data["identifier"], password=self.data["password"], isActive=True)

        response = client.post("/native/v1/signin", json=self.data)

        decoded_refresh_token = decode_token(response.json["refreshToken"])
        token_issue_date = decoded_refresh_token["iat"]
        token_expiration_date = decoded_refresh_token["exp"]
        refresh_token_lifetime = token_expiration_date - token_issue_date

        assert refresh_token_lifetime == settings.JWT_REFRESH_TOKEN_EXPIRES

    @override_features(
        WIP_ENABLE_TRUSTED_DEVICE=True,
        WIP_ENABLE_SUSPICIOUS_EMAIL_SEND=True,
    )
    def should_extend_refresh_token_lifetime_on_email_validation_when_device_is_trusted(self, client):
        user = users_factories.UserFactory(isEmailValidated=False)
        users_factories.TrustedDeviceFactory(user=user, deviceId=self.data["deviceInfo"]["deviceId"])
        token = token_utils.Token.create(
            type_=token_utils.TokenType.EMAIL_VALIDATION,
            ttl=users_constants.EMAIL_VALIDATION_TOKEN_LIFE_TIME,
            user_id=user.id,
        ).encoded_token

        response = client.post(
            "/native/v1/validate_email",
            json={"email_validation_token": token, "deviceInfo": self.data["deviceInfo"]},
        )

        decoded_refresh_token = decode_token(response.json["refreshToken"])
        token_issue_date = decoded_refresh_token["iat"]
        token_expiration_date = decoded_refresh_token["exp"]
        refresh_token_lifetime = token_expiration_date - token_issue_date

        assert refresh_token_lifetime == settings.JWT_REFRESH_TOKEN_EXTENDED_EXPIRES

    @override_features(
        WIP_ENABLE_TRUSTED_DEVICE=True,
        WIP_ENABLE_SUSPICIOUS_EMAIL_SEND=True,
    )
    def should_not_extend_refresh_token_lifetime_on_email_validation_when_device_is_unknown(self, client):
        user = users_factories.UserFactory(isEmailValidated=False)
        token = token_utils.Token.create(
            type_=token_utils.TokenType.EMAIL_VALIDATION,
            ttl=users_constants.EMAIL_VALIDATION_TOKEN_LIFE_TIME,
            user_id=user.id,
        ).encoded_token

        response = client.post("/native/v1/validate_email", json={"email_validation_token": token})

        decoded_refresh_token = decode_token(response.json["refreshToken"])
        token_issue_date = decoded_refresh_token["iat"]
        token_expiration_date = decoded_refresh_token["exp"]
        refresh_token_lifetime = token_expiration_date - token_issue_date

        assert refresh_token_lifetime == settings.JWT_REFRESH_TOKEN_EXPIRES

    @override_features(WIP_ENABLE_TRUSTED_DEVICE=True)
    def should_not_send_email_when_logging_in_from_a_trusted_device(self, client):
        user = users_factories.UserFactory(email=self.data["identifier"], password=self.data["password"], isActive=True)
        users_factories.TrustedDeviceFactory(user=user)

        client.post("/native/v1/signin", json=self.data)

        assert len(mails_testing.outbox) == 0

    @override_features(WIP_ENABLE_TRUSTED_DEVICE=False)
    def should_not_send_email_when_feature_flag_is_inactive(self, client):
        users_factories.UserFactory(email=self.data["identifier"], password=self.data["password"], isActive=True)

        client.post("/native/v1/signin", json=self.data)

        assert len(mails_testing.outbox) == 0

    @override_features(
        WIP_ENABLE_TRUSTED_DEVICE=True,
        WIP_ENABLE_SUSPICIOUS_EMAIL_SEND=False,
    )
    def should_not_send_email_when_feature_flag_is_active_but_email_is_inactive(self, client):
        users_factories.UserFactory(email=self.data["identifier"], password=self.data["password"], isActive=True)

        client.post("/native/v1/signin", json=self.data)

        assert len(mails_testing.outbox) == 0


class RequestResetPasswordTest:
    def test_send_reset_password_email_without_email(self, client):
        response = client.post(
            "/native/v1/request_password_reset",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 400
        assert response.json["email"] == ["Ce champ est obligatoire"]

    def test_request_reset_password_for_unknown_email(self, client):
        data = {"email": "not_existing_user@example.com"}
        response = client.post("/native/v1/request_password_reset", json=data)

        assert response.status_code == 204

    @patch("pcapi.connectors.api_recaptcha.check_native_app_recaptcha_token")
    @override_features(ENABLE_NATIVE_APP_RECAPTCHA=True)
    def test_request_reset_password_with_recaptcha_ok(
        self,
        mock_check_native_app_recaptcha_token,
        client,
    ):
        email = "existing_user@example.com"
        data = {"email": email}
        user = users_factories.UserFactory(email=email)

        saved_token = Token.query.filter_by(user=user).first()
        assert saved_token is None

        mock_check_native_app_recaptcha_token.return_value = None

        response = client.post("/native/v1/request_password_reset", json=data)

        mock_check_native_app_recaptcha_token.assert_called_once()
        assert response.status_code == 204

        assert token_utils.Token.token_exists(token_utils.TokenType.RESET_PASSWORD, user.id)

        assert len(mails_testing.outbox) == 1
        assert mails_testing.outbox[0].sent_data["params"]["RESET_PASSWORD_LINK"]

    def test_request_reset_password_for_existing_email(self, client):
        email = "existing_user@example.com"
        data = {"email": email}
        user = users_factories.UserFactory(email=email)

        saved_token = Token.query.filter_by(user=user).first()
        assert saved_token is None

        response = client.post("/native/v1/request_password_reset", json=data)

        assert response.status_code == 204

        assert token_utils.Token.token_exists(token_utils.TokenType.RESET_PASSWORD, user.id)
        assert len(mails_testing.outbox) == 1
        assert mails_testing.outbox[0].sent_data["params"]["RESET_PASSWORD_LINK"]

    @patch("pcapi.core.mails.transactional.send_reset_password_email_to_user")
    def test_request_reset_password_with_mail_service_exception(self, mock_send_reset_password_email_to_user, client):
        email = "tt_user@example.com"
        data = {"email": email}
        users_factories.UserFactory(email=email)

        mock_send_reset_password_email_to_user.return_value = False

        response = client.post("/native/v1/request_password_reset", json=data)

        mock_send_reset_password_email_to_user.assert_called_once()
        assert response.status_code == 400
        assert response.json["email"] == ["L'email n'a pas pu être envoyé"]

    def test_reset_password_with_not_valid_token(self, client):
        data = {"reset_password_token": "unknown_token", "new_password": "new_password"}
        user = users_factories.UserFactory()
        old_password = user.password

        response = client.post("/native/v1/reset_password", json=data)

        assert response.status_code == 400
        assert user.password == old_password

    def test_reset_password_success(self, client):
        new_password = "New_password1998!"

        user = users_factories.UserFactory()
        token = token_utils.Token.create(
            token_utils.TokenType.RESET_PASSWORD, users_constants.RESET_PASSWORD_TOKEN_LIFE_TIME, user_id=user.id
        )

        data = {"reset_password_token": token.encoded_token, "new_password": new_password}
        response = client.post("/native/v1/reset_password", json=data)

        assert response.status_code == 200
        db.session.refresh(user)
        assert user.password == crypto.hash_password(new_password)

        with pytest.raises(users_exceptions.InvalidToken):
            token.check(token_utils.TokenType.RESET_PASSWORD)
        # Ensure the access token is valid
        access_token = response.json["accessToken"]
        client.auth_header = {"Authorization": f"Bearer {access_token}"}
        protected_response = client.get("/native/v1/me")
        assert protected_response.status_code == 200

        # Ensure the refresh token is valid
        refresh_token = response.json["refreshToken"]
        client.auth_header = {"Authorization": f"Bearer {refresh_token}"}
        refresh_response = client.post("/native/v1/refresh_access_token", json={})
        assert refresh_response.status_code == 200

    @patch("pcapi.core.subscription.dms.api.try_dms_orphan_adoption")
    def test_reset_password_for_unvalidated_email(self, try_dms_orphan_adoption_mock, client):
        new_password = "New_password1998!"

        user = users_factories.UserFactory(isEmailValidated=False)
        token = token_utils.Token.create(
            token_utils.TokenType.RESET_PASSWORD, users_constants.RESET_PASSWORD_TOKEN_LIFE_TIME, user_id=user.id
        )

        data = {"reset_password_token": token.encoded_token, "new_password": new_password}
        response = client.post("/native/v1/reset_password", json=data)

        assert response.status_code == 200
        db.session.refresh(user)
        assert user.password == crypto.hash_password(new_password)
        try_dms_orphan_adoption_mock.assert_called_once_with(user)
        assert user.isEmailValidated

        # Ensure the access token is valid
        access_token = response.json["accessToken"]
        client.auth_header = {"Authorization": f"Bearer {access_token}"}
        protected_response = client.get("/native/v1/me")
        assert protected_response.status_code == 200

        # Ensure the refresh token is valid
        refresh_token = response.json["refreshToken"]
        client.auth_header = {"Authorization": f"Bearer {refresh_token}"}
        refresh_response = client.post("/native/v1/refresh_access_token", json={})
        assert refresh_response.status_code == 200

    def test_reset_password_fail_for_password_strength(self, client):
        user = users_factories.UserFactory()
        token = token_utils.Token.create(
            token_utils.TokenType.RESET_PASSWORD, users_constants.RESET_PASSWORD_TOKEN_LIFE_TIME, user_id=user.id
        )

        old_password = user.password
        new_password = "weak_password"

        data = {"reset_password_token": token.encoded_token, "new_password": new_password}

        response = client.post("/native/v1/reset_password", json=data)

        assert response.status_code == 400
        db.session.refresh(user)
        assert user.password == old_password
        # should note raise
        token.check(token_utils.TokenType.RESET_PASSWORD)

    def test_change_password_success(self, client):
        new_password = "New_password1998!"
        user = users_factories.UserFactory()

        access_token = create_access_token(identity=user.email)
        client.auth_header = {"Authorization": f"Bearer {access_token}"}

        response = client.post(
            "/native/v1/change_password",
            json={"currentPassword": settings.TEST_DEFAULT_PASSWORD, "newPassword": new_password},
        )

        assert response.status_code == 204
        db.session.refresh(user)
        assert user.password == crypto.hash_password(new_password)

    def test_change_password_failures(self, client):
        new_password = "New_password1998!"
        user = users_factories.UserFactory()

        access_token = create_access_token(identity=user.email)
        client.auth_header = {"Authorization": f"Bearer {access_token}"}

        response = client.post(
            "/native/v1/change_password",
            json={"currentPassword": "wrong_password", "newPassword": new_password},
        )

        assert response.status_code == 400
        assert response.json["code"] == "INVALID_PASSWORD"

        response = client.post(
            "/native/v1/change_password",
            json={"currentPassword": settings.TEST_DEFAULT_PASSWORD, "newPassword": "weak_password"},
        )

        assert response.status_code == 400
        assert response.json["code"] == "WEAK_PASSWORD"
        db.session.refresh(user)
        assert user.password == crypto.hash_password(settings.TEST_DEFAULT_PASSWORD)


class InactiveAccountRequestResetPasswordTest:
    def test_suspended_upon_user_request(self, client):
        user = users_factories.UserFactory(email="existing_user@example.com", isActive=False)
        history_factories.SuspendedUserActionHistoryFactory(
            user=user, reason=users_constants.SuspensionReason.UPON_USER_REQUEST
        )

        response = client.post("/native/v1/request_password_reset", json={"email": user.email})
        self.assert_email_is_sent(response, user)

    def test_suspended_account(self, client):
        user = users_factories.UserFactory(email="existing_user@example.com", isActive=False)
        history_factories.SuspendedUserActionHistoryFactory(
            user=user, reason=users_constants.SuspensionReason.FRAUD_SUSPICION
        )

        response = client.post("/native/v1/request_password_reset", json={"email": user.email})
        self.assert_email_is_sent(response, user)

    def test_deleted_account(self, client):
        user = users_factories.UserFactory(email="existing_user@example.com", isActive=False)
        history_factories.SuspendedUserActionHistoryFactory(user=user, reason=users_constants.SuspensionReason.DELETED)

        response = client.post("/native/v1/request_password_reset", json={"email": user.email})
        self.assert_email_is_sent(response, user)

    def assert_email_is_sent(self, response, user):
        assert response.status_code == 204

        assert token_utils.Token.token_exists(token_utils.TokenType.RESET_PASSWORD, user.id)
        assert len(mails_testing.outbox) == 1
        assert mails_testing.outbox[0].sent_data["params"]["RESET_PASSWORD_LINK"]


class EmailValidationTest:
    def initialize_token(self, user, is_expired=False):
        token = token_utils.Token.create(
            type_=token_utils.TokenType.EMAIL_VALIDATION,
            ttl=users_constants.EMAIL_VALIDATION_TOKEN_LIFE_TIME,
            user_id=user.id,
        )
        if is_expired:
            token.expire()
        return token.encoded_token

    def test_validate_email_with_expired_token(self, client):
        user = users_factories.UserFactory(isEmailValidated=False)
        token = self.initialize_token(
            user=user,
            is_expired=True,
        )

        response = client.post("/native/v1/validate_email", json={"email_validation_token": token})

        assert response.status_code == 400

    @freeze_time("2018-06-01")
    def test_validate_email_when_eligible(self, client):
        user = users_factories.UserFactory(
            isEmailValidated=False,
            dateOfBirth=datetime(2000, 6, 1),
        )
        token = self.initialize_token(user)

        response = client.post("/native/v1/validate_email", json={"email_validation_token": token})

        assert user.isEmailValidated
        assert response.status_code == 200

        # Ensure the access token is valid
        access_token = response.json["accessToken"]
        client.auth_header = {"Authorization": f"Bearer {access_token}"}
        protected_response = client.get("/native/v1/me")
        assert protected_response.status_code == 200

        # assert we updated the external users
        assert len(bash_testing.requests) == 2
        assert len(sendinblue_testing.sendinblue_requests) == 1

        # Ensure the access token contains user.id
        decoded = decode_token(access_token)
        assert decoded["user_claims"]["user_id"] == user.id

        # Ensure the refresh token is valid
        refresh_token = response.json["refreshToken"]
        client.auth_header = {"Authorization": f"Bearer {refresh_token}"}
        refresh_response = client.post("/native/v1/refresh_access_token", json={})
        assert refresh_response.status_code == 200

    def test_validate_email_second_time_is_forbidden(self, client):
        user = users_factories.UserFactory(isEmailValidated=False)
        token = self.initialize_token(user)

        response = client.post("/native/v1/validate_email", json={"email_validation_token": token})

        assert user.isEmailValidated
        assert response.status_code == 200

        response = client.post("/native/v1/validate_email", json={"email_validation_token": token})
        assert response.status_code == 400
        assert response.json["token"] == ["Le token de validation d'email est invalide."]

    @freeze_time("2018-06-01")
    def test_validate_email_when_not_eligible(self, client):
        user = users_factories.UserFactory(isEmailValidated=False, dateOfBirth=datetime(2000, 7, 1))
        token = self.initialize_token(user)

        assert not user.isEmailValidated

        response = client.post("/native/v1/validate_email", json={"email_validation_token": token})

        assert user.isEmailValidated
        assert response.status_code == 200

        # assert we updated the external users
        assert len(bash_testing.requests) == 2
        assert len(sendinblue_testing.sendinblue_requests) == 1

        # Ensure the access token is valid
        access_token = response.json["accessToken"]
        client.auth_header = {"Authorization": f"Bearer {access_token}"}
        protected_response = client.get("/native/v1/me")
        assert protected_response.status_code == 200

        # Ensure the refresh token is valid
        refresh_token = response.json["refreshToken"]
        client.auth_header = {"Authorization": f"Bearer {refresh_token}"}
        refresh_response = client.post("/native/v1/refresh_access_token", json={})
        assert refresh_response.status_code == 200

    @patch.object(api_dms.DMSGraphQLClient, "execute_query")
    def test_validate_email_dms_orphan(self, execute_query, client):
        application_number = 1234
        email = "dms_orphan@example.com"

        user = users_factories.UserFactory(isEmailValidated=False, dateOfBirth=datetime(2000, 7, 1), email=email)
        token = self.initialize_token(user)

        assert not user.isEmailValidated

        fraud_factories.OrphanDmsApplicationFactory(email=email, application_id=application_number)

        execute_query.return_value = make_single_application(
            application_number, dms_models.GraphQLApplicationStates.accepted, email=email
        )
        response = client.post("/native/v1/validate_email", json={"email_validation_token": token})

        assert user.isEmailValidated
        assert response.status_code == 200

        fraud_check = subscription_api.get_relevant_identity_fraud_check(user, user.eligibility)
        assert fraud_check is not None
