from typing import Any

import pytest
from flowerhub.config_flow import (
    OptionsFlowHandler,
    async_get_config_entry_diagnostics,
    async_get_options_flow,
)
from flowerhub.const import DOMAIN
from homeassistant import data_entry_flow
from homeassistant.core import HomeAssistant


@pytest.mark.asyncio
async def test_options_flow_create_entry(hass: HomeAssistant):
    class DummyEntry:
        def __init__(self):
            self.entry_id = "123"
            self.options = {}
            self.data = {"username": "test_user", "password": "test_pass"}

    entry = DummyEntry()
    flow = OptionsFlowHandler(entry)
    flow.hass = hass  # Ensure flow has hass reference

    # Show form
    form = await flow.async_step_init()
    assert form["type"] == data_entry_flow.FlowResultType.FORM

    # Submit options (no credentials changed, same values)
    result = await flow.async_step_init(
        {
            "username": "test_user",
            "password": "test_pass",
            "scan_interval": 45,
        }
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"]["scan_interval"] == 45

    # Helper returns handler
    flow2 = await async_get_options_flow(entry)
    assert isinstance(flow2, OptionsFlowHandler)


@pytest.mark.asyncio
async def test_config_entry_diagnostics_error_path(hass: HomeAssistant):
    # Prepare fake client without the expected readout structure
    class ClientWithMinimalAPI:
        asset_owner_id = "owner"
        asset_id = "asset"
        asset_info: dict[str, Any] = {}
        flowerhub_status = None

        async def async_readout_sequence(self):
            return None  # Will trigger exception path in diagnostics

    class DummyEntry:
        def __init__(self):
            self.entry_id = "entry_1"

    entry = DummyEntry()
    # Some test harnesses provide `hass` as an async generator.
    # Ensure we have the actual `HomeAssistant` instance.
    hass_gen = hass
    if hasattr(hass, "__anext__"):
        hass = await hass.__anext__()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": ClientWithMinimalAPI()
    }

    result = await async_get_config_entry_diagnostics(hass, entry)
    assert "diagnostic_error" in result

    if hasattr(hass_gen, "__anext__"):
        try:
            await hass_gen.__anext__()
        except StopAsyncIteration:
            pass
