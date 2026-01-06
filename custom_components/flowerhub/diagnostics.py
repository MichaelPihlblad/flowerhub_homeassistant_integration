"""Diagnostics support for FlowerHub."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    client = data["client"]

    # Gather diagnostic information
    coordinator_data = coordinator.data if coordinator.data else {}

    # Get connection status information
    connection_status = {
        "status": coordinator_data.get("status"),
        "message": coordinator_data.get("message"),
        "last_updated": coordinator_data.get("last_updated"),
    }

    diagnostics_data = {
        "config_entry": {
            "entry_id": entry.entry_id,
            "version": entry.version,
            "domain": entry.domain,
            "title": entry.title,
            "options": dict(entry.options),
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "last_update_time": coordinator.last_update_time.isoformat()
            if coordinator.last_update_time
            else None,
            "update_interval": str(coordinator.update_interval),
            "last_success_monotonic": getattr(
                coordinator, "_last_success_monotonic", None
            ),
        },
        "connection_status": connection_status,
        "client_info": {
            "asset_id": getattr(client, "asset_id", None),
            "asset_owner_id": getattr(client, "asset_owner_id", None),
            "inverter_name": getattr(client, "inverter_name", None),
            "inverter_manufacturer": getattr(client, "inverter_manufacturer", None),
            "battery_name": getattr(client, "battery_name", None),
            "battery_manufacturer": getattr(client, "battery_manufacturer", None),
        },
        "coordinator_data": coordinator_data,
    }

    return diagnostics_data
