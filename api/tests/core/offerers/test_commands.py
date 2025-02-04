from unittest.mock import patch

import freezegun
import pytest

from pcapi.core.offerers import factories as offerers_factories

from tests.test_utils import run_command


pytestmark = pytest.mark.usefixtures("db_session")


class CheckActiveOfferersTest:
    @patch("pcapi.connectors.sirene.get_siren")
    def test_check_active_offerers(self, mock_get_siren, app):
        tag = offerers_factories.OffererTagFactory(name="siren-caduc")

        offerers_factories.OffererFactory(id=23 + 27)  # not checked today
        offerer = offerers_factories.OffererFactory(id=23 + 28)
        offerers_factories.OffererFactory(id=23 + 29)  # not checked today
        offerers_factories.OffererFactory(id=23 + 28 * 2, isActive=False)  # not checked because inactive
        offerers_factories.OffererFactory(id=23 + 28 * 3, tags=[tag])  # not checked because already tagged

        with freezegun.freeze_time("2024-12-24 23:00:00"):
            run_command(app, "check_active_offerers")

        # Only check that the task is called; its behavior is tested in test_api.py
        mock_get_siren.assert_called_once_with(offerer.siren, with_address=False, raise_if_non_public=False)
