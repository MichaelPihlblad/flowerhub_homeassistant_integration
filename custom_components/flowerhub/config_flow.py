"""Config flow for Flowerhub integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_NAME, DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("username"): str,
        vol.Required("password"): str,
    }
)

LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors = {}
        if user_input is not None:
            username = user_input["username"]
            password = user_input["password"]
            # Validate by instantiating the client and trying to read
            try:
                from flowerhub_portal_api_client import AsyncFlowerhubClient

                session = async_get_clientsession(self.hass)
                client = AsyncFlowerhubClient(session=session)
                await client.async_login(username, password)
                await client.async_readout_sequence()
            except ImportError as err:
                LOGGER.error("Flowerhub client library not found: %s", err)
                errors["base"] = "missing_library"
            except Exception as err:
                # Do not log credentials; keep a concise trace for diagnostics
                LOGGER.exception("Authentication failed during validation: %s", err)
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=DEFAULT_NAME,
                    description="Login using Flowerhub portal account credentials",
                    data={"username": username, "password": password},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "portal_link": "https://portal.flowerhub.se",
            },
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        options_schema = vol.Schema({"scan_interval": int})
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init", data_schema=options_schema)


async def async_get_options_flow(
    config_entry: config_entries.ConfigEntry,
) -> OptionsFlowHandler:
    return OptionsFlowHandler(config_entry)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: config_entries.ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    from .const import DOMAIN

    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]

    try:
        readout = await client.async_readout_sequence()
        # readout["asset_resp"] is now AssetFetchResult TypedDict
        asset_resp = readout.get("asset_resp") if readout else None
        return {
            "asset_owner_information": readout.get("with_asset_resp"),
            "hardware_asset_details": asset_resp.get("asset_info")
            if asset_resp
            else None,
            "client_connection_state": {
                "asset_owner_id": client.asset_owner_id,
                "asset_id": client.asset_id,
                "asset_info": client.asset_info,
                "flowerhub_status": client.flowerhub_status.__dict__
                if client.flowerhub_status
                else None,
            },
        }
    except Exception as e:
        return {"diagnostic_error": str(e)}
