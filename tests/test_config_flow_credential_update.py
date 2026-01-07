"""Test credential update via options flow."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from flowerhub.config_flow import OptionsFlowHandler
from homeassistant.core import HomeAssistant


class DummyEntry:
    """Dummy config entry for testing."""

    def __init__(self, data=None, options=None):
        self.entry_id = "test_entry_id"
        self.data = data or {}
        self.options = options or {}

    def add_to_hass(self, hass):
        """Mock method."""
        pass


@pytest.mark.asyncio
async def test_options_flow_credential_update_success(hass: HomeAssistant):
    """Test successfully updating credentials via options flow."""
    # Create a dummy config entry
    entry = DummyEntry(
        data={"username": "old_user", "password": "old_pass"},
        options={"scan_interval": 60},
    )

    # Mock the hass.config_entries.async_update_entry method
    update_entry_mock = MagicMock()
    hass.config_entries = MagicMock()
    hass.config_entries.async_update_entry = update_entry_mock

    # Mock the client to simulate successful authentication
    with patch(
        "flowerhub_portal_api_client.AsyncFlowerhubClient"
    ) as mock_client_class, patch("flowerhub.config_flow.async_get_clientsession"):
        mock_client = AsyncMock()
        mock_client.async_login = AsyncMock()
        mock_client.async_readout_sequence = AsyncMock()
        mock_client_class.return_value = mock_client

        # Start the options flow
        flow = OptionsFlowHandler(entry)
        flow.hass = hass  # Ensure flow has hass reference
        result = await flow.async_step_init()

        assert result["type"] == "form"
        assert result["step_id"] == "init"

        # Submit new credentials and scan interval
        result = await flow.async_step_init(
            user_input={
                "username": "new_user",
                "password": "new_pass",
                "scan_interval": 120,
            }
        )

        assert result["type"] == "create_entry"
        assert result["data"] == {"scan_interval": 120}

        # Verify credentials were validated
        mock_client.async_login.assert_called_once_with("new_user", "new_pass")
        mock_client.async_readout_sequence.assert_called_once()

        # Verify async_update_entry was called with new credentials
        update_entry_mock.assert_called_once()
        call_args = update_entry_mock.call_args
        assert call_args[0][0] == entry  # First positional arg is the entry
        assert call_args[1]["data"] == {"username": "new_user", "password": "new_pass"}


@pytest.mark.asyncio
async def test_options_flow_credential_validation_fails(hass: HomeAssistant):
    """Test credential update fails when validation fails."""
    # Create a dummy config entry
    entry = DummyEntry(
        data={"username": "old_user", "password": "old_pass"},
        options={"scan_interval": 60},
    )

    # Mock the hass.config_entries.async_update_entry method
    update_entry_mock = MagicMock()
    hass.config_entries = MagicMock()
    hass.config_entries.async_update_entry = update_entry_mock

    # Mock the client to simulate failed authentication
    with patch(
        "flowerhub_portal_api_client.AsyncFlowerhubClient"
    ) as mock_client_class, patch("flowerhub.config_flow.async_get_clientsession"):
        mock_client = AsyncMock()
        mock_client.async_login = AsyncMock(
            side_effect=Exception("Invalid credentials")
        )
        mock_client_class.return_value = mock_client

        # Start the options flow
        flow = OptionsFlowHandler(entry)
        flow.hass = hass  # Ensure flow has hass reference
        result = await flow.async_step_init()

        assert result["type"] == "form"
        assert result["step_id"] == "init"

        # Submit invalid credentials
        result = await flow.async_step_init(
            user_input={
                "username": "bad_user",
                "password": "bad_pass",
                "scan_interval": 120,
            }
        )

        assert result["type"] == "form"
        assert result["errors"] == {"base": "cannot_connect"}

        # Verify async_update_entry was NOT called
        update_entry_mock.assert_not_called()


@pytest.mark.asyncio
async def test_options_flow_only_scan_interval_change(hass: HomeAssistant):
    """Test updating only scan interval without changing credentials."""
    # Create a dummy config entry
    entry = DummyEntry(
        data={"username": "my_user", "password": "my_pass"},
        options={"scan_interval": 60},
    )

    # Mock the hass.config_entries.async_update_entry method
    update_entry_mock = MagicMock()
    hass.config_entries = MagicMock()
    hass.config_entries.async_update_entry = update_entry_mock

    # No need to mock client since credentials aren't changing
    with patch("flowerhub_portal_api_client.AsyncFlowerhubClient") as mock_client_class:
        # Start the options flow
        flow = OptionsFlowHandler(entry)
        flow.hass = hass  # Ensure flow has hass reference
        result = await flow.async_step_init()

        assert result["type"] == "form"
        assert result["step_id"] == "init"

        # Submit same credentials but different scan interval (password left blank)
        result = await flow.async_step_init(
            user_input={
                "username": "my_user",
                "password": "",  # Empty password field
                "scan_interval": 300,
            }
        )

        assert result["type"] == "create_entry"
        assert result["data"] == {"scan_interval": 300}

        # Verify client was not called (credentials didn't change)
        mock_client_class.assert_not_called()

        # Verify async_update_entry was NOT called (credentials unchanged)
        update_entry_mock.assert_not_called()


@pytest.mark.asyncio
async def test_options_flow_change_password_only(hass: HomeAssistant):
    """Test changing only the password while keeping username the same."""
    # Create a dummy config entry
    entry = DummyEntry(
        data={"username": "my_user", "password": "old_pass"},
        options={"scan_interval": 60},
    )

    # Mock the hass.config_entries.async_update_entry method
    update_entry_mock = MagicMock()
    hass.config_entries = MagicMock()
    hass.config_entries.async_update_entry = update_entry_mock

    # Mock the client to simulate successful authentication
    with patch(
        "flowerhub_portal_api_client.AsyncFlowerhubClient"
    ) as mock_client_class, patch("flowerhub.config_flow.async_get_clientsession"):
        mock_client = AsyncMock()
        mock_client.async_login = AsyncMock()
        mock_client.async_readout_sequence = AsyncMock()
        mock_client_class.return_value = mock_client

        # Start the options flow
        flow = OptionsFlowHandler(entry)
        flow.hass = hass  # Ensure flow has hass reference
        result = await flow.async_step_init()

        assert result["type"] == "form"
        assert result["step_id"] == "init"

        # Change password only (username stays same, password field not empty)
        result = await flow.async_step_init(
            user_input={
                "username": "my_user",
                "password": "new_pass",  # New password
                "scan_interval": 60,
            }
        )

        assert result["type"] == "create_entry"
        assert result["data"] == {"scan_interval": 60}

        # Verify new password was validated
        mock_client.async_login.assert_called_once_with("my_user", "new_pass")
        mock_client.async_readout_sequence.assert_called_once()

        # Verify password was updated
        update_entry_mock.assert_called_once()
        call_args = update_entry_mock.call_args
        assert call_args[1]["data"] == {"username": "my_user", "password": "new_pass"}
