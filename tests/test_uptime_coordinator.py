"""Tests for uptime data fetching in coordinator."""

from time import monotonic
from unittest.mock import AsyncMock, MagicMock

import pytest
from flowerhub.coordinator import FlowerhubDataUpdateCoordinator


@pytest.fixture
def mock_client():
    """Create a mock AsyncFlowerhubClient with uptime support."""
    client = MagicMock()
    client.asset_id = 75
    client.asset_owner_id = 32
    client.flowerhub_status = MagicMock(
        status="Online", message="ok", updated_at=MagicMock()
    )
    client.asset_info = {
        "inverter": {"name": "SUN2000 M1", "powerCapacity": 10},
        "battery": {"name": "LUNA2000 S0", "energyCapacity": 15},
        "fuseSize": 16,
        "isInstalled": True,
    }

    # Mock async_readout_sequence to return uptime data
    client.async_readout_sequence = AsyncMock(
        return_value={
            "asset_owner_id": 32,
            "asset_id": 75,
            "with_asset_resp": {
                "status_code": 200,
                "asset_id": 75,
                "error": None,
            },
            "asset_resp": {
                "status_code": 200,
                "asset_info": client.asset_info,
                "flowerhub_status": client.flowerhub_status,
                "error": None,
            },
            "uptime_pie_resp": {
                "status_code": 200,
                "uptime": 2592000.0,
                "downtime": 3600.0,
                "noData": 0.0,
                "uptime_ratio_total": 99.86,
                "uptime_ratio_actual": 99.86,
                "json": {},
                "text": "",
                "error": None,
            },
        }
    )

    # Mock async_fetch_asset for subsequent updates
    client.async_fetch_asset = AsyncMock(
        return_value={
            "status_code": 200,
            "asset_info": client.asset_info,
            "flowerhub_status": client.flowerhub_status,
            "error": None,
        }
    )

    # Mock async_fetch_uptime_pie for periodic updates
    client.async_fetch_uptime_pie = AsyncMock(
        return_value={
            "status_code": 200,
            "uptime": 2595600.0,  # Updated value
            "downtime": 3700.0,
            "noData": 0.0,
            "uptime_ratio_total": 99.86,
            "uptime_ratio_actual": 99.86,
            "json": {},
            "text": "",
            "error": None,
        }
    )

    client.async_login = AsyncMock()

    return client


@pytest.mark.asyncio
async def test_uptime_data_cached_from_initial_readout(hass, mock_client):
    """Test that uptime data is cached from initial readout."""
    from datetime import timedelta

    coordinator = FlowerhubDataUpdateCoordinator(
        hass,
        mock_client,
        update_interval=timedelta(seconds=60),
        entry_id="test_entry",
        username="test_user",
        password="test_pass",
    )

    # Run first update (should call async_readout_sequence)
    await coordinator.async_refresh()

    # Verify uptime data was cached
    assert coordinator._uptime_data is not None
    assert coordinator._uptime_data["uptime"] == 2592000.0
    assert coordinator._uptime_data["downtime"] == 3600.0
    assert coordinator._uptime_data["no_data"] == 0.0
    assert coordinator._uptime_data["uptime_ratio_actual"] == 99.86

    # Verify data is available in coordinator.data
    assert coordinator.data["uptime"] == 2592000.0
    assert coordinator.data["downtime"] == 3600.0
    assert coordinator.data["no_data"] == 0.0
    assert coordinator.data["uptime_ratio_total"] == 99.86
    assert coordinator.data["uptime_ratio_actual"] == 99.86
    assert coordinator.data["uptime_last_updated"]
    assert coordinator.data["uptime_next_update"]


@pytest.mark.asyncio
async def test_uptime_data_fetched_on_every_update(hass, mock_client):
    """Test that uptime data is fetched on every coordinator update."""
    from datetime import timedelta

    coordinator = FlowerhubDataUpdateCoordinator(
        hass,
        mock_client,
        update_interval=timedelta(seconds=60),
        entry_id="test_entry",
        username="test_user",
        password="test_pass",
    )

    # Run first update
    await coordinator.async_refresh()

    # Reset mock to track new calls
    mock_client.async_fetch_uptime_pie.reset_mock()

    # Run second update (should fetch uptime again)
    await coordinator.async_refresh()

    # async_fetch_uptime_pie should have been called on every update
    mock_client.async_fetch_uptime_pie.assert_called_once()


@pytest.mark.asyncio
async def test_uptime_fetch_handles_errors_gracefully(hass, mock_client):
    """Test that uptime fetch errors don't break coordinator updates."""
    from datetime import timedelta

    # Make async_fetch_uptime_pie raise an exception
    mock_client.async_fetch_uptime_pie = AsyncMock(
        side_effect=Exception("Uptime fetch failed")
    )

    coordinator = FlowerhubDataUpdateCoordinator(
        hass,
        mock_client,
        update_interval=timedelta(seconds=60),
        entry_id="test_entry",
        username="test_user",
        password="test_pass",
    )

    # Simulate time passing (more than 1 hour)
    coordinator._last_uptime_fetch_monotonic = monotonic() - 3601.0

    # This should not raise an exception
    await coordinator.async_refresh()

    # Main data should still be available
    assert coordinator.data["status"] is not None


@pytest.mark.asyncio
async def test_uptime_data_missing_from_readout(hass, mock_client):
    """Test handling when uptime_pie_resp is missing from readout."""
    from datetime import timedelta

    # Remove uptime_pie_resp from readout response
    mock_client.async_readout_sequence = AsyncMock(
        return_value={
            "asset_owner_id": 32,
            "asset_id": 75,
            "with_asset_resp": {
                "status_code": 200,
                "asset_id": 75,
                "error": None,
            },
            "asset_resp": {
                "status_code": 200,
                "asset_info": mock_client.asset_info,
                "flowerhub_status": mock_client.flowerhub_status,
                "error": None,
            },
            "uptime_pie_resp": None,  # No uptime data
        }
    )

    coordinator = FlowerhubDataUpdateCoordinator(
        hass,
        mock_client,
        update_interval=timedelta(seconds=60),
        entry_id="test_entry",
        username="test_user",
        password="test_pass",
    )

    # Run first update
    await coordinator.async_refresh()

    # Uptime data should be None
    assert coordinator._uptime_data is None
    assert coordinator.data["uptime"] is None
    assert coordinator.data["downtime"] is None
    assert coordinator.data["no_data"] is None
    assert coordinator.data["uptime_ratio_total"] is None
    assert coordinator.data["uptime_ratio_actual"] is None


@pytest.mark.asyncio
async def test_uptime_fetch_skipped_without_asset_id(hass, mock_client):
    """Test that uptime fetch is skipped when asset_id is not available."""
    from datetime import timedelta

    # Remove asset_id
    mock_client.asset_id = None

    coordinator = FlowerhubDataUpdateCoordinator(
        hass,
        mock_client,
        update_interval=timedelta(seconds=60),
        entry_id="test_entry",
        username="test_user",
        password="test_pass",
    )

    # Reset mock
    mock_client.async_fetch_uptime_pie.reset_mock()

    # This should not fail, just skip the uptime fetch
    await coordinator._maybe_fetch_uptime_data()

    # async_fetch_uptime_pie should NOT have been called
    mock_client.async_fetch_uptime_pie.assert_not_called()


@pytest.mark.asyncio
async def test_uptime_fetch_called_with_correct_parameters(hass, mock_client):
    """Test that uptime fetch is called with correct parameters on each update."""
    from datetime import timedelta

    coordinator = FlowerhubDataUpdateCoordinator(
        hass,
        mock_client,
        update_interval=timedelta(seconds=60),
        entry_id="test_entry",
        username="test_user",
        password="test_pass",
    )

    # Run first update
    await coordinator.async_refresh()

    # Reset mock to track new calls
    mock_client.async_fetch_uptime_pie.reset_mock()

    # Run second update
    await coordinator.async_refresh()

    # Verify async_fetch_uptime_pie was called with correct parameters
    # (period is omitted, client library uses local datetime.now() by default)
    mock_client.async_fetch_uptime_pie.assert_called_once_with(
        75,  # asset_id
        raise_on_error=False,
        timeout_total=30.0,
    )
