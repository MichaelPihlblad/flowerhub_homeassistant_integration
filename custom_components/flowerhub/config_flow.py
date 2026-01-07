"""Config flow for Flowerhub integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_NAME, DOMAIN, SCAN_INTERVAL_MAX, SCAN_INTERVAL_MIN

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

    async def async_step_reauth(self, entry_data: dict[str, Any] | None = None):
        """Handle reauthentication when credentials are no longer valid."""
        # Locate the existing entry from context
        entry_id = self.context.get("entry_id")
        self._reauth_entry = (
            self.hass.config_entries.async_get_entry(entry_id) if entry_id else None
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None):
        """Confirm new credentials for reauthentication."""
        errors: dict[str, str] = {}
        data_schema = vol.Schema(
            {
                vol.Required("username"): str,
                vol.Required("password"): str,
            }
        )

        if user_input is not None:
            username = user_input["username"]
            password = user_input["password"]
            try:
                from flowerhub_portal_api_client import AsyncFlowerhubClient

                session = async_get_clientsession(self.hass)
                client = AsyncFlowerhubClient(session=session)
                await client.async_login(username, password)
                # Prime the client to ensure credentials are valid
                await client.async_readout_sequence()
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                # Update the existing entry with new credentials
                if getattr(self, "_reauth_entry", None):
                    self.hass.config_entries.async_update_entry(
                        self._reauth_entry,
                        data={"username": username, "password": password},
                    )
                    return self.async_abort(reason="reauth_successful")
                # Fallback: create a new entry if original could not be found
                return self.async_create_entry(
                    title=DEFAULT_NAME,
                    description="Login using Flowerhub portal account credentials",
                    data={"username": username, "password": password},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=data_schema,
            errors=errors,
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        # Base class exposes a read-only `config_entry` property
        # backed by `_config_entry`
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        # Get current credentials from config entry
        current_username = self._config_entry.data.get("username", "")
        current_password = self._config_entry.data.get("password", "")
        current_scan_interval = self._config_entry.options.get("scan_interval", 60)

        options_schema = vol.Schema(
            {
                vol.Required("username", default=current_username): str,
                vol.Optional("password"): str,
                vol.Required("scan_interval", default=current_scan_interval): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=SCAN_INTERVAL_MIN, max=SCAN_INTERVAL_MAX),
                ),
            }
        )

        if user_input is not None:
            username = user_input["username"]
            password = user_input.get("password", "")
            scan_interval = user_input["scan_interval"]

            # Check if credentials need validation:
            # - Username changed, OR
            # - Password field is not empty AND different from current password
            credentials_changed = username != current_username or (
                password and password != current_password
            )

            if credentials_changed:
                try:
                    from flowerhub_portal_api_client import AsyncFlowerhubClient

                    session = async_get_clientsession(self.hass)
                    client = AsyncFlowerhubClient(session=session)
                    # Use new password if provided, otherwise keep current password
                    password_to_validate = password if password else current_password
                    await client.async_login(username, password_to_validate)
                    await client.async_readout_sequence()
                except Exception:
                    errors["base"] = "cannot_connect"
                else:
                    # Update config entry data with new credentials
                    # Use new password if provided, otherwise keep current password
                    password_to_save = password if password else current_password
                    self.hass.config_entries.async_update_entry(
                        self._config_entry,
                        data={"username": username, "password": password_to_save},
                    )
                    # Save options (scan_interval)
                    return self.async_create_entry(
                        title="", data={"scan_interval": scan_interval}
                    )
            else:
                # Only scan_interval changed, save options
                return self.async_create_entry(
                    title="", data={"scan_interval": scan_interval}
                )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            errors=errors,
            description_placeholders={
                "min": SCAN_INTERVAL_MIN,
                "max": SCAN_INTERVAL_MAX,
            },
        )


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
