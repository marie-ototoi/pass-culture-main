from unittest.mock import patch, call

from models.db import db
from repository import repository
import pytest
from tests.conftest import TestClient
from model_creators.generic_creators import create_offerer, create_venue


class Get:
    class Returns202:
        @pytest.mark.usefixtures("db_session")
        def expect_validation_token_to_be_none(self, app):
            # Given
            offerer = create_offerer()
            venue = create_venue(offerer)
            venue.generate_validation_token()
            repository.save(venue)

            token = venue.validationToken

            # When
            response = TestClient(app.test_client()).get('/validate/venue?token={}'.format(token))

            # Then
            assert response.status_code == 202
            db.session.refresh(venue)
            assert venue.isValidated

        @patch('routes.validate.feature_queries.is_active', return_value=True)
        @patch('routes.validate.redis.add_venue_id')
        @pytest.mark.usefixtures("db_session")
        def expect_venue_id_to_be_added_to_redis(self, mock_redis, mock_feature, app):
            # Given
            offerer = create_offerer()
            venue = create_venue(offerer)
            venue.generate_validation_token()
            repository.save(venue)

            # When
            response = TestClient(app.test_client()).get(f'/validate/venue?token={venue.validationToken}')

            # Then
            assert response.status_code == 202
            assert mock_redis.call_count == 1
            assert mock_redis.call_args_list == [
                call(client=app.redis_client, venue_id=venue.id)
            ]

        @pytest.mark.usefixtures("db_session")
        @patch('routes.validate.link_valid_venue_to_irises')
        def expect_link_venue_to_iris_if_valid_to_be_called_for_validated_venue(self, mocked_link_venue_to_iris_if_valid, app):
            # Given
            offerer = create_offerer()
            venue = create_venue(offerer)
            venue.generate_validation_token()
            repository.save(venue)

            token = venue.validationToken

            # When
            response = TestClient(app.test_client()).get(f'/validate/venue?token={token}')

            # Then
            assert response.status_code == 202
            mocked_link_venue_to_iris_if_valid.assert_called_once_with(venue)

    class Returns400:
        @pytest.mark.usefixtures("db_session")
        def when_no_validation_token_is_provided(self, app):
            # When
            response = TestClient(app.test_client()).get('/validate/venue')

            # Then
            assert response.status_code == 400
            assert response.json['token'] == ['Vous devez fournir un jeton de validation']

    class Returns404:
        @pytest.mark.usefixtures("db_session")
        def when_validation_token_is_unknown(self, app):
            # When
            response = TestClient(app.test_client()).get(f'/validate/venue?token=12345')

            # Then
            assert response.status_code == 404
            assert response.json['token'] == ['Jeton inconnu']
