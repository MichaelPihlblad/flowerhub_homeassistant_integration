"""Tests for uptime sensors and uptime data fetching."""

import pytest
from flowerhub.sensor import (
    FlowerhubMonthlyDowntimeSensor,
    FlowerhubMonthlyUptimeRatioSensor,
    FlowerhubMonthlyUptimeRatioTotalSensor,
    FlowerhubMonthlyUptimeSensor,
)


class FakeCoordinator:
    def __init__(self):
        self.last_update_success = True
        self.data = {
            "status": "state_1",
            "message": "ok",
            "uptime": 2592000.0,  # 30 days in seconds
            "downtime": 3600.0,  # 1 hour in seconds
            "no_data": 0.0,
            "uptime_ratio_total": 99.86,
            "uptime_ratio_actual": 99.86,  # 99.86% uptime
            "uptime_last_updated": "2026-01-10T00:00:00+00:00",
            "uptime_next_update": "2026-01-10T01:00:00+00:00",
        }
        self.client = FakeClient()


class FakeClient:
    def __init__(self):
        self.asset_id = 75
        self.asset_owner_id = 32


class FakeEntry:
    def __init__(self, entry_id: str = "test_entry"):
        self.entry_id = entry_id


@pytest.mark.parametrize(
    "sensor_cls, expected_value, expected_unit",
    [
        (FlowerhubMonthlyUptimeRatioSensor, 99.86, "%"),
        (FlowerhubMonthlyUptimeRatioTotalSensor, 99.86, "%"),
        (FlowerhubMonthlyUptimeSensor, 2592000.0, "s"),
        (FlowerhubMonthlyDowntimeSensor, 3600.0, "s"),
    ],
)
def test_uptime_sensor_values(sensor_cls, expected_value, expected_unit):
    """Test that uptime sensors return correct values from coordinator data."""
    coord = FakeCoordinator()
    entry = FakeEntry()
    sensor = sensor_cls(coord, entry)

    # Check sensor is available
    assert sensor.available is True

    # Check native value
    assert sensor.native_value == expected_value

    # Check unit of measurement
    assert sensor.entity_description.native_unit_of_measurement == expected_unit


def test_uptime_ratio_sensor_attributes():
    """Test uptime ratio sensor specific attributes."""
    coord = FakeCoordinator()
    entry = FakeEntry()
    sensor = FlowerhubMonthlyUptimeRatioSensor(coord, entry)

    # Should be a main sensor (not diagnostic)
    assert sensor.entity_description.entity_category is None

    # Should have power factor device class
    from homeassistant.components.sensor import SensorDeviceClass

    assert sensor.entity_description.device_class == SensorDeviceClass.POWER_FACTOR

    # Should have 1 decimal precision
    assert sensor.entity_description.suggested_display_precision == 1

    # Attributes should include uptime/downtime/no_data
    attrs = sensor.extra_state_attributes
    assert attrs["uptime"] == 2592000.0
    assert attrs["downtime"] == 3600.0
    assert attrs["no_data"] == 0.0
    assert attrs["last_updated"] == "2026-01-10T00:00:00+00:00"
    assert attrs["next_update"] == "2026-01-10T01:00:00+00:00"


def test_uptime_ratio_availability_by_staleness():
    from datetime import timedelta
    from time import monotonic

    coord = FakeCoordinator()
    coord.update_interval = timedelta(seconds=60)  # 1 minute polling
    entry = FakeEntry()
    sensor = FlowerhubMonthlyUptimeRatioSensor(coord, entry)

    # Before any uptime fetch timestamp is set, fall back to coordinator success
    assert sensor.available is True

    # Simulate recent uptime fetch (< 3 * 60 seconds = 3 minutes)
    setattr(coord, "_last_uptime_fetch_monotonic", monotonic() - 120)
    assert sensor.available is True

    # Simulate stale uptime fetch (> 3 * 60 seconds = 3 minutes)
    setattr(coord, "_last_uptime_fetch_monotonic", monotonic() - (3 * 60 + 10))
    assert sensor.available is False


def test_uptime_duration_sensors_are_diagnostic():
    """Test that uptime and downtime duration sensors are marked as diagnostic."""
    from homeassistant.components.sensor import SensorDeviceClass
    from homeassistant.const import EntityCategory

    coord = FakeCoordinator()
    entry = FakeEntry()

    # Test uptime sensor
    uptime_sensor = FlowerhubMonthlyUptimeSensor(coord, entry)
    assert uptime_sensor.entity_description.entity_category == EntityCategory.DIAGNOSTIC
    assert uptime_sensor.entity_description.device_class == SensorDeviceClass.DURATION

    # Test downtime sensor
    downtime_sensor = FlowerhubMonthlyDowntimeSensor(coord, entry)
    assert (
        downtime_sensor.entity_description.entity_category == EntityCategory.DIAGNOSTIC
    )
    assert downtime_sensor.entity_description.device_class == SensorDeviceClass.DURATION


def test_uptime_sensors_handle_none_values():
    """Test that uptime sensors handle None values gracefully."""
    coord = FakeCoordinator()
    coord.data = {
        "status": "state_1",
        "message": "ok",
        "uptime": None,
        "downtime": None,
        "uptime_ratio_actual": None,
    }
    entry = FakeEntry()

    ratio_sensor = FlowerhubMonthlyUptimeRatioSensor(coord, entry)
    uptime_sensor = FlowerhubMonthlyUptimeSensor(coord, entry)
    downtime_sensor = FlowerhubMonthlyDowntimeSensor(coord, entry)

    # All sensors should return None when data is None
    assert ratio_sensor.native_value is None
    assert uptime_sensor.native_value is None
    assert downtime_sensor.native_value is None


def test_uptime_sensors_unique_ids():
    """Test that uptime sensors have unique IDs."""
    coord = FakeCoordinator()
    entry = FakeEntry(entry_id="test_123")

    ratio_sensor = FlowerhubMonthlyUptimeRatioSensor(coord, entry)
    ratio_total_sensor = FlowerhubMonthlyUptimeRatioTotalSensor(coord, entry)
    uptime_sensor = FlowerhubMonthlyUptimeSensor(coord, entry)
    downtime_sensor = FlowerhubMonthlyDowntimeSensor(coord, entry)

    assert ratio_sensor._attr_unique_id == "test_123_monthly_uptime_ratio"
    assert ratio_total_sensor._attr_unique_id == "test_123_monthly_uptime_ratio_total"
    assert uptime_sensor._attr_unique_id == "test_123_monthly_uptime"
    assert downtime_sensor._attr_unique_id == "test_123_monthly_downtime"


def test_uptime_sensors_translation_keys():
    """Test that uptime sensors have correct translation keys."""
    coord = FakeCoordinator()
    entry = FakeEntry()

    ratio_sensor = FlowerhubMonthlyUptimeRatioSensor(coord, entry)
    ratio_total_sensor = FlowerhubMonthlyUptimeRatioTotalSensor(coord, entry)
    uptime_sensor = FlowerhubMonthlyUptimeSensor(coord, entry)
    downtime_sensor = FlowerhubMonthlyDowntimeSensor(coord, entry)

    assert ratio_sensor.entity_description.translation_key == "monthly_uptime_ratio"
    assert (
        ratio_total_sensor.entity_description.translation_key
        == "monthly_uptime_ratio_total"
    )
    assert uptime_sensor.entity_description.translation_key == "monthly_uptime"
    assert downtime_sensor.entity_description.translation_key == "monthly_downtime"
