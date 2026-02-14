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
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        
        self._key = key
        self._attr_name = f"{config_entry.data[CONF_NAME]} {name}"
        self._attr_unique_id = f"{config_entry.entry_id}_{key}"
        # No device_class - will show as simple On/Off
        
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
        # Get the source address for this sensor
        source_address, bit, _ = BINARY_SENSOR_BITS[self._key]
        
        # Read from the appropriate register
        # The coordinator stores these as "working_status_register", etc.
        # Map address to data key
        address_to_key = {
            0x0002: "switching_input_symbol",
            0x0003: "working_status_register",  # Special name for backward compatibility
            0x0004: "output_symbol_1",
            0x0005: "output_symbol_2",
            0x0006: "output_symbol_3",
            0x0007: "failure_symbol_1",
            0x0008: "failure_symbol_2",
            0x0009: "failure_symbol_3",
            0x000A: "failure_symbol_4",
            0x000B: "failure_symbol_5",
            0x000C: "failure_symbol_6",
            0x000D: "failure_symbol_7",
        }
        
        register_key = address_to_key.get(source_address)
        if not register_key:
            return False
            
        register_value = self.coordinator.data.get(register_key, 0)
        # Check if bit is set
        return bool(register_value & (1 << bit))
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Get source address for availability check
        source_address, _, _ = BINARY_SENSOR_BITS[self._key]
        
        address_to_key = {
            0x0002: "switching_input_symbol",
            0x0003: "working_status_register",
            0x0004: "output_symbol_1",
            0x0005: "output_symbol_2",
            0x0006: "output_symbol_3",
            0x0007: "failure_symbol_1",
            0x0008: "failure_symbol_2",
            0x0009: "failure_symbol_3",
            0x000A: "failure_symbol_4",
            0x000B: "failure_symbol_5",
            0x000C: "failure_symbol_6",
            0x000D: "failure_symbol_7",
        }
        
        register_key = address_to_key.get(source_address)
        return (
            self.coordinator.last_update_success
            and register_key in self.coordinator.data
        )
