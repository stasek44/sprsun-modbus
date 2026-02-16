"""Number platform for SPRSUN Heat Pump."""
import logging

from homeassistant.components.number import NumberEntity, NumberDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, REGISTERS_NUMBER, CONF_DEVICE_ADDRESS

_LOGGER = logging.getLogger(__name__)

# RW registers that should be interpreted as signed int16 (can be negative)
SIGNED_RW_REGISTERS = {
    0x0169, 0x016A, 0x016B, 0x016C,  # E01-E04: Economic heat ambient
    0x016D, 0x016E, 0x016F, 0x0170,  # E05-E08: Economic water ambient
    0x0171, 0x0172, 0x0173, 0x0174,  # E09-E12: Economic cool ambient
    0x0183,  # G07: Hotwater heater external temp
    0x0184,  # G05: Heating heater external temp
    0x0192,  # G10: Ambient temp switch setpoint
}


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
        # Note: NumberDeviceClass doesn't have PRESSURE or FREQUENCY in older HA versions
        # Just set the unit, HA will handle it appropriately
        
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
        # Read from coordinator cache (new format with timestamp)
        cache_entry = self.coordinator.data.get(self._key)
        if cache_entry:
            # Handle new format (dict with value/timestamp)
            if isinstance(cache_entry, dict):
                return cache_entry.get("value")
            # Handle old format (raw float) for backwards compatibility
            return cache_entry
        return None
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success
    
    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        # Use coordinator's write helper (handles cache + timestamp automatically)
        await self.coordinator.async_write_register(
            address=self._address,
            value=value,
            key=self._key,
            scale=(1 / self._scale)  # Convert scale factor for coordinator
        )
        
        # Trigger UI update immediately
        self.async_write_ha_state()
    
    async def async_added_to_hass(self) -> None:
        """When entity is added to hass, read initial value."""
        await super().async_added_to_hass()
        
        # Initial value will be loaded by coordinator on first refresh
        # No need to read directly anymore
    
    async def _async_read_register(self) -> float:
        """Read from Modbus register."""
        # Use coordinator's persistent connection instead of creating a new one
        # This avoids connection conflicts when Elfin max_accept=1
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
            
            # Convert to signed int16 if this is a signed register
            if self._address in SIGNED_RW_REGISTERS:
                if raw_value > 32767:
                    raw_value = raw_value - 65536
            
            scaled_value = raw_value * self._scale
            
            _LOGGER.debug(
                "Read register 0x%04X: raw=%d, scaled=%.2f",
                self._address, raw_value, scaled_value
            )
            
            return scaled_value
        
        return await self.hass.async_add_executor_job(_read)
    
    async def _async_write_register(self, value: float) -> None:
        """Write to Modbus register."""
        # Convert scaled value back to raw register value
        raw_value = int(value / self._scale)
        
        # Convert negative values to unsigned int16 (two's complement) if this is a signed register
        if self._address in SIGNED_RW_REGISTERS and raw_value < 0:
            raw_value = raw_value + 65536
        
        _LOGGER.info(
            "Writing to register 0x%04X: scaled=%.2f, raw=%d",
            self._address, value, raw_value
        )
        
        # Use coordinator's write method to avoid connection conflicts
        await self.hass.async_add_executor_job(
            self.coordinator.write_register,
            self._address,
            raw_value
        )
