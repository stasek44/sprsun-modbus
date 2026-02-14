"""Binary sensor platform for SPRSUN Heat Pump."""
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, BINARY_SENSOR_BITS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SPRSUN binary sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    for key, (address, bit, name) in BINARY_SENSOR_BITS.items():
        entities.append(
            SPRSUNBinarySensor(
                coordinator,
                config_entry,
                key,
                name,
                bit,
            )
        )
    
    async_add_entities(entities)


class SPRSUNBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a SPRSUN binary sensor (bit field)."""
    
    def __init__(
        self,
        coordinator,
        config_entry: ConfigEntry,
        key: str,
        name: str,
        bit: int,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        
        self._key = key
        self._bit = bit
        self._attr_name = f"{config_entry.data[CONF_NAME]} {name}"
        self._attr_unique_id = f"{config_entry.entry_id}_{key}"
        self._attr_device_class = BinarySensorDeviceClass.RUNNING
        
        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": config_entry.data[CONF_NAME],
            "manufacturer": "SPRSUN",
            "model": "Heat Pump",
        }
    
    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        # Read from working status register (0x0003)
        register_value = self.coordinator.data.get("working_status_register", 0)
        # Check if bit is set
        return bool(register_value & (1 << self._bit))
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and "working_status_register" in self.coordinator.data
        )
