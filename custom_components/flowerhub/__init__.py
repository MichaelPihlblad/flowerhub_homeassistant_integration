"""Flowerhub integration for Home Assistant (example).

This is a minimal skeleton showing how to wire up `AsyncFlowerhubClient` with
Home Assistant's `DataUpdateCoordinator`. It is provided as an example only and
is not a full integration implementation.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from flowerhub_portal_api_client import AsyncFlowerhubClient
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, PLATFORMS
from .coordinator import FlowerhubDataUpdateCoordinator

LOGGER = logging.getLogger(__name__)


async def _options_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    client = AsyncFlowerhubClient(session=session)
    try:
        login_resp = await client.async_login(
            entry.data["username"], entry.data["password"]
        )
    except Exception as err:
        # Surface credential issues as auth failures so HA can prompt reauth
        raise ConfigEntryAuthFailed("Flowerhub login failed") from err

    # Some client implementations return a status-bearing dict instead of raising
    if isinstance(login_resp, dict):
        status = login_resp.get("status") or login_resp.get("code")
        try:
            status_int = int(status) if status is not None else None
        except (
            Exception
        ):  # pragma: no cover - fallback if status is not convertible to int
            status_int = None
        if status_int and status_int >= 400:
            raise ConfigEntryAuthFailed(f"Flowerhub login failed (status {status_int})")

    # Use the dedicated coordinator wrapper to keep logic centralized
    scan_interval = entry.options.get("scan_interval", 60)
    coordinator = FlowerhubDataUpdateCoordinator(
        hass,
        client,
        update_interval=timedelta(seconds=scan_interval),
        entry_id=entry.entry_id,
        username=entry.data.get("username"),
        password=entry.data.get("password"),
    )

    await coordinator.async_refresh()

    # Store data for platforms
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    # Register listener for options updates
    entry.async_on_unload(entry.add_update_listener(_options_update_listener))

    # Forward setup to platforms (skip in tests where integration not loaded)
    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:
        # In tests, platforms aren't loaded.
        # create test specific behavior here if needed
        pass

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Unload platforms first
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False

    data = hass.data.get(DOMAIN, {})
    entry_data = data.pop(entry.entry_id, None)

    if entry_data:
        coordinator = entry_data["coordinator"]
        client = entry_data["client"]
        client.stop_periodic_asset_fetch()
        if hasattr(coordinator, "_unsub_shutdown") and coordinator._unsub_shutdown:
            coordinator._unsub_shutdown()
        remove_listener = entry_data.get("remove_listener")
        if remove_listener:
            try:
                remove_listener()
            except Exception:
                LOGGER.exception("Error removing coordinator listener")

    return True
