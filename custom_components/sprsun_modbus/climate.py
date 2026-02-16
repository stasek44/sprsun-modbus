"""Climate platform for SPRSUN Heat Pump."""
import logging

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
    HVACAction,
    PRESET_NONE,
    PRESET_ECO,
    PRESET_BOOST,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, UnitOfTemperature, ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SPRSUN climate entity."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    async_add_entities([SPRSUNClimate(coordinator, config_entry)])


class SPRSUNClimate(CoordinatorEntity, ClimateEntity):
    """SPRSUN Heat Pump Climate Entity (Hybrid Interface)."""
    
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.PRESET_MODE
    )
    
    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.HEAT,
        HVACMode.COOL,
        HVACMode.HEAT_COOL,  # Auto mode (with G09 enabled)
    ]
    
    _attr_fan_modes = ["normal", "eco", "night", "test"]
    _attr_preset_modes = [PRESET_NONE, PRESET_ECO, PRESET_BOOST]
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 10
    _attr_max_temp = 55
    _attr_target_temperature_step = 0.5
    
    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        
        self._attr_name = f"{config_entry.data[CONF_NAME]} Climate"
        self._attr_unique_id = f"{config_entry.entry_id}_climate"
        
        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": config_entry.data[CONF_NAME],
            "manufacturer": "SPRSUN",
            "model": "Heat Pump",
        }
    
    def _get_cache_value(self, key: str, default=None):
        """Helper to extract value from cache (handles both old and new format)."""
        cache_entry = self.coordinator.data.get(key)
        if cache_entry:
            if isinstance(cache_entry, dict):
                return cache_entry.get("value", default)
            return cache_entry
        return default
    
    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        # Check power switch (bit 0 of register 0x0032)
        power_on = self._get_cache_value("power_switch", False)
        if not power_on:
            return HVACMode.OFF
        
        # Check unit mode (P06: 0=DHW, 1=Heat, 2=Cool, 3=Heat+DHW, 4=Cool+DHW)
        unit_mode = int(self._get_cache_value("unit_mode", 1))
        
        # Check if auto mode is enabled (G09)
        auto_mode = self._get_cache_value("mode_control_enable", 0)
        if auto_mode == 1:
            return HVACMode.HEAT_COOL
        
        # Map unit_mode to hvac_mode
        if unit_mode in [1, 3]:  # Heating or Heating+DHW
            return HVACMode.HEAT
        elif unit_mode in [2, 4]:  # Cooling or Cooling+DHW
            return HVACMode.COOL
        else:  # DHW only (shouldn't happen with power on)
            return HVACMode.OFF
    
    @property
    def hvac_action(self) -> HVACAction:
        """Return current HVAC action."""
        power_on = self._get_cache_value("power_switch", False)
        if not power_on:
            return HVACAction.OFF
        
        # Check if compressor is running
        compressor_running = self._get_cache_value("compressor_running", False)
        if not compressor_running:
            return HVACAction.IDLE
        
        # Check current mode
        unit_mode = int(self._get_cache_value("unit_mode", 1))
        if unit_mode in [1, 3]:  # Heating
            return HVACAction.HEATING
        elif unit_mode in [2, 4]:  # Cooling
            return HVACAction.COOLING
        
        return HVACAction.IDLE
    
    @property
    def current_temperature(self) -> float | None:
        """Return outlet water temperature (what's being delivered)."""
        return self._get_cache_value("outlet_temp")
    
    @property
    def target_temperature(self) -> float | None:
        """Return target temperature based on current mode."""
        unit_mode = int(self._get_cache_value("unit_mode", 1))
        
        if unit_mode in [1, 3]:  # Heating or Heating+DHW
            return self._get_cache_value("heating_setpoint")
        else:  # Cooling
            return self._get_cache_value("cooling_setpoint")
    
    @property
    def fan_mode(self) -> str | None:
        """Return current fan mode (maps to P07)."""
        fan_mode_value = int(self._get_cache_value("fan_mode", 0))
        fan_mode_map = {
            0: "normal",
            1: "eco",
            2: "night",
            3: "test",
        }
        return fan_mode_map.get(fan_mode_value, "normal")
    
    @property
    def preset_mode(self) -> str:
        """Return current preset mode."""
        # Check economic mode enabled
        mode_control = self._get_cache_value("mode_control_enable", 0)
        if mode_control == 1:
            return PRESET_ECO
        
        # Check fan mode for boost
        fan_mode_value = int(self._get_cache_value("fan_mode", 0))
        if fan_mode_value == 0:  # Normal = max capacity
            return PRESET_BOOST
        
        return PRESET_NONE
    
    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode."""
        if hvac_mode == HVACMode.OFF:
            # Turn off power switch (register 0x0032, bit 0)
            await self._write_power(False)
        
        elif hvac_mode == HVACMode.HEAT:
            # Turn on power, set to heating mode
            await self._write_power(True)
            # Disable auto mode
            await self.coordinator.async_write_register(
                address=0x0191, value=0, key="mode_control_enable", scale=1
            )
            # Set unit mode to heating (preserve DHW if currently enabled)
            current_mode = int(self._get_cache_value("unit_mode", 1))
            new_mode = 3 if current_mode in [3, 4] else 1  # Keep +DHW if present
            await self.coordinator.async_write_register(
                address=0x00C6, value=new_mode, key="unit_mode", scale=1
            )
        
        elif hvac_mode == HVACMode.COOL:
            # Turn on power, set to cooling mode
            await self._write_power(True)
            # Disable auto mode
            await self.coordinator.async_write_register(
                address=0x0191, value=0, key="mode_control_enable", scale=1
            )
            # Set unit mode to cooling (preserve DHW if currently enabled)
            current_mode = int(self._get_cache_value("unit_mode", 1))
            new_mode = 4 if current_mode in [3, 4] else 2  # Keep +DHW if present
            await self.coordinator.async_write_register(
                address=0x00C6, value=new_mode, key="unit_mode", scale=1
            )
        
        elif hvac_mode == HVACMode.HEAT_COOL:
            # Turn on power, enable auto mode (G09)
            await self._write_power(True)
            await self.coordinator.async_write_register(
                address=0x0191, value=1, key="mode_control_enable", scale=1
            )
        
        self.async_write_ha_state()
    
    async def async_set_temperature(self, **kwargs) -> None:
        """Set target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        
        # Determine which setpoint to write based on current mode
        unit_mode = int(self._get_cache_value("unit_mode", 1))
        
        if unit_mode in [1, 3]:  # Heating or Heating+DHW
            # Write heating setpoint (P01 at 0x00CC, scale 0.5)
            await self.coordinator.async_write_register(
                address=0x00CC,
                value=temperature,
                key="heating_setpoint",
                scale=2  # 0.5°C scale means multiply by 2
            )
        else:  # Cooling
            # Write cooling setpoint (P02 at 0x00CB, scale 0.5)
            await self.coordinator.async_write_register(
                address=0x00CB,
                value=temperature,
                key="cooling_setpoint",
                scale=2
            )
        
        self.async_write_ha_state()
    
    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set fan mode (P07)."""
        fan_mode_map = {
            "normal": 0,
            "eco": 1,
            "night": 2,
            "test": 3,
        }
        
        value = fan_mode_map.get(fan_mode)
        if value is not None:
            await self.coordinator.async_write_register(
                address=0x018B,  # P07 Fan Mode
                value=value,
                key="fan_mode",
                scale=1
            )
            self.async_write_ha_state()
    
    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set preset mode."""
        if preset_mode == PRESET_ECO:
            # Enable automatic mode control (G09)
            await self.coordinator.async_write_register(
                address=0x0191,
                value=1,
                key="mode_control_enable",
                scale=1
            )
        elif preset_mode == PRESET_BOOST:
            # Set fan mode to normal (max capacity)
            await self.async_set_fan_mode("normal")
        else:  # PRESET_NONE
            # Disable automatic mode control
            await self.coordinator.async_write_register(
                address=0x0191,
                value=0,
                key="mode_control_enable",
                scale=1
            )
        
        self.async_write_ha_state()
    
    async def _write_power(self, state: bool) -> None:
        """Write power switch state (bit 0 of register 0x0032)."""
        import time
        
        def _write():
            client = self.coordinator.write_client
            if client is None:
                from pymodbus.client import ModbusTcpClient
                client = ModbusTcpClient(
                    host=self.coordinator.host,
                    port=self.coordinator.port,
                    timeout=5
                )
                self.coordinator.write_client = client
            
            if not client.connected:
                if not client.connect():
                    raise ConnectionError("Cannot connect to Modbus write device")
            
            # Read current register value
            result = client.read_holding_registers(
                address=0x0032,
                count=1,
                device_id=self.coordinator.device_address
            )
            
            if result.isError():
                raise ValueError(f"Modbus read error: {result}")
            
            current_value = result.registers[0]
            
            # Modify bit 0 (power switch)
            if state:
                new_value = current_value | 1  # Set bit 0
            else:
                new_value = current_value & ~1  # Clear bit 0
            
            # Write back if changed
            if new_value != current_value:
                result = client.write_register(
                    address=0x0032,
                    value=new_value,
                    device_id=self.coordinator.device_address
                )
                
                if result.isError():
                    raise ValueError(f"Modbus write error: {result}")
                
                _LOGGER.info("Set power to %s (register 0x0032: 0x%04X -> 0x%04X)", state, current_value, new_value)
            
            # Update cache with timestamp
            self.coordinator.data["power_switch"] = {
                "value": state,
                "updated_at": time.time()
            }
        
        await self.hass.async_add_executor_job(_write)
