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
    """Set up SPRSUN climate entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    # Create two climate entities: one for heating/cooling, one for DHW
    async_add_entities([
        SPRSUNClimate(coordinator, config_entry),
        SPRSUNDHWClimate(coordinator, config_entry),
    ])


class SPRSUNClimate(CoordinatorEntity, ClimateEntity):
    """SPRSUN Heat Pump Climate Entity for Heating/Cooling Control.
    
    HVAC Modes:
    - OFF: Power off (register 0x0032 bit 0 = 0)
    - HEAT: Heating mode (P06 = 1 or 3)
    - COOL: Cooling mode (P06 = 2 or 4)
    - HEAT_COOL: Automatic mode switching based on ambient temp (G09 = 1)
    
    Note: DHW (hot water) control is in separate 'DHW' climate entity.
    """
    
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
        
        self._attr_name = f"{config_entry.data[CONF_NAME]} Heating/Cooling"
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
        # Check power switch (bit 0 of control register 0x0032)
        # Switch entities store register value in _control_XXXX key
        reg_key = "_control_0032"
        reg_cache = self.coordinator.data.get(reg_key)
        if reg_cache:
            if isinstance(reg_cache, dict):
                reg_value = int(reg_cache.get("value", 0))
            else:
                reg_value = int(reg_cache)
            power_on = bool(reg_value & 1)  # bit 0
        else:
            power_on = False
        
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
        # Check power first
        reg_key = "_control_0032"
        reg_cache = self.coordinator.data.get(reg_key)
        if reg_cache:
            if isinstance(reg_cache, dict):
                reg_value = int(reg_cache.get("value", 0))
            else:
                reg_value = int(reg_cache)
            power_on = bool(reg_value & 1)
        else:
            power_on = False
        
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
        """Return inlet water temperature (water returning from heating system)."""
        return self._get_cache_value("inlet_temp")
    
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
            
            # Ensure connection with keep-alive
            self.coordinator._ensure_connection(client, "write_client")
            
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
            
            # Update cache with timestamp using register-based key
            reg_key = "_control_0032"
            self.coordinator.data[reg_key] = {
                "value": new_value,
                "updated_at": time.time()
            }
        
        await self.hass.async_add_executor_job(_write)


class SPRSUNDHWClimate(CoordinatorEntity, ClimateEntity):
    """SPRSUN Heat Pump DHW (Domestic Hot Water) Climate Entity.
    
    Controls hot water heating separately from space heating/cooling.
    
    HVAC Modes:
    - OFF: DHW disabled (P06 doesn't include DHW)
    - HEAT: DHW heating enabled (P06 = 0, 3, or 4)
    
    Unit Mode (P06) values:
    - 0: DHW only
    - 1: Heating only
    - 2: Cooling only
    - 3: Heating + DHW
    - 4: Cooling + DHW
    """
    
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    
    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.HEAT,
    ]
    
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 10
    _attr_max_temp = 55
    _attr_target_temperature_step = 0.5
    
    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the DHW climate entity."""
        super().__init__(coordinator)
        
        self._attr_name = f"{config_entry.data[CONF_NAME]} DHW"
        self._attr_unique_id = f"{config_entry.entry_id}_dhw_climate"
        
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
        """Return current HVAC mode for DHW."""
        # Check power switch
        reg_key = "_control_0032"
        reg_cache = self.coordinator.data.get(reg_key)
        if reg_cache:
            if isinstance(reg_cache, dict):
                reg_value = int(reg_cache.get("value", 0))
            else:
                reg_value = int(reg_cache)
            power_on = bool(reg_value & 1)
        else:
            power_on = False
        
        if not power_on:
            return HVACMode.OFF
        
        # Check if DHW is enabled in unit mode (P06: 0=DHW, 3=Heat+DHW, 4=Cool+DHW)
        unit_mode = int(self._get_cache_value("unit_mode", 1))
        if unit_mode in [0, 3, 4]:  # DHW enabled
            return HVACMode.HEAT
        
        return HVACMode.OFF
    
    @property
    def hvac_action(self) -> HVACAction:
        """Return current HVAC action for DHW."""
        if self.hvac_mode == HVACMode.OFF:
            return HVACAction.OFF
        
        # Check if heating DHW (check working status register for DHW heating)
        # We can infer from unit_mode and compressor status
        compressor_running_cache = self.coordinator.data.get("working_status_register")
        if compressor_running_cache:
            if isinstance(compressor_running_cache, dict):
                status_reg = int(compressor_running_cache.get("value", 0))
            else:
                status_reg = int(compressor_running_cache)
            compressor_running = bool(status_reg & (1 << 0))  # bit 0 = compressor running
        else:
            compressor_running = False
        
        unit_mode = int(self._get_cache_value("unit_mode", 1))
        
        if compressor_running and unit_mode in [0, 3, 4]:
            return HVACAction.HEATING
        
        return HVACAction.IDLE
    
    @property
    def current_temperature(self) -> float | None:
        """Return hot water temperature."""
        return self._get_cache_value("hotwater_temp")
    
    @property
    def target_temperature(self) -> float | None:
        """Return hot water setpoint."""
        return self._get_cache_value("hotwater_setpoint")
    
    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode for DHW."""
        current_mode = int(self._get_cache_value("unit_mode", 1))
        
        if hvac_mode == HVACMode.OFF:
            # Disable DHW in unit mode
            if current_mode == 0:  # DHW only
                # Turn off power
                await self._write_power(False)
            elif current_mode == 3:  # Heat+DHW
                # Switch to heating only
                await self.coordinator.async_write_register(
                    address=0x00C6, value=1, key="unit_mode", scale=1
                )
            elif current_mode == 4:  # Cool+DHW
                # Switch to cooling only
                await self.coordinator.async_write_register(
                    address=0x00C6, value=2, key="unit_mode", scale=1
                )
        
        elif hvac_mode == HVACMode.HEAT:
            # Enable DHW in unit mode
            await self._write_power(True)
            
            if current_mode == 1:  # Heating only
                # Switch to Heat+DHW
                await self.coordinator.async_write_register(
                    address=0x00C6, value=3, key="unit_mode", scale=1
                )
            elif current_mode == 2:  # Cooling only
                # Switch to Cool+DHW
                await self.coordinator.async_write_register(
                    address=0x00C6, value=4, key="unit_mode", scale=1
                )
            elif current_mode in [0, 3, 4]:
                # DHW already enabled, just ensure power is on
                pass
            else:
                # Default: DHW only
                await self.coordinator.async_write_register(
                    address=0x00C6, value=0, key="unit_mode", scale=1
                )
        
        self.async_write_ha_state()
    
    async def async_set_temperature(self, **kwargs) -> None:
        """Set hot water target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        
        # Write hot water setpoint (P04 at 0x00CA, scale 0.5)
        await self.coordinator.async_write_register(
            address=0x00CA,
            value=temperature,
            key="hotwater_setpoint",
            scale=2  # 0.5°C scale means multiply by 2
        )
        
        self.async_write_ha_state()
    
    async def _write_power(self, state: bool) -> None:
        """Write power switch state (bit 0 of register 0x0032)."""
        import time
        
        def _write():
            client = self.coordinator.write_client
            
            # Ensure connection with keep-alive
            self.coordinator._ensure_connection(client, "write_client")
            
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
                
                _LOGGER.info("Set DHW power to %s (register 0x0032: 0x%04X -> 0x%04X)", state, current_value, new_value)
            
            # Update cache with timestamp using register-based key
            reg_key = "_control_0032"
            self.coordinator.data[reg_key] = {
                "value": new_value,
                "updated_at": time.time()
            }
        
        await self.hass.async_add_executor_job(_write)
