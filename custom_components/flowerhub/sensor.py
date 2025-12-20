"""Simple sensor platform for Flowerhub integration (example)."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfEnergy,
    UnitOfPower,
)

from .const import DEFAULT_NAME, DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    if isinstance(data, dict) and "coordinator" in data:
        coordinator = data["coordinator"]
    else:
        coordinator = data  # for test
    async_add_entities(
        [
            FlowerhubStatusSensor(coordinator, entry),
            FlowerhubLastUpdatedSensor(coordinator, entry),
            FlowerhubInverterNameSensor(coordinator, entry),
            FlowerhubBatteryNameSensor(coordinator, entry),
            FlowerhubPowerCapacitySensor(coordinator, entry),
            FlowerhubEnergyCapacitySensor(coordinator, entry),
            FlowerhubFuseSizeSensor(coordinator, entry),
            FlowerhubIsInstalledSensor(coordinator, entry),
            FlowerhubInverterManufacturerSensor(coordinator, entry),
            FlowerhubInverterBatteryStacksSensor(coordinator, entry),
            FlowerhubBatteryManufacturerSensor(coordinator, entry),
            FlowerhubBatteryMaxModulesSensor(coordinator, entry),
            FlowerhubBatteryPowerCapacitySensor(coordinator, entry),
        ],
        True,
    )


class FlowerhubBaseSensor(SensorEntity):
    _attr_has_entity_name = True
    _device_model = "Powergrid balancing system"

    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
        self._config_entry = entry
        super().__init__()

    async def async_added_to_hass(self):
        if hasattr(self.coordinator, "async_add_listener"):
            self.async_on_remove(
                self.coordinator.async_add_listener(self._handle_coordinator_update)
            )

    def _handle_coordinator_update(self):
        self.async_write_ha_state()

    @property
    def device_info(self):
        data = getattr(self.coordinator, "data", {}) or {}
        client = getattr(self.coordinator, "client", None)

        # Prefer client-exposed properties; fall back to coordinator data
        inverter_name = (
            getattr(client, "inverter_name", None) if client else None
        ) or data.get("inverter_name")
        inverter_manufacturer = (
            getattr(client, "inverter_manufacturer", None) if client else None
        ) or data.get("inverter_manufacturer")
        battery_name = (
            getattr(client, "battery_name", None) if client else None
        ) or data.get("battery_name")
        battery_manufacturer = (
            getattr(client, "battery_manufacturer", None) if client else None
        ) or data.get("battery_manufacturer")

        hw_parts = []
        if inverter_name or inverter_manufacturer:
            hw_parts.append(
                f"Inverter: {inverter_manufacturer or ''} {inverter_name or ''}".strip()
            )
        if battery_name or battery_manufacturer:
            hw_parts.append(
                f"Battery: {battery_manufacturer or ''} {battery_name or ''}".strip()
            )

        # Optionally include asset identifiers if available on the client
        asset_id = getattr(client, "asset_id", None) if client else None
        asset_owner_id = getattr(client, "asset_owner_id", None) if client else None

        if asset_id:
            hw_parts.append(f"Asset ID: {asset_id}")
        if asset_owner_id:
            hw_parts.append(f"Owner ID: {asset_owner_id}")

        hw_version = " | ".join(hw_parts) if hw_parts else None

        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": DEFAULT_NAME,
            "manufacturer": "FlowerHub",
            "model": self._device_model,
            "hw_version": hw_version,
            "sw_version": None,
            "configuration_url": "https://portal.flowerhub.se",
        }

    @property
    def available(self) -> bool:
        # Default HA behavior for most sensors
        return self.coordinator.last_update_success


class FlowerhubStatusSensor(FlowerhubBaseSensor):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self.entity_description = SensorEntityDescription(
            key="status",
            translation_key="status",
        )
        self._attr_unique_id = f"{entry.entry_id}_status"

    @property
    def available(self) -> bool:
        # For connection status only: consider entity unavailable
        # if no successful update occurred within 3x the update interval
        coord = self.coordinator
        try:
            interval = getattr(coord, "update_interval", None)
            interval_sec = float(interval.total_seconds()) if interval else 60.0
        except Exception:
            interval_sec = 60.0

        last_success = getattr(coord, "_last_success_monotonic", None)
        if last_success is None:
            return bool(getattr(coord, "last_update_success", False))

        from time import monotonic

        age = monotonic() - last_success
        return age <= (3.0 * interval_sec)

    @property
    def state(self):
        return self.coordinator.data.get("status")

    @property
    def extra_state_attributes(self):
        return {
            "message": self.coordinator.data.get("message"),
            "last_updated": self.coordinator.data.get("last_updated"),
        }


class FlowerhubLastUpdatedSensor(FlowerhubBaseSensor):
    _device_model = "Solar System"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self.entity_description = SensorEntityDescription(
            key="last_updated",
            translation_key="last_updated",
            device_class=SensorDeviceClass.TIMESTAMP,
            entity_category=EntityCategory.DIAGNOSTIC,
        )
        self._attr_unique_id = f"{entry.entry_id}_last_updated"

    @property
    def native_value(self) -> datetime | None:
        """Return the last updated timestamp."""
        if self.coordinator.data and self.coordinator.data.get("last_updated"):
            return datetime.fromisoformat(self.coordinator.data["last_updated"])
        return None


class FlowerhubInverterNameSensor(FlowerhubBaseSensor):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self.entity_description = SensorEntityDescription(
            key="inverter_name",
            translation_key="inverter_name",
            entity_category=EntityCategory.DIAGNOSTIC,
        )
        self._attr_unique_id = f"{entry.entry_id}_inverter_name"

    @property
    def state(self):
        return self.coordinator.data.get("inverter_name")


class FlowerhubBatteryNameSensor(FlowerhubBaseSensor):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self.entity_description = SensorEntityDescription(
            key="battery_name",
            translation_key="battery_name",
            entity_category=EntityCategory.DIAGNOSTIC,
        )
        self._attr_unique_id = f"{entry.entry_id}_battery_name"

    @property
    def state(self):
        return self.coordinator.data.get("battery_name")


class FlowerhubPowerCapacitySensor(FlowerhubBaseSensor):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self.entity_description = SensorEntityDescription(
            key="power_capacity",
            translation_key="power_capacity",
            device_class=SensorDeviceClass.POWER,
            native_unit_of_measurement=UnitOfPower.KILO_WATT,
            entity_category=EntityCategory.DIAGNOSTIC,
        )
        self._attr_unique_id = f"{entry.entry_id}_power_capacity"

    @property
    def native_value(self):
        return self.coordinator.data.get("power_capacity")


class FlowerhubEnergyCapacitySensor(FlowerhubBaseSensor):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self.entity_description = SensorEntityDescription(
            key="energy_capacity",
            translation_key="energy_capacity",
            device_class=SensorDeviceClass.ENERGY_STORAGE,
            native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
            entity_category=EntityCategory.DIAGNOSTIC,
        )
        self._attr_unique_id = f"{entry.entry_id}_energy_capacity"

    @property
    def native_value(self):
        return self.coordinator.data.get("energy_capacity")


class FlowerhubFuseSizeSensor(FlowerhubBaseSensor):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self.entity_description = SensorEntityDescription(
            key="fuse_size",
            translation_key="fuse_size",
            device_class=SensorDeviceClass.CURRENT,
            native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            entity_category=EntityCategory.DIAGNOSTIC,
        )
        self._attr_unique_id = f"{entry.entry_id}_fuse_size"

    @property
    def native_value(self):
        return self.coordinator.data.get("fuse_size")


class FlowerhubIsInstalledSensor(FlowerhubBaseSensor):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self.entity_description = SensorEntityDescription(
            key="is_installed",
            translation_key="is_installed",
            entity_category=EntityCategory.DIAGNOSTIC,
        )
        self._attr_unique_id = f"{entry.entry_id}_is_installed"

    @property
    def state(self):
        is_installed = self.coordinator.data.get("is_installed")
        return "Yes" if is_installed else "No"


class FlowerhubInverterManufacturerSensor(FlowerhubBaseSensor):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self.entity_description = SensorEntityDescription(
            key="inverter_manufacturer",
            translation_key="inverter_manufacturer",
            entity_category=EntityCategory.DIAGNOSTIC,
        )
        self._attr_unique_id = f"{entry.entry_id}_inverter_manufacturer"

    @property
    def state(self):
        inverter = self.coordinator.data.get("inverter", {})
        return inverter.get("manufacturerName")


class FlowerhubInverterBatteryStacksSensor(FlowerhubBaseSensor):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self.entity_description = SensorEntityDescription(
            key="inverter_battery_stacks",
            translation_key="inverter_battery_stacks",
            entity_category=EntityCategory.DIAGNOSTIC,
        )
        self._attr_unique_id = f"{entry.entry_id}_inverter_battery_stacks"

    @property
    def state(self):
        inverter = self.coordinator.data.get("inverter", {})
        return inverter.get("numberOfBatteryStacksSupported")


class FlowerhubBatteryManufacturerSensor(FlowerhubBaseSensor):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self.entity_description = SensorEntityDescription(
            key="battery_manufacturer",
            translation_key="battery_manufacturer",
            entity_category=EntityCategory.DIAGNOSTIC,
        )
        self._attr_unique_id = f"{entry.entry_id}_battery_manufacturer"

    @property
    def state(self):
        battery = self.coordinator.data.get("battery", {})
        return battery.get("manufacturerName")


class FlowerhubBatteryMaxModulesSensor(FlowerhubBaseSensor):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self.entity_description = SensorEntityDescription(
            key="battery_max_modules",
            translation_key="battery_max_modules",
            entity_category=EntityCategory.DIAGNOSTIC,
        )
        self._attr_unique_id = f"{entry.entry_id}_battery_max_modules"

    @property
    def state(self):
        battery = self.coordinator.data.get("battery", {})
        return battery.get("maxNumberOfBatteryModules")


class FlowerhubBatteryPowerCapacitySensor(FlowerhubBaseSensor):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self.entity_description = SensorEntityDescription(
            key="battery_power_capacity",
            translation_key="battery_power_capacity",
            device_class=SensorDeviceClass.POWER,
            native_unit_of_measurement=UnitOfPower.KILO_WATT,
            entity_category=EntityCategory.DIAGNOSTIC,
        )
        self._attr_unique_id = f"{entry.entry_id}_battery_power_capacity"

    @property
    def native_value(self):
        battery = self.coordinator.data.get("battery", {})
        return battery.get("powerCapacity")
