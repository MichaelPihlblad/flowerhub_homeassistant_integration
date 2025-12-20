import time
from datetime import timedelta

import pytest
from flowerhub.sensor import FlowerhubStatusSensor


class FakeCoordinator:
    def __init__(self, update_interval: timedelta, last_update_success: bool = True):
        self.update_interval = update_interval
        self.last_update_success = last_update_success
        self._last_success_monotonic = None
        self.data = {"status": "ok", "message": "ok"}


class FakeEntry:
    def __init__(self, entry_id: str = "entry_status"):
        self.entry_id = entry_id


@pytest.mark.parametrize(
    "age_seconds, expected",
    [
        (120, True),  # 2x interval -> available
        (179, True),  # just under 3x interval -> available
        (181, False),  # just over 3x interval -> unavailable
    ],
)
def test_status_sensor_availability_by_staleness(age_seconds, expected):
    coord = FakeCoordinator(
        update_interval=timedelta(seconds=60), last_update_success=True
    )
    entry = FakeEntry()
    sensor = FlowerhubStatusSensor(coord, entry)

    # Simulate last success age
    coord._last_success_monotonic = time.monotonic() - age_seconds

    assert sensor.available is expected


def test_status_sensor_availability_before_first_success():
    # No recorded success yet: falls back to last_update_success
    coord = FakeCoordinator(
        update_interval=timedelta(seconds=60), last_update_success=True
    )
    entry = FakeEntry()
    sensor = FlowerhubStatusSensor(coord, entry)

    coord._last_success_monotonic = None
    assert sensor.available is True

    # If last_update_success is False, should be unavailable until we record a success
    coord.last_update_success = False
    assert sensor.available is False
