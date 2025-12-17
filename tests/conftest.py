import sys
import types

import pytest

# Ensure pycares shutdown thread (created by aiodns/pycares) is started
# before the test thread snapshot is taken by pytest-homeassistant so it is
# not reported as a lingering thread during teardown. If pycares isn't
# installed this will simply no-op.
try:
    import pycares

    try:
        # _shutdown_manager is a module-level instance; start its thread.
        _ = getattr(pycares, "_shutdown_manager", None)
        if _ is not None and getattr(_, "start", None):
            _.start()
    except Exception:
        # Be conservative - tests should not fail if we cannot start it.
        pass
except Exception:
    pass

# Ensure pytest-homeassistant-custom-component plugin is loaded
pytest_plugins = "pytest_homeassistant_custom_component"


class FakeStatus:
    def __init__(self, status=None, message=None):
        self.status = status
        self.message = message
        from datetime import datetime

        self.updated_at = datetime.now()


class FakeAsyncFlowerhubClient:
    def __init__(self, session=None):
        self.session = session
        self.flowerhub_status = FakeStatus(status="initial", message="ok")
        self._counter = 0
        self.stopped = False
        self.asset_info = {
            "inverter": {"name": "SUN2000 M1", "powerCapacity": 10},
            "battery": {"name": "LUNA2000 S0", "energyCapacity": 15},
            "fuseSize": 0,
            "isInstalled": True,
        }

    async def async_login(self, username, password):
        # Simulate login
        pass

    async def async_readout_sequence(self):
        # Change status on each call so coordinator updates can be observed
        self._counter += 1
        self.flowerhub_status = FakeStatus(
            status=f"state_{self._counter}", message="ok"
        )

    def stop_periodic_asset_fetch(self):
        self.stopped = True


# Inject fake module `flowerhub_portal_api_client` used by the integration
fake_mod = types.ModuleType("flowerhub_portal_api_client")
setattr(fake_mod, "AsyncFlowerhubClient", FakeAsyncFlowerhubClient)
sys.modules["flowerhub_portal_api_client"] = fake_mod


@pytest.fixture
def fake_client_class():
    return FakeAsyncFlowerhubClient
