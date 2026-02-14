"""Switch platform for SPRSUN Heat Pump."""
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from pymodbus.client import ModbusTcpClient

from .const import DOMAIN, REGISTERS_SWITCH, CONF_DEVICE_ADDRESS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SPRSUN switches."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    for address, (key, name) in REGISTERS_SWITCH.items():
        entities.append(
            SPRSUNSwitch(
                coordinator,
                config_entry,
                key,
                name,
                address,
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
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        
        self._key = key
        self._address = address
        self._attr_name = f"{config_entry.data[CONF_NAME]} {name}"
        self._attr_unique_id = f"{config_entry.entry_id}_{key}"
        
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
    def is_on(self) -> bool:
        """Return true if switch is on."""
        value = self.coordinator.data.get(self._key, 0)
        return value == 1
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self._key in self.coordinator.data
        )
    
    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        await self._async_write_register(1)
        await self.coordinator.async_request_refresh()
    
    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        await self._async_write_register(0)
        await self.coordinator.async_request_refresh()
    
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
                
                _LOGGER.debug("Wrote %d to register 0x%04X", value, self._address)
                
            finally:
                client.close()
        
        await self.hass.async_add_executor_job(_write)
