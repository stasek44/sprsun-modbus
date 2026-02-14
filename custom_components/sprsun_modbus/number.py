"""Number platform for SPRSUN Heat Pump."""
import logging

from homeassistant.components.number import NumberEntity, NumberDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from pymodbus.client import ModbusTcpClient

from .const import DOMAIN, REGISTERS_NUMBER, CONF_DEVICE_ADDRESS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SPRSUN numbers."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    for address, config in REGISTERS_NUMBER.items():
        key, name, scale, unit, min_val, max_val, step, device_class = config
        entities.append(
            SPRSUNNumber(
                coordinator,
                config_entry,
                key,
                name,
                address,
                scale,
                unit,
                min_val,
                max_val,
                step,
                device_class,
            )
        )
    
    async_add_entities(entities)


class SPRSUNNumber(CoordinatorEntity, NumberEntity):
    """Representation of a SPRSUN number."""
    
    def __init__(
        self,
        coordinator,
        config_entry: ConfigEntry,
        key: str,
        name: str,
        address: int,
        scale: float,
        unit: str | None,
        min_val: float,
        max_val: float,
        step: float,
        device_class: str | None,
    ) -> None:
        """Initialize the number."""
        super().__init__(coordinator)
        
        self._key = key
        self._address = address
        self._scale = scale
        self._attr_name = f"{config_entry.data[CONF_NAME]} {name}"
        self._attr_unique_id = f"{config_entry.entry_id}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_native_min_value = min_val
        self._attr_native_max_value = max_val
        self._attr_native_step = step
        
        self._host = config_entry.data[CONF_HOST]
        self._port = config_entry.data[CONF_PORT]
        self._device_address = config_entry.data[CONF_DEVICE_ADDRESS]
        
        # Set device class
        if device_class == "temperature":
            self._attr_device_class = NumberDeviceClass.TEMPERATURE
        elif device_class == "pressure":
            self._attr_device_class = NumberDeviceClass.PRESSURE
        elif device_class == "frequency":
            self._attr_device_class = NumberDeviceClass.FREQUENCY
        
        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": config_entry.data[CONF_NAME],
            "manufacturer": "SPRSUN",
            "model": "Heat Pump",
        }
    
    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        # First try to read from coordinator (cached)
        if self._key in self.coordinator.data:
            return self.coordinator.data[self._key]
        
        # If not in coordinator, read directly (for RW registers)
        return None
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success
    
    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await self._async_write_register(value)
        
        # Update cached value immediately for responsiveness
        if self._key not in self.coordinator.data:
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
    
    async def _async_read_register(self) -> float:
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
                scaled_value = raw_value * self._scale
                
                _LOGGER.debug(
                    "Read register 0x%04X: raw=%d, scaled=%.2f",
                    self._address, raw_value, scaled_value
                )
                
                return scaled_value
                
            finally:
                client.close()
        
        return await self.hass.async_add_executor_job(_read)
    
    async def _async_write_register(self, value: float) -> None:
        """Write to Modbus register."""
        def _write():
            # Convert scaled value back to raw register value
            raw_value = int(value / self._scale)
            
            client = ModbusTcpClient(host=self._host, port=self._port, timeout=5)
            try:
                if not client.connect():
                    raise ConnectionError("Cannot connect to Modbus device")
                
                result = client.write_register(
                    address=self._address,
                    value=raw_value,
                    device_id=self._device_address
                )
                
                if result.isError():
                    raise ValueError(f"Modbus write error: {result}")
                
                _LOGGER.info(
                    "Wrote to register 0x%04X: scaled=%.2f, raw=%d",
                    self._address, value, raw_value
                )
                
            finally:
                client.close()
        
        await self.hass.async_add_executor_job(_write)
