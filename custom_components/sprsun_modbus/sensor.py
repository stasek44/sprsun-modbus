"""Sensor platform for SPRSUN Heat Pump."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, REGISTERS_READ_ONLY

DIAGNOSTIC_SENSOR_KEYS = {
    "software_version_year",
    "software_version_month_day",
    "controller_version",
    "display_version",
    "switching_input_symbol",
    "working_status_mark",
    "output_symbol_1",
    "output_symbol_2",
    "output_symbol_3",
    "failure_symbol_1",
    "failure_symbol_2",
    "failure_symbol_3",
    "failure_symbol_4",
    "failure_symbol_5",
    "failure_symbol_6",
    "failure_symbol_7",
    "freq_conversion_failure_1",
    "freq_conversion_failure_2",
    "freq_conversion_fault_high",
    "freq_conversion_fault_low",
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SPRSUN sensors."""
    coordinator = getattr(config_entry, "runtime_data", None) or hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    for address, (key, name, scale, unit, device_class) in REGISTERS_READ_ONLY.items():
        entities.append(
            SPRSUNSensor(
                coordinator,
                config_entry,
                key,
                name,
                unit,
                device_class,
            )
        )
    
    async_add_entities(entities)


class SPRSUNSensor(CoordinatorEntity, SensorEntity):
    """Representation of a SPRSUN sensor."""
    
    _attr_has_entity_name = True
    
    def __init__(
        self,
        coordinator,
        config_entry: ConfigEntry,
        key: str,
        name: str,
        unit: str | None,
        device_class: str | None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{config_entry.entry_id}_{key}"
        self._attr_native_unit_of_measurement = unit
        
        if key in DIAGNOSTIC_SENSOR_KEYS:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        
        # Set device class
        if device_class == "temperature":
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
        elif device_class == "pressure":
            self._attr_device_class = SensorDeviceClass.PRESSURE
        elif device_class == "power":
            self._attr_device_class = SensorDeviceClass.POWER
        elif device_class == "current":
            self._attr_device_class = SensorDeviceClass.CURRENT
        elif device_class == "frequency":
            self._attr_device_class = SensorDeviceClass.FREQUENCY
        elif device_class == "voltage":
            self._attr_device_class = SensorDeviceClass.VOLTAGE
        
        # Set state class for statistical sensors
        if device_class in ["temperature", "pressure", "power", "current", "frequency", "voltage"]:
            self._attr_state_class = SensorStateClass.MEASUREMENT
        
        # Device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=config_entry.data[CONF_NAME],
            manufacturer="SPRSUN",
            model="Heat Pump",
        )
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        cache_entry = self.coordinator.data.get(self._key)
        if cache_entry is not None:
            # Handle new format (dict with value/timestamp)
            if isinstance(cache_entry, dict):
                return cache_entry.get("value")
            # Handle old format (raw value) for backwards compatibility
            return cache_entry
        return None
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return bool(
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self._key in self.coordinator.data
        )
