"""Select platform for SPRSUN Heat Pump."""
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from pymodbus.client import ModbusTcpClient

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
        if self._key in self.coordinator.data:
            value = self.coordinator.data[self._key]
            # Convert scaled value back to raw integer
            raw_value = int(value)
            return self._options_dict.get(raw_value)
        return None
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success
    
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
        
        await self._async_write_register(value)
        
        # Update cached value immediately for responsiveness
        self.coordinator.data[self._key] = value
        
        # Request coordinator refresh to read back actual value
        await self.coordinator.async_request_refresh()
    
    async def async_added_to_hass(self) -> None:
        """When entity is added to hass, read initial value."""
        await super().async_added_to_hass()
        
        # Read initial value if not in coordinator
        if self._key not in self.coordinator.data:
            try:
                value = await self._async_read_register()
                self.coordinator.data[self._key] = value
            except Exception as err:
                _LOGGER.warning("Failed to read initial value for %s: %s", self._key, err)
    
    async def _async_read_register(self) -> int:
        """Read from Modbus register."""
        def _read():
            client = ModbusTcpClient(host=self._host, port=self._port, timeout=5)
            try:
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
                
            finally:
                client.close()
        
        return await self.hass.async_add_executor_job(_read)
    
    async def _async_write_register(self, value: int) -> None:
        """Write to Modbus register."""
        def _write():
            client = ModbusTcpClient(host=self._host, port=self._port, timeout=5)
            try:
                if not client.connect():
                    raise ConnectionError("Cannot connect to Modbus device")
                
                result = client.write_register(
                    address=self._address,
                    value=value,
                    device_id=self._device_address
                )
                
                if result.isError():
                    raise ValueError(f"Modbus write error: {result}")
                
                _LOGGER.info(
                    "Wrote to register 0x%04X: value=%d (%s)",
                    self._address, value, self._options_dict.get(value, "Unknown")
                )
                
            finally:
                client.close()
        
        await self.hass.async_add_executor_job(_write)
