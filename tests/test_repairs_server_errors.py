from datetime import timedelta

import pytest
from flowerhub.const import DOMAIN
from flowerhub.coordinator import FlowerhubDataUpdateCoordinator
from homeassistant.helpers.issue_registry import async_get as ir_async_get


class FlowerhubStatus:
    def __init__(self, status: str = "ok"):
        self.status = status
        from datetime import datetime

        self.updated_at = datetime.now()
        self.message = "ok"


class ServerFlakyClient:
    def __init__(self, fail_count_before_success: int = 2):
        self.asset_info: dict[str, dict] = {"inverter": {}, "battery": {}}
        self.flowerhub_status = FlowerhubStatus("state_1")
        self._failures_left = fail_count_before_success

    async def async_fetch_asset(self):
        if self._failures_left > 0:
            self._failures_left -= 1

            class Err(Exception):
                def __init__(self):
                    super().__init__("server error")
                    self.status = 500

            raise Err()
        # Success path
        self.flowerhub_status = FlowerhubStatus("state_2")
        return {
            "status_code": 200,
            "asset_info": self.asset_info,
            "flowerhub_status": self.flowerhub_status,
            "error": None,
        }

    async def async_login(self, username, password):
        return None

    async def async_readout_sequence(self):
        return {
            "asset_owner_id": 1,
            "asset_id": 2,
            "asset_resp": {
                "status_code": 200,
                "asset_info": self.asset_info,
                "flowerhub_status": self.flowerhub_status,
                "error": None,
            },
            "with_asset_resp": {"status_code": 200, "asset_id": 2, "error": None},
        }


@pytest.mark.asyncio
async def test_repairs_issue_created_and_cleared(hass):
    hass_gen = hass
    if hasattr(hass, "__anext__"):
        hass = await hass.__anext__()

    client = ServerFlakyClient(fail_count_before_success=2)
    coord = FlowerhubDataUpdateCoordinator(
        hass,
        client,
        update_interval=timedelta(seconds=5),
        entry_id="entry_1",
        username="u",
        password="p",
    )
    coord._first_update = False
    coord._repair_threshold = 2

    # First failure - no issue yet
    with pytest.raises(Exception):
        await coord._async_update()

    ir = ir_async_get(hass)
    issue_id = "server_update_failures_entry_1"
    assert ir.async_get_issue(DOMAIN, issue_id) is None

    # Second failure - issue raised
    with pytest.raises(Exception):
        await coord._async_update()

    assert ir.async_get_issue(DOMAIN, issue_id) is not None

    # Success clears issue
    await coord._async_update()
    assert ir.async_get_issue(DOMAIN, issue_id) is None

    if hasattr(hass_gen, "__anext__"):
        try:
            await hass_gen.__anext__()
        except StopAsyncIteration:
            pass
