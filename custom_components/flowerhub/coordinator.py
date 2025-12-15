from __future__ import annotations

import logging
from typing import Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

LOGGER = logging.getLogger(__name__)


class FlowerhubDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, client, update_interval):
        super().__init__(
            hass,
            LOGGER,
            name="flowerhub",
            update_method=self._async_update,
            update_interval=update_interval,
        )
        self.client = client

    async def _async_update(self) -> dict[str, Any]:
        await self.client.async_readout_sequence()
        status = self.client.flowerhub_status
        asset_info = self.client.asset_info
        return {
            "status": status.status if status else None,
            "message": status.message if status else None,
            "last_updated": status.updated_at.isoformat() if status and status.updated_at else None,
            "inverter_name": asset_info.get("inverter", {}).get("name") if asset_info else None,
            "battery_name": asset_info.get("battery", {}).get("name") if asset_info else None,
            "power_capacity": asset_info.get("inverter", {}).get("powerCapacity") if asset_info else None,
            "energy_capacity": asset_info.get("battery", {}).get("energyCapacity") if asset_info else None,
            "fuse_size": asset_info.get("fuseSize") if asset_info else None,
            "is_installed": asset_info.get("isInstalled") if asset_info else None,
        }
