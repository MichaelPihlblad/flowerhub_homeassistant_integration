"""Simple sensor platform for Flowerhub integration (example)."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import EntityCategory, UnitOfPower, UnitOfEnergy, UnitOfElectricCurrent

from .const import DOMAIN, DEFAULT_NAME


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    if isinstance(data, dict) and "coordinator" in data:
        coordinator = data["coordinator"]
    else:
        coordinator = data  # for test
    async_add_entities([
        FlowerhubStatusSensor(coordinator, entry),
        FlowerhubLastUpdatedSensor(coordinator, entry),
        FlowerhubInverterNameSensor(coordinator, entry),
        FlowerhubBatteryNameSensor(coordinator, entry),
        FlowerhubPowerCapacitySensor(coordinator, entry),
        FlowerhubEnergyCapacitySensor(coordinator, entry),
        FlowerhubFuseSizeSensor(coordinator, entry),
        FlowerhubIsInstalledSensor(coordinator, entry),
    ], True)


class FlowerhubStatusSensor(SensorEntity):
    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
        self._config_entry = entry
        self._attr_name = "FlowerHub Connection Status"
        self._attr_unique_id = f"{entry.entry_id}_status"
        super().__init__()

    async def async_added_to_hass(self):
        if hasattr(self.coordinator, 'async_add_listener'):
            self.async_on_remove(self.coordinator.async_add_listener(self._handle_coordinator_update))

    def _handle_coordinator_update(self):
        self.async_write_ha_state()

    @property
    def device_info(self):
        data = self.coordinator.data
        hw_version = None
        if data.get("inverter_name") and data.get("battery_name"):
            hw_version = f"{data['inverter_name']} / {data['battery_name']}"
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": DEFAULT_NAME,
            "manufacturer": "FlowerHub",
            "model": "Electric grid battery balance system",
            "hw_version": hw_version,
            "sw_version": None,
            "configuration_url": "https://portal.flowerhub.se",
        }

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def state(self):
        return self.coordinator.data.get("status")

    @property
    def extra_state_attributes(self):
        return {"message": self.coordinator.data.get("message")}


class FlowerhubLastUpdatedSensor(SensorEntity):
    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
        self._config_entry = entry
        self._attr_name = "FlowerHub Data Last Updated"
        self._attr_unique_id = f"{entry.entry_id}_last_updated"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        super().__init__()

    async def async_added_to_hass(self):
        if hasattr(self.coordinator, 'async_add_listener'):
            self.async_on_remove(self.coordinator.async_add_listener(self._handle_coordinator_update))

    def _handle_coordinator_update(self):
        self.async_write_ha_state()

    @property
    def device_info(self):
        data = self.coordinator.data
        hw_version = None
        if data.get("inverter_name") and data.get("battery_name"):
            hw_version = f"{data['inverter_name']} / {data['battery_name']}"
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": DEFAULT_NAME,
            "manufacturer": "FlowerHub",
            "model": "Solar System",
            "hw_version": hw_version,
            "sw_version": None,
            "configuration_url": "https://portal.flowerhub.se",
        }

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def native_value(self) -> datetime | None:
        """Return the last updated timestamp."""
        if self.coordinator.data and self.coordinator.data.get("last_updated"):
            return datetime.fromisoformat(self.coordinator.data["last_updated"])
        return None


class FlowerhubInverterNameSensor(SensorEntity):
    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
        self._config_entry = entry
        self._attr_name = "FlowerHub Inverter Name"
        self._attr_unique_id = f"{entry.entry_id}_inverter_name"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        super().__init__()

    async def async_added_to_hass(self):
        self.async_on_remove(self.coordinator.async_add_listener(self._handle_coordinator_update))

    def _handle_coordinator_update(self):
        self.async_write_ha_state()

    @property
    def device_info(self):
        data = self.coordinator.data
        hw_version = None
        if data.get("inverter_name") and data.get("battery_name"):
            hw_version = f"{data['inverter_name']} / {data['battery_name']}"
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": DEFAULT_NAME,
            "manufacturer": "FlowerHub",
            "model": "Electric grid battery balance system",
            "hw_version": hw_version,
            "sw_version": None,
            "configuration_url": "https://portal.flowerhub.se",
        }

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def state(self):
        return self.coordinator.data.get("inverter_name")


class FlowerhubBatteryNameSensor(SensorEntity):
    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
        self._config_entry = entry
        self._attr_name = "FlowerHub Battery Name"
        self._attr_unique_id = f"{entry.entry_id}_battery_name"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        super().__init__()

    async def async_added_to_hass(self):
        self.async_on_remove(self.coordinator.async_add_listener(self._handle_coordinator_update))

    def _handle_coordinator_update(self):
        self.async_write_ha_state()

    @property
    def device_info(self):
        data = self.coordinator.data
        hw_version = None
        if data.get("inverter_name") and data.get("battery_name"):
            hw_version = f"{data['inverter_name']} / {data['battery_name']}"
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": DEFAULT_NAME,
            "manufacturer": "FlowerHub",
            "model": "Electric grid battery balance system",
            "hw_version": hw_version,
            "sw_version": None,
            "configuration_url": "https://portal.flowerhub.se",
        }

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def state(self):
        return self.coordinator.data.get("battery_name")


class FlowerhubPowerCapacitySensor(SensorEntity):
    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
        self._config_entry = entry
        self._attr_name = "FlowerHub Power Capacity"
        self._attr_unique_id = f"{entry.entry_id}_power_capacity"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_native_unit_of_measurement = UnitOfPower.KILO_WATT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        super().__init__()

    async def async_added_to_hass(self):
        self.async_on_remove(self.coordinator.async_add_listener(self._handle_coordinator_update))

    def _handle_coordinator_update(self):
        self.async_write_ha_state()

    @property
    def device_info(self):
        data = self.coordinator.data
        hw_version = None
        if data.get("inverter_name") and data.get("battery_name"):
            hw_version = f"{data['inverter_name']} / {data['battery_name']}"
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": DEFAULT_NAME,
            "manufacturer": "FlowerHub",
            "model": "Electric grid battery balance system",
            "hw_version": hw_version,
            "sw_version": None,
            "configuration_url": "https://portal.flowerhub.se",
        }

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def native_value(self):
        return self.coordinator.data.get("power_capacity")


class FlowerhubEnergyCapacitySensor(SensorEntity):
    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
        self._config_entry = entry
        self._attr_name = "FlowerHub Energy Capacity"
        self._attr_unique_id = f"{entry.entry_id}_energy_capacity"
        self._attr_device_class = SensorDeviceClass.ENERGY_STORAGE
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        super().__init__()

    async def async_added_to_hass(self):
        self.async_on_remove(self.coordinator.async_add_listener(self._handle_coordinator_update))

    def _handle_coordinator_update(self):
        self.async_write_ha_state()

    @property
    def device_info(self):
        data = self.coordinator.data
        hw_version = None
        if data.get("inverter_name") and data.get("battery_name"):
            hw_version = f"{data['inverter_name']} / {data['battery_name']}"
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": DEFAULT_NAME,
            "manufacturer": "FlowerHub",
            "model": "Electric grid battery balance system",
            "hw_version": hw_version,
            "sw_version": None,
            "configuration_url": "https://portal.flowerhub.se",
        }

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def native_value(self):
        return self.coordinator.data.get("energy_capacity")


class FlowerhubFuseSizeSensor(SensorEntity):
    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
        self._config_entry = entry
        self._attr_name = "FlowerHub Fuse Size"
        self._attr_unique_id = f"{entry.entry_id}_fuse_size"
        self._attr_device_class = SensorDeviceClass.CURRENT
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        super().__init__()

    async def async_added_to_hass(self):
        self.async_on_remove(self.coordinator.async_add_listener(self._handle_coordinator_update))

    def _handle_coordinator_update(self):
        self.async_write_ha_state()

    @property
    def device_info(self):
        data = self.coordinator.data
        hw_version = None
        if data.get("inverter_name") and data.get("battery_name"):
            hw_version = f"{data['inverter_name']} / {data['battery_name']}"
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": DEFAULT_NAME,
            "manufacturer": "FlowerHub",
            "model": "Electric grid battery balance system",
            "hw_version": hw_version,
            "sw_version": None,
            "configuration_url": "https://portal.flowerhub.se",
        }

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def native_value(self):
        return self.coordinator.data.get("fuse_size")


class FlowerhubIsInstalledSensor(SensorEntity):
    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
        self._config_entry = entry
        self._attr_name = "FlowerHub Is Installed"
        self._attr_unique_id = f"{entry.entry_id}_is_installed"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        super().__init__()

    async def async_added_to_hass(self):
        self.async_on_remove(self.coordinator.async_add_listener(self._handle_coordinator_update))

    def _handle_coordinator_update(self):
        self.async_write_ha_state()

    @property
    def device_info(self):
        data = self.coordinator.data
        hw_version = None
        if data.get("inverter_name") and data.get("battery_name"):
            hw_version = f"{data['inverter_name']} / {data['battery_name']}"
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": DEFAULT_NAME,
            "manufacturer": "FlowerHub",
            "model": "Electric grid battery balance system",
            "hw_version": hw_version,
            "sw_version": None,
            "configuration_url": "https://portal.flowerhub.se",
        }

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def state(self):
        is_installed = self.coordinator.data.get("is_installed")
        return "Yes" if is_installed else "No"
