"""Sensor platform for SPRSUN Heat Pump."""
import logging

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, REGISTERS_READ_ONLY

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SPRSUN sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
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
        self._attr_name = f"{config_entry.data[CONF_NAME]} {name}"
        self._attr_unique_id = f"{config_entry.entry_id}_{key}"
        self._attr_native_unit_of_measurement = unit
        
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
        
        # Set state class for statistical sensors
        if device_class in ["temperature", "pressure", "power", "current", "frequency"]:
            self._attr_state_class = SensorStateClass.MEASUREMENT
        
        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": config_entry.data[CONF_NAME],
            "manufacturer": "SPRSUN",
            "model": "Heat Pump",
        }
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get(self._key)
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self._key in self.coordinator.data
        )
