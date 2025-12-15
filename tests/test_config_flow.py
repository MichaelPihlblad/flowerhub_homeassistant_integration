import pytest

from homeassistant import data_entry_flow

from homeassistant.core import HomeAssistant

from flowerhub.const import DOMAIN
from flowerhub.config_flow import ConfigFlow


@pytest.mark.asyncio
async def test_config_flow_success(hass: HomeAssistant):
    # Start config flow
    # Some test harnesses provide `hass` as an async generator; ensure we have the instance
    hass_gen = hass
    if hasattr(hass, "__anext__"):
        hass = await hass.__anext__()
    flow = ConfigFlow()
    flow.hass = hass

    result = await flow.async_step_user()
    assert result["type"] == data_entry_flow.FlowResultType.FORM

    # Submit user data, our fake client will accept it
    result2 = await flow.async_step_user({"username": "testuser", "password": "testpass"})
    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"]

    # If we consumed an async generator for hass, finish it to run teardown
    if hasattr(hass_gen, "__anext__"):
        try:
            await hass_gen.__anext__()
        except StopAsyncIteration:
            pass


@pytest.mark.asyncio
async def test_config_flow_cannot_connect(hass: HomeAssistant, monkeypatch):
    # Make the client raise on read
    hass_gen = hass
    if hasattr(hass, "__anext__"):
        hass = await hass.__anext__()
    class BadClient:
        def __init__(self, *args, **kwargs):
            pass

        async def async_readout_sequence(self):
            raise Exception("failed")

    monkeypatch.setitem(__import__("sys").modules, "flowerhub_portal_api_client", type("m", (), {"AsyncFlowerhubClient": BadClient}))

    flow = ConfigFlow()
    flow.hass = hass

    result = await flow.async_step_user()
    assert result["type"] == data_entry_flow.FlowResultType.FORM

    result2 = await flow.async_step_user({"username": "baduser", "password": "badpass"})
    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"]["base"] == "cannot_connect"

    if hasattr(hass_gen, "__anext__"):
        try:
            await hass_gen.__anext__()
        except StopAsyncIteration:
            pass
