import asyncio
import pytest

from homeassistant.core import HomeAssistant

from pytest_homeassistant_custom_component.common import MockConfigEntry

from flowerhub.const import DOMAIN
from flowerhub import async_setup_entry


@pytest.mark.asyncio
async def test_entity_state_and_coordinator_refresh(hass: HomeAssistant):
    # Ensure hass is the instance if provided as an async generator
    hass_gen = hass
    if hasattr(hass, "__anext__"):
        hass = await hass.__anext__()

    # Create a mock config entry and set up the integration directly
    entry = MockConfigEntry(domain=DOMAIN, data={"username": "testuser", "password": "testpass"})
    await async_setup_entry(hass, entry)
    await hass.async_block_till_done()

    # Ensure entity exists and initial state from fake client
    state = hass.states.get("sensor.flowerhub_status")
    assert state is not None
    assert state.state.startswith("state_")

    # Trigger coordinator refresh and wait
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    state2 = hass.states.get("sensor.flowerhub_status")
    assert state2.state != state.state

    # Clean up by unloading the entry so coordinator timers are stopped
    from flowerhub import async_unload_entry

    assert await async_unload_entry(hass, entry)
    await hass.async_block_till_done()
    # Stop hass to ensure any background threads/timers are cleaned up
    await hass.async_stop()
    await hass.async_block_till_done()

    if hasattr(hass_gen, "__anext__"):
        try:
            await hass_gen.__anext__()
        except StopAsyncIteration:
            pass
