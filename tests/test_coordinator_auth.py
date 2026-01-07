from datetime import timedelta

import pytest
from flowerhub.coordinator import FlowerhubDataUpdateCoordinator
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed


class DummyAuthError(Exception):
    def __init__(self, status=None, message="auth"):
        super().__init__(message)
        self.status = status
        self.status_code = status
        self.code = status


class DummyServerError(Exception):
    def __init__(self, status=None, message="server"):
        super().__init__(message)
        self.status = status
        self.status_code = status
        self.code = status


class AuthFailingClient:
    def __init__(self):
        self.asset_info = {}
        self.flowerhub_status = None

    async def async_fetch_asset(self):
        raise DummyAuthError(status=401)

    async def async_login(self, username, password):
        raise DummyAuthError(status=401)

    async def async_readout_sequence(self):
        return {}


class ServerFailingClient:
    def __init__(self):
        self.asset_info = {}
        self.flowerhub_status = None

    async def async_fetch_asset(self):
        raise DummyServerError(status=500)

    async def async_login(self, username, password):
        return None

    async def async_readout_sequence(self):
        return {}


@pytest.mark.asyncio
async def test_is_auth_error_status_and_text(hass):
    hass_gen = hass
    if hasattr(hass, "__anext__"):
        hass = await hass.__anext__()

    coord = FlowerhubDataUpdateCoordinator(
        hass,
        AuthFailingClient(),
        update_interval=timedelta(seconds=30),
        username="u",
        password="p",
    )

    assert coord._is_auth_error(DummyAuthError(status=401))
    assert coord._is_auth_error(DummyAuthError(status=403))
    assert not coord._is_auth_error(DummyServerError(status=500))
    assert coord._is_auth_error(DummyAuthError(message="unauthorized"))

    if hasattr(hass_gen, "__anext__"):
        try:
            await hass_gen.__anext__()
        except StopAsyncIteration:
            pass


@pytest.mark.asyncio
async def test_auth_error_triggers_config_entry_auth_failed(hass):
    hass_gen = hass
    if hasattr(hass, "__anext__"):
        hass = await hass.__anext__()

    client = AuthFailingClient()
    coord = FlowerhubDataUpdateCoordinator(
        hass,
        client,
        update_interval=timedelta(seconds=30),
        username="u",
        password="p",
    )
    coord._first_update = False

    with pytest.raises(ConfigEntryAuthFailed):
        await coord._async_update()

    if hasattr(hass_gen, "__anext__"):
        try:
            await hass_gen.__anext__()
        except StopAsyncIteration:
            pass


@pytest.mark.asyncio
async def test_server_error_does_not_trigger_reauth(hass):
    hass_gen = hass
    if hasattr(hass, "__anext__"):
        hass = await hass.__anext__()

    client = ServerFailingClient()
    coord = FlowerhubDataUpdateCoordinator(
        hass,
        client,
        update_interval=timedelta(seconds=30),
        username="u",
        password="p",
    )
    coord._first_update = False

    with pytest.raises(UpdateFailed):
        await coord._async_update()

    if hasattr(hass_gen, "__anext__"):
        try:
            await hass_gen.__anext__()
        except StopAsyncIteration:
            pass
