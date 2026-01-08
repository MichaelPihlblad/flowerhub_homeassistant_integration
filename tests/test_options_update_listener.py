"""Tests for options update listener."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from flowerhub import _options_update_listener


@pytest.mark.asyncio
async def test_options_update_listener_triggers_reload():
    hass = MagicMock()
    hass.config_entries = MagicMock()
    hass.config_entries.async_reload = AsyncMock()

    entry = MagicMock()
    entry.entry_id = "entry1"

    await _options_update_listener(hass, entry)

    hass.config_entries.async_reload.assert_awaited_once_with("entry1")
