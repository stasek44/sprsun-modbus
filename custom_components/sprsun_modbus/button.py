"""Button platform for SPRSUN Heat Pump."""
import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, REGISTERS_BUTTON

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SPRSUN buttons."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    for key, (address, bit, name, description) in REGISTERS_BUTTON.items():
        entities.append(
            SPRSUNButton(
                coordinator,
                config_entry,
                key,
                name,
                address,
                bit,
                description,
            )
        )
    
    async_add_entities(entities)


class SPRSUNButton(CoordinatorEntity, ButtonEntity):
    """Representation of a SPRSUN button."""
    
    def __init__(
        self,
        coordinator,
        config_entry: ConfigEntry,
        key: str,
        name: str,
        address: int,
        bit: int,
        description: str,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        
        self._key = key
        self._address = address
        self._bit = bit
        self._attr_name = f"{config_entry.data[CONF_NAME]} {name}"
        self._attr_unique_id = f"{config_entry.entry_id}_{key}"
        self._attr_entity_description = description
        
        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": config_entry.data[CONF_NAME],
            "manufacturer": "SPRSUN",
            "model": "Heat Pump",
        }
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success
    
    async def async_press(self) -> None:
        """Handle the button press."""
        await self._async_trigger_bit()
    
    async def _async_trigger_bit(self) -> None:
        """Trigger momentary bit action (read-modify-write, then clear)."""
        def _trigger():
            client = self.coordinator.client
            if client is None or not client.connected:
                if not client.connect():
                    raise ConnectionError("Cannot connect to Modbus device")
            
            # Read current register value
            result = client.read_holding_registers(
                address=self._address,
                count=1,
                device_id=self.coordinator.device_address
            )
            
            if result.isError():
                raise ValueError(f"Modbus read error: {result}")
            
            current_value = result.registers[0]
            
            # Set the bit (trigger action)
            trigger_value = current_value | (1 << self._bit)
            
            # Write trigger value
            result = client.write_register(
                address=self._address,
                value=trigger_value,
                device_id=self.coordinator.device_address
            )
            
            if result.isError():
                raise ValueError(f"Modbus write error: {result}")
            
            _LOGGER.info(
                "Triggered bit %d on register 0x%04X (was 0x%04X, triggered 0x%04X)",
                self._bit, self._address, current_value, trigger_value
            )
            
            # Note: Bit automatically clears after device processes action
            # No need to manually clear or update cache
        
        await self.hass.async_add_executor_job(_trigger)
