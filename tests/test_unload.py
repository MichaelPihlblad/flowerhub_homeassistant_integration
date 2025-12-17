import pytest
from flowerhub import async_setup_entry, async_unload_entry
from flowerhub.const import DOMAIN
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.mark.asyncio
async def test_unload_stops_periodic_tasks(hass: HomeAssistant):
    hass_gen = hass
    if hasattr(hass, "__anext__"):
        hass = await hass.__anext__()

    entry = MockConfigEntry(
        domain=DOMAIN, data={"username": "testuser", "password": "testpass"}
    )
    await async_setup_entry(hass, entry)
    await hass.async_block_till_done()

    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]

    # Stop should not have been called yet
    assert getattr(client, "stopped", False) is False

    # Unload entry
    assert await async_unload_entry(hass, entry)
    await hass.async_block_till_done()

    # The fake client stop_periodic_asset_fetch should have been called
    assert getattr(client, "stopped", False) is True

    # Entry data removed
    assert entry.entry_id not in hass.data.get(DOMAIN, {})

    if hasattr(hass_gen, "__anext__"):
        try:
            await hass_gen.__anext__()
        except StopAsyncIteration:
            pass
