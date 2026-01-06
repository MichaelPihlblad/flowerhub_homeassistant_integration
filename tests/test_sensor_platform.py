from datetime import datetime

import pytest
from flowerhub.sensor import (
    FlowerhubBatteryNameSensor,
    FlowerhubEnergyCapacitySensor,
    FlowerhubFuseSizeSensor,
    FlowerhubInverterNameSensor,
    FlowerhubIsInstalledSensor,
    FlowerhubLastUpdatedSensor,
    FlowerhubPowerCapacitySensor,
    FlowerhubStatusSensor,
)


class FakeCoordinator:
    def __init__(self):
        self.last_update_success = True
        self.data = {
            "status": "state_1",
            "message": "ok",
            "last_updated": datetime.now().isoformat(),
            "inverter_name": "SUN2000 M1",
            "battery_name": "LUNA2000 S0",
            "power_capacity": 10,
            "energy_capacity": 15,
            "fuse_size": 16,
            "is_installed": True,
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
    "sensor_cls, expected",
    [
        (FlowerhubStatusSensor, ("state_1", {"message": "ok"})),
        (FlowerhubLastUpdatedSensor, ("timestamp", None)),
        (FlowerhubInverterNameSensor, ("SUN2000 M1", None)),
        (FlowerhubBatteryNameSensor, ("LUNA2000 S0", None)),
        (FlowerhubPowerCapacitySensor, (10, None)),
        (FlowerhubEnergyCapacitySensor, (15, None)),
        (FlowerhubFuseSizeSensor, (16, None)),
        (FlowerhubIsInstalledSensor, ("Yes", None)),
    ],
)
def test_sensor_values_and_device_info(sensor_cls, expected):
    coord = FakeCoordinator()
    entry = FakeEntry()
    sensor = sensor_cls(coord, entry)

    # Available reflects coordinator success
    assert sensor.available is True

    # Check primary value
    if isinstance(sensor, FlowerhubLastUpdatedSensor):
        val = sensor.native_value
        assert isinstance(val, datetime) or val is None
    elif isinstance(
        sensor,
        (
            FlowerhubPowerCapacitySensor,
            FlowerhubEnergyCapacitySensor,
            FlowerhubFuseSizeSensor,
        ),
    ):
        assert sensor.native_value == expected[0]
    else:
        # Status, InverterName, BatteryName, IsInstalled use state
        assert sensor.state == expected[0]

    # Device info contains identifiers and hw_version combined
    info = sensor.device_info
    assert ("identifiers" in info) and info["identifiers"]
    assert info["manufacturer"] == "Flowerhub"
    assert "configuration_url" in info and info["configuration_url"].startswith(
        "https://"
    )
