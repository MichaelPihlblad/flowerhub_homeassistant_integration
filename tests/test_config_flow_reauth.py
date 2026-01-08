"""Reauth flow tests for Flowerhub config flow."""

from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from flowerhub.config_flow import ConfigFlow
from flowerhub.const import DEFAULT_NAME, DOMAIN
from homeassistant import data_entry_flow
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.mark.asyncio
async def test_reauth_success_updates_entry_and_aborts(hass: HomeAssistant):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"username": "old_user", "password": "old_pass"},
        options={"scan_interval": 60},
    )
    entry.add_to_hass(hass)

    update_entry_mock = MagicMock()
    with patch.object(
        hass.config_entries, "async_update_entry", update_entry_mock
    ), patch.object(hass.config_entries, "async_get_entry", return_value=entry), patch(
        "flowerhub.config_flow.async_get_clientsession", return_value=None
    ), patch(
        "flowerhub_portal_api_client.AsyncFlowerhubClient"
    ) as mock_client_cls:
        mock_client = MagicMock()
        mock_client.async_login = AsyncMock()
        mock_client.async_readout_sequence = AsyncMock()
        mock_client_cls.return_value = mock_client

        flow = ConfigFlow()
        flow.hass = hass
        setattr(
            flow,
            "_flow_context",
            {
                "entry_id": entry.entry_id,
            },
        )

        form = cast(dict[str, Any], await flow.async_step_reauth())
        assert form["type"] == data_entry_flow.FlowResultType.FORM
        assert form["step_id"] == "reauth_confirm"

        # Ensure the existing entry is available for reauth confirmation
        flow._reauth_entry = entry  # type: ignore[attr-defined]

        result = cast(
            dict[str, Any],
            await flow.async_step_reauth_confirm(
                {"username": "new_user", "password": "new_pass"}
            ),
        )

        assert result["type"] == data_entry_flow.FlowResultType.ABORT
        assert result["reason"] == "reauth_successful"
        mock_client.async_login.assert_awaited_once_with("new_user", "new_pass")
        mock_client.async_readout_sequence.assert_awaited_once()
        update_entry_mock.assert_called_once()
        args, kwargs = update_entry_mock.call_args
        assert args[0] == entry
        expected_data = {"username": "new_user", "password": "new_pass"}
        assert kwargs["data"] == expected_data


@pytest.mark.asyncio
async def test_reauth_invalid_credentials_sets_error(hass: HomeAssistant):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"username": "old_user", "password": "old_pass"},
        options={"scan_interval": 60},
    )
    entry.add_to_hass(hass)

    update_entry_mock = MagicMock()
    with patch.object(
        hass.config_entries, "async_update_entry", update_entry_mock
    ), patch.object(hass.config_entries, "async_get_entry", return_value=entry), patch(
        "flowerhub.config_flow.async_get_clientsession", return_value=None
    ), patch(
        "flowerhub_portal_api_client.AsyncFlowerhubClient"
    ) as mock_client_cls:
        mock_client = MagicMock()
        mock_client.async_login = AsyncMock(side_effect=Exception("Invalid creds"))
        mock_client.async_readout_sequence = AsyncMock()
        mock_client_cls.return_value = mock_client

        flow = ConfigFlow()
        flow.hass = hass
        setattr(
            flow,
            "_flow_context",
            {
                "entry_id": entry.entry_id,
            },
        )

        form = cast(dict[str, Any], await flow.async_step_reauth())
        assert form["type"] == data_entry_flow.FlowResultType.FORM

        flow._reauth_entry = entry  # type: ignore[attr-defined]

        result = cast(
            dict[str, Any],
            await flow.async_step_reauth_confirm(
                {"username": "bad_user", "password": "bad_pass"}
            ),
        )

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}
        update_entry_mock.assert_not_called()


@pytest.mark.asyncio
async def test_reauth_missing_entry_creates_new_entry(hass: HomeAssistant):
    update_entry_mock = MagicMock()
    with patch.object(
        hass.config_entries, "async_update_entry", update_entry_mock
    ), patch.object(hass.config_entries, "async_get_entry", return_value=None), patch(
        "flowerhub.config_flow.async_get_clientsession", return_value=None
    ), patch(
        "flowerhub_portal_api_client.AsyncFlowerhubClient"
    ) as mock_client_cls:
        mock_client = MagicMock()
        mock_client.async_login = AsyncMock()
        mock_client.async_readout_sequence = AsyncMock()
        mock_client_cls.return_value = mock_client

        flow = ConfigFlow()
        flow.hass = hass
        setattr(
            flow,
            "_flow_context",
            {
                "entry_id": "missing_entry_id",
            },
        )

        form = cast(dict[str, Any], await flow.async_step_reauth())
        assert form["type"] == data_entry_flow.FlowResultType.FORM

        result = cast(
            dict[str, Any],
            await flow.async_step_reauth_confirm(
                {"username": "new_user", "password": "new_pass"}
            ),
        )

        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["title"] == DEFAULT_NAME
        assert result["data"] == {"username": "new_user", "password": "new_pass"}
        mock_client.async_login.assert_awaited_once_with("new_user", "new_pass")
        mock_client.async_readout_sequence.assert_awaited_once()
        update_entry_mock.assert_not_called()
