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
        # Read current register value from cache using register-based key
        reg_key = f"_control_{self._address:04x}"
        cache_entry = self.coordinator.data.get(reg_key)
        if cache_entry:
            # Handle new format (dict with value/timestamp)
            if isinstance(cache_entry, dict):
                value = int(cache_entry.get("value", 0))
            else:
                # Handle old format
                value = int(cache_entry)
        else:
            value = 0
        
        # Check if our bit is set
        return bool(value & (1 << self._bit))
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Check if coordinator is working
        if not self.coordinator.last_update_success:
            return False
        
        # For switches, we need to check if the REGISTER (not switch key) exists in cache
        # Switches read from _control_XXXX keys that map to their register addresses
        reg_key = f"_control_{self._address:04x}"
        return reg_key in self.coordinator.data
    
    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        await self._async_write_bit(True)
        self.async_write_ha_state()
    
    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        await self._async_write_bit(False)
        self.async_write_ha_state()
    
    async def _async_write_bit(self, value: bool) -> None:
        """Write bit to Modbus register (safe bit manipulation)."""
        import time
        
        def _write():
            # Use coordinator's client for writes
            client = self.coordinator.client
            
            # Ensure connection (auto-reconnect if needed)
            if not self.coordinator._ensure_connection(client, \"client\"):
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
            
            # Update cached value with timestamp using register-based key
            reg_key = f"_control_{self._address:04x}"
            self.coordinator.data[reg_key] = {
                "value": new_value,
                "updated_at": time.time()
            }
        
        await self.hass.async_add_executor_job(_write)
