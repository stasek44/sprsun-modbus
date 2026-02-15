"""Switch platform for SPRSUN Heat Pump."""
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, REGISTERS_SWITCH

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SPRSUN switches."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    for key, (address, bit, name, _) in REGISTERS_SWITCH.items():
        entities.append(
            SPRSUNSwitch(
                coordinator,
                config_entry,
                key,
                name,
                address,
                bit,
            )
        )
    
    async_add_entities(entities)


class SPRSUNSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a SPRSUN switch."""
    
    def __init__(
        self,
        coordinator,
        config_entry: ConfigEntry,
        key: str,
        name: str,
        address: int,
        bit: int,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        
        self._key = key
        self._address = address
        self._bit = bit
        self._attr_name = f"{config_entry.data[CONF_NAME]} {name}"
        self._attr_unique_id = f"{config_entry.entry_id}_{key}"
        
        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": config_entry.data[CONF_NAME],
            "manufacturer": "SPRSUN",
            "model": "Heat Pump",
        }
    
    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        # Read current register value
        value = self.coordinator.data.get(self._key, 0)
        # Check if our bit is set
        return bool(value & (1 << self._bit))
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self._key in self.coordinator.data
        )
    
    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        await self._async_write_bit(True)
        # Note: Cache updated in _async_write_bit, no immediate refresh needed
    
    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        await self._async_write_bit(False)
        # Note: Cache updated in _async_write_bit, no immediate refresh needed
    
    async def _async_write_bit(self, value: bool) -> None:
        """Write bit to Modbus register (safe bit manipulation)."""
        def _write():
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
            
            # Modify only our bit
            if value:
                new_value = current_value | (1 << self._bit)  # Set bit
            else:
                new_value = current_value & ~(1 << self._bit)  # Clear bit
            
            # Write back if changed
            if new_value != current_value:
                result = client.write_register(
                    address=self._address,
                    value=new_value,
                    device_id=self.coordinator.device_address
                )
                
                if result.isError():
                    raise ValueError(f"Modbus write error: {result}")
                
                _LOGGER.info(
                    "Wrote bit %d=%s to register 0x%04X (was 0x%04X, now 0x%04X)",
                    self._bit, value, self._address, current_value, new_value
                )
            
            # Update cached value
            self.coordinator.data[self._key] = new_value
        
        await self.hass.async_add_executor_job(_write)
