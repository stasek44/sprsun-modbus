"""Select platform for SPRSUN Heat Pump."""
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, REGISTERS_SELECT, CONF_DEVICE_ADDRESS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SPRSUN select entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    for address, (key, name, options) in REGISTERS_SELECT.items():
        entities.append(
            SPRSUNSelect(
                coordinator,
                config_entry,
                key,
                name,
                address,
                options,
            )
        )
    
    async_add_entities(entities)


class SPRSUNSelect(CoordinatorEntity, SelectEntity):
    """Representation of a SPRSUN select entity."""
    
    def __init__(
        self,
        coordinator,
        config_entry: ConfigEntry,
        key: str,
        name: str,
        address: int,
        options: dict[int, str],
    ) -> None:
        """Initialize the select."""
        super().__init__(coordinator)
        
        self._key = key
        self._address = address
        self._options_dict = options
        self._attr_name = f"{config_entry.data[CONF_NAME]} {name}"
        self._attr_unique_id = f"{config_entry.entry_id}_{key}"
        self._attr_options = list(options.values())
        
        self._host = config_entry.data[CONF_HOST]
        self._port = config_entry.data[CONF_PORT]
        self._device_address = config_entry.data[CONF_DEVICE_ADDRESS]
        
        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": config_entry.data[CONF_NAME],
            "manufacturer": "SPRSUN",
            "model": "Heat Pump",
        }
    
    @property
    def current_option(self) -> str | None:
        """Return the current option."""
        cache_entry = self.coordinator.data.get(self._key)
        if cache_entry:
            # Handle new format (dict with value/timestamp)
            if isinstance(cache_entry, dict):
                value = cache_entry.get("value")
            else:
                # Handle old format
                value = cache_entry
            
            if value is not None:
                # Convert scaled value back to raw integer
                raw_value = int(value)
                return self._options_dict.get(raw_value)
        return None
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Check if coordinator is working and key exists
        if not self.coordinator.last_update_success:
            return False
        return self._key in self.coordinator.data
    
    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        # Find the value for this option
        value = None
        for val, opt in self._options_dict.items():
            if opt == option:
                value = val
                break
        
        if value is None:
            _LOGGER.error("Invalid option: %s", option)
            return
        
        # Use coordinator's write helper
        await self.coordinator.async_write_register(
            address=self._address,
            value=float(value),
            key=self._key,
            scale=1  # No scaling for select entities
        )
        
        # Trigger UI update immediately
        self.async_write_ha_state()
    
    async def async_added_to_hass(self) -> None:
        """When entity is added to hass, read initial value."""
        await super().async_added_to_hass()
        
        # Initial value will be loaded by coordinator on first refresh
        # No need to read directly anymore
    
    async def _async_read_register(self) -> int:
        """Read from Modbus register."""
        # Use coordinator's persistent connection to avoid conflicts
        def _read():
            client = self.coordinator.client
            if client is None or not client.connected:
                if not client.connect():
                    raise ConnectionError("Cannot connect to Modbus device")
            
            result = client.read_holding_registers(
                address=self._address,
                count=1,
                device_id=self._device_address
            )
            
            if result.isError():
                raise ValueError(f"Modbus read error: {result}")
            
            raw_value = result.registers[0]
            
            _LOGGER.debug(
                "Read register 0x%04X: raw=%d (%s)",
                self._address, raw_value, self._options_dict.get(raw_value, "Unknown")
            )
            
            return raw_value
        
        return await self.hass.async_add_executor_job(_read)
    
    async def _async_write_register(self, value: int) -> None:
        """Write to Modbus register."""
        _LOGGER.info(
            "Writing to register 0x%04X: value=%d (%s)",
            self._address, value, self._options_dict.get(value, "Unknown")
        )
        
        # Use coordinator's write method to avoid connection conflicts
        await self.hass.async_add_executor_job(
            self.coordinator.write_register,
            self._address,
            value
        )
