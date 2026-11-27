"""Unit tests for climate.py."""
import unittest
from unittest.mock import MagicMock, AsyncMock, patch

from tests.conftest import setup_mocks
setup_mocks()

from homeassistant.components.climate import (
    HVACMode,
    HVACAction,
    PRESET_NONE,
    PRESET_ECO,
    PRESET_SLEEP,
)
from homeassistant.const import CONF_NAME, ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.exceptions import HomeAssistantError
from custom_components.sprsun_modbus.const import DOMAIN, CONF_TEMP_STEP
from custom_components.sprsun_modbus.climate import (
    SPRSUNClimate,
    SPRSUNDHWClimate,
    async_setup_entry,
)


class TestSPRSUNClimate(unittest.IsolatedAsyncioTestCase):
    """Test suite for SPRSUN climate entities."""

    def setUp(self):
        """Set up test environment."""
        self.coordinator = MagicMock()
        self.coordinator.device_address = 1
        self.coordinator.async_write_register = AsyncMock()
        self.coordinator.async_write_masked_register = AsyncMock()

        def _mock_read_register(address, key=None, scale=1):
            if address == 0x0036 and "unit_mode" in self.coordinator.data:
                return self.coordinator.data["unit_mode"]["value"]
            raise ConnectionError(f"Register 0x{address:04X} unavailable")

        self.coordinator.async_read_register = AsyncMock(side_effect=_mock_read_register)
        self.coordinator.data = {
            "_control_0032": {"value": 1, "updated_at": 1000.0},  # Power ON (bit 0 = 1)
            "unit_mode": {"value": 3, "updated_at": 1000.0},       # Heating + DHW
            "output_symbol_1": {"value": 1, "updated_at": 1000.0}, # Bit 0: Compressor running
            "mode_control_enable": {"value": 0, "updated_at": 1000.0},
            "compressor_running": {"value": True, "updated_at": 1000.0},
            "inlet_temp": {"value": 26.5, "updated_at": 1000.0},
            "outlet_temp": {"value": 32.0, "updated_at": 1000.0},
            "hotwater_temp": {"value": 48.0, "updated_at": 1000.0},
            "heating_setpoint": {"value": 38.0, "updated_at": 1000.0},
            "cooling_setpoint": {"value": 18.0, "updated_at": 1000.0},
            "hotwater_setpoint": {"value": 50.0, "updated_at": 1000.0},
            "fan_mode": {"value": 0, "updated_at": 1000.0},  # Normal
            "working_status_register": {"value": 0b00000001, "updated_at": 1000.0},
        }

        self.config_entry = MagicMock()
        self.config_entry.entry_id = "test_entry_climate"
        self.config_entry.data = {
            CONF_NAME: "SPRSUN Heat Pump",
        }
        self.config_entry.options = {}

        self.climate = SPRSUNClimate(self.coordinator, self.config_entry)
        self.dhw_climate = SPRSUNDHWClimate(self.coordinator, self.config_entry)

    async def test_async_setup_entry_creates_both_climates(self):
        """Test async_setup_entry adds heating/cooling and DHW entities."""
        hass = MagicMock()
        hass.data = {DOMAIN: {self.config_entry.entry_id: self.coordinator}}
        async_add_entities = MagicMock()

        await async_setup_entry(hass, self.config_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        self.assertEqual(len(entities), 2)
        self.assertIsInstance(entities[0], SPRSUNClimate)
        self.assertIsInstance(entities[1], SPRSUNDHWClimate)

    def test_climate_hvac_modes(self):
        """Test HVAC mode logic for heating/cooling entity."""
        # Power ON, unit_mode=3 (Heating + DHW) -> HEAT
        self.assertEqual(self.climate.hvac_mode, HVACMode.HEAT)

        # Unit mode 2 (Cooling) -> COOL
        self.coordinator.data["unit_mode"]["value"] = 2
        self.assertEqual(self.climate.hvac_mode, HVACMode.COOL)

        # Mode control enable = 1 -> HEAT_COOL (auto)
        self.coordinator.data["mode_control_enable"]["value"] = 1
        self.assertEqual(self.climate.hvac_mode, HVACMode.HEAT_COOL)

        # Power OFF (bit 0 of _control_0032 is 0) -> OFF
        self.coordinator.data["_control_0032"]["value"] = 0
        self.assertEqual(self.climate.hvac_mode, HVACMode.OFF)

    def test_climate_hvac_actions(self):
        """Test HVAC action (HEATING, COOLING, IDLE, OFF)."""
        # Power ON, compressor running, heating mode
        self.assertEqual(self.climate.hvac_action, HVACAction.HEATING)

        # Compressor stopped -> IDLE
        self.coordinator.data["output_symbol_1"]["value"] = 0
        self.assertEqual(self.climate.hvac_action, HVACAction.IDLE)

        # Compressor running in cooling mode -> COOLING
        self.coordinator.data["output_symbol_1"]["value"] = 1
        self.coordinator.data["unit_mode"]["value"] = 2
        self.assertEqual(self.climate.hvac_action, HVACAction.COOLING)

        # Power OFF -> OFF
        self.coordinator.data["_control_0032"]["value"] = 0
        self.assertEqual(self.climate.hvac_action, HVACAction.OFF)

    def test_climate_temperatures(self):
        """Test current and target temperature resolution."""
        self.assertEqual(self.climate._attr_native_temperature_unit, UnitOfTemperature.CELSIUS)
        # Current temp is water returning from emitters (inlet_temp)
        self.assertEqual(self.climate.native_current_temperature, 26.5)
        self.assertEqual(self.climate.current_temperature, 26.5)

        # In heating mode, target temp is heating_setpoint
        self.assertEqual(self.climate.native_target_temperature, 38.0)
        self.assertEqual(self.climate.target_temperature, 38.0)

        # In cooling mode, target temp is cooling_setpoint
        self.coordinator.data["unit_mode"]["value"] = 2
        self.assertEqual(self.climate.native_target_temperature, 18.0)
        self.assertEqual(self.climate.target_temperature, 18.0)

    def test_climate_fan_and_preset_modes(self):
        """Test fan mode and preset mode properties map cleanly to P07 without G09 interference."""
        # Fan mode 0 -> normal / PRESET_NONE (even when mode_control_enable == 1)
        self.assertEqual(self.climate.fan_mode, "normal")
        self.assertEqual(self.climate.preset_mode, PRESET_NONE)
        self.coordinator.data["mode_control_enable"]["value"] = 1
        self.assertEqual(self.climate.preset_mode, PRESET_NONE)

        # Fan mode 1 -> eco / PRESET_ECO
        self.coordinator.data["fan_mode"]["value"] = 1
        self.assertEqual(self.climate.fan_mode, "eco")
        self.assertEqual(self.climate.preset_mode, PRESET_ECO)

        # Fan mode 2 -> night / PRESET_SLEEP
        self.coordinator.data["fan_mode"]["value"] = 2
        self.assertEqual(self.climate.fan_mode, "night")
        self.assertEqual(self.climate.preset_mode, PRESET_SLEEP)

        # Fan mode 3 -> test / falls back to PRESET_NONE
        self.coordinator.data["fan_mode"]["value"] = 3
        self.assertEqual(self.climate.fan_mode, "test")
        self.assertEqual(self.climate.preset_mode, PRESET_NONE)

    async def test_async_set_preset_mode(self):
        """Test setting preset mode writes P07 (0x0190) without touching G09."""
        await self.climate.async_set_preset_mode(PRESET_ECO)
        self.coordinator.async_write_register.assert_called_once_with(
            address=0x0190, value=1, key="fan_mode", scale=1
        )

        self.coordinator.async_write_register.reset_mock()
        await self.climate.async_set_preset_mode(PRESET_SLEEP)
        self.coordinator.async_write_register.assert_called_once_with(
            address=0x0190, value=2, key="fan_mode", scale=1
        )

        self.coordinator.async_write_register.reset_mock()
        await self.climate.async_set_preset_mode(PRESET_NONE)
        self.coordinator.async_write_register.assert_called_once_with(
            address=0x0190, value=0, key="fan_mode", scale=1
        )

        self.coordinator.async_write_register.reset_mock()
        await self.climate.async_set_preset_mode("unsupported_preset")
        self.coordinator.async_write_register.assert_not_called()

    async def test_async_set_temperature_heating(self):
        """Test setting temperature in heating mode writes P01 (0x00CC) with 0x00FF mask."""
        self.coordinator.data["unit_mode"]["value"] = 3

        await self.climate.async_set_temperature(**{ATTR_TEMPERATURE: 41.0})

        self.coordinator.async_write_masked_register.assert_called_once_with(
            address=0x00CC,
            raw_value=82,
            mask=0x00FF,
            key="heating_setpoint",
            cached_value=41.0,
        )

    async def test_async_set_temperature_cooling(self):
        """Test setting temperature in cooling mode writes P02 (0x00CB) with 0x00FF mask."""
        self.coordinator.data["unit_mode"]["value"] = 2

        await self.climate.async_set_temperature(**{ATTR_TEMPERATURE: 21.0})

        self.coordinator.async_write_masked_register.assert_called_once_with(
            address=0x00CB,
            raw_value=42,
            mask=0x00FF,
            key="cooling_setpoint",
            cached_value=21.0,
        )

    async def test_async_set_hvac_mode_heat_and_cool(self):
        """Test setting HVAC mode writes unit_mode to 0x0036 and power."""
        self.climate._write_power = AsyncMock()

        # Switch to HEAT
        await self.climate.async_set_hvac_mode(HVACMode.HEAT)
        self.climate._write_power.assert_called_with(True)
        self.coordinator.async_write_register.assert_any_call(
            address=0x0036, value=3, key="unit_mode", scale=1
        )

        # Switch to COOL
        await self.climate.async_set_hvac_mode(HVACMode.COOL)
        self.coordinator.async_write_register.assert_any_call(
            address=0x0036, value=4, key="unit_mode", scale=1
        )

        # Switch to OFF
        await self.climate.async_set_hvac_mode(HVACMode.OFF)
        self.climate._write_power.assert_called_with(False)

    async def test_async_set_fan_mode(self):
        """Test setting fan mode writes P07 (0x0190)."""
        await self.climate.async_set_fan_mode("eco")
        self.coordinator.async_write_register.assert_called_once_with(
            address=0x0190,
            value=1,
            key="fan_mode",
            scale=1,
        )

    def test_dhw_climate_properties(self):
        """Test DHW climate mode, action and temperatures."""
        # Unit mode 3 includes DHW -> HEAT
        self.assertEqual(self.dhw_climate._attr_native_temperature_unit, UnitOfTemperature.CELSIUS)
        self.assertEqual(self.dhw_climate.hvac_mode, HVACMode.HEAT)
        self.assertEqual(self.dhw_climate.native_current_temperature, 48.0)
        self.assertEqual(self.dhw_climate.current_temperature, 48.0)
        self.assertEqual(self.dhw_climate.native_target_temperature, 50.0)
        self.assertEqual(self.dhw_climate.target_temperature, 50.0)

        # Unit mode 1 (Heating only) does NOT include DHW -> OFF
        self.coordinator.data["unit_mode"]["value"] = 1
        self.assertEqual(self.dhw_climate.hvac_mode, HVACMode.OFF)

    async def test_dhw_climate_set_temperature(self):
        """Test setting DHW setpoint writes P04 (0x00CA) with 0x00FF mask."""
        await self.dhw_climate.async_set_temperature(**{ATTR_TEMPERATURE: 52.0})
        self.coordinator.async_write_masked_register.assert_called_once_with(
            address=0x00CA,
            raw_value=104,
            mask=0x00FF,
            key="hotwater_setpoint",
            cached_value=52.0,
        )

    async def test_dhw_climate_set_hvac_mode(self):
        """Test setting DHW HVAC mode switches unit_mode correctly."""
        # When current mode is 1 (Heating only) and DHW turned ON -> mode becomes 3 (Heat+DHW)
        self.coordinator.data["unit_mode"]["value"] = 1
        self.dhw_climate._write_power = AsyncMock()

        await self.dhw_climate.async_set_hvac_mode(HVACMode.HEAT)
        self.dhw_climate._write_power.assert_called_with(True)
        self.coordinator.async_write_register.assert_called_with(
            address=0x0036, value=3, key="unit_mode", scale=1
        )

        # When current mode is 3 (Heat+DHW) and DHW turned OFF -> mode becomes 1 (Heating only)
        self.coordinator.data["unit_mode"]["value"] = 3
        await self.dhw_climate.async_set_hvac_mode(HVACMode.OFF)
        self.coordinator.async_write_register.assert_called_with(
            address=0x0036, value=1, key="unit_mode", scale=1
        )

    def test_temperature_step_default(self):
        """Test default target temperature step and precision is 1.0°C."""
        self.assertEqual(self.climate.target_temperature_step, 1.0)
        self.assertEqual(self.climate.precision, 1.0)
        self.assertEqual(self.dhw_climate.target_temperature_step, 1.0)
        self.assertEqual(self.dhw_climate.precision, 1.0)

    def test_temperature_step_custom_options(self):
        """Test custom target temperature step configured via options."""
        entry = MagicMock()
        entry.entry_id = "custom_step_entry"
        entry.data = {CONF_NAME: "SPRSUN Heat Pump"}
        entry.options = {CONF_TEMP_STEP: 1.0}

        climate = SPRSUNClimate(self.coordinator, entry)
        dhw = SPRSUNDHWClimate(self.coordinator, entry)

        self.assertEqual(climate.target_temperature_step, 1.0)
        self.assertEqual(climate.precision, 1.0)
        self.assertEqual(dhw.target_temperature_step, 1.0)
        self.assertEqual(dhw.precision, 1.0)

    def test_temperature_step_mappingproxy(self):
        """Test target temperature step works with MappingProxyType (as in real Home Assistant)."""
        from types import MappingProxyType

        entry = MagicMock()
        entry.entry_id = "custom_step_mappingproxy"
        entry.data = MappingProxyType({CONF_NAME: "SPRSUN Heat Pump"})
        entry.options = MappingProxyType({CONF_TEMP_STEP: 1.0})

        climate = SPRSUNClimate(self.coordinator, entry)
        dhw = SPRSUNDHWClimate(self.coordinator, entry)

        self.assertEqual(climate.target_temperature_step, 1.0)
        self.assertEqual(climate.precision, 1.0)
        self.assertEqual(dhw.target_temperature_step, 1.0)
        self.assertEqual(dhw.precision, 1.0)

    def test_temperature_step_custom_data(self):
        """Test custom target temperature step configured via initial data."""
        entry = MagicMock()
        entry.entry_id = "custom_step_entry"
        entry.data = {CONF_NAME: "SPRSUN Heat Pump", CONF_TEMP_STEP: 1.0}
        entry.options = {}

        climate = SPRSUNClimate(self.coordinator, entry)
        dhw = SPRSUNDHWClimate(self.coordinator, entry)

        self.assertEqual(climate.target_temperature_step, 1.0)
        self.assertEqual(climate.precision, 1.0)
        self.assertEqual(dhw.target_temperature_step, 1.0)
        self.assertEqual(dhw.precision, 1.0)

    async def test_set_temperature_rounding_with_step_1(self):
        """Test async_set_temperature rounds fractional temperatures when step is 1.0."""
        entry = MagicMock()
        entry.entry_id = "step_1_entry"
        entry.data = {CONF_NAME: "SPRSUN Heat Pump"}
        entry.options = {CONF_TEMP_STEP: 1.0}

        climate = SPRSUNClimate(self.coordinator, entry)
        dhw = SPRSUNDHWClimate(self.coordinator, entry)

        # Space heating setpoint rounding: 28.5 -> 29.0
        await climate.async_set_temperature(**{ATTR_TEMPERATURE: 28.5})
        self.coordinator.async_write_masked_register.assert_called_with(
            address=0x00CC,
            raw_value=58,
            mask=0x00FF,
            key="heating_setpoint",
            cached_value=29.0,
        )

        # DHW setpoint rounding: 48.4 -> 48.0
        await dhw.async_set_temperature(**{ATTR_TEMPERATURE: 48.4})
        self.coordinator.async_write_masked_register.assert_called_with(
            address=0x00CA,
            raw_value=96,
            mask=0x00FF,
            key="hotwater_setpoint",
            cached_value=48.0,
        )

    async def test_set_temperature_half_step_with_step_05(self):
        """Test async_set_temperature preserves 0.5 steps when step is 0.5."""
        entry = MagicMock()
        entry.entry_id = "step_05_entry"
        entry.data = {CONF_NAME: "SPRSUN Heat Pump"}
        entry.options = {CONF_TEMP_STEP: 0.5}
        climate = SPRSUNClimate(self.coordinator, entry)

        await climate.async_set_temperature(**{ATTR_TEMPERATURE: 28.5})
        self.coordinator.async_write_masked_register.assert_called_with(
            address=0x00CC,
            raw_value=57,
            mask=0x00FF,
            key="heating_setpoint",
            cached_value=28.5,
        )

    async def test_async_set_hvac_mode_reads_live_0x0036_when_cache_missing_or_stale(self):
        """Setting Heat/Cool reads live 0x0036 so missing or stale cache cannot disable DHW."""
        self.climate._write_power = AsyncMock()

        # Case 1: unit_mode missing from cache, live device reports 3 (Heating + DHW)
        del self.coordinator.data["unit_mode"]
        self.coordinator.async_read_register = AsyncMock(return_value=3)

        await self.climate.async_set_hvac_mode(HVACMode.HEAT)
        self.coordinator.async_read_register.assert_called_once_with(
            address=0x0036, key="unit_mode", scale=1
        )
        self.coordinator.async_write_register.assert_any_call(
            address=0x0036, value=3, key="unit_mode", scale=1
        )

        # Case 2: cache stale (1), live device reports 3 -> COOL preserves DHW (writes 4)
        self.coordinator.async_write_register.reset_mock()
        self.coordinator.data["unit_mode"] = {"value": 1, "updated_at": 1000.0}
        self.coordinator.async_read_register = AsyncMock(return_value=3)

        await self.climate.async_set_hvac_mode(HVACMode.COOL)
        self.coordinator.async_write_register.assert_any_call(
            address=0x0036, value=4, key="unit_mode", scale=1
        )

    async def test_async_set_dhw_hvac_mode_reads_live_0x0036_when_cache_missing(self):
        """Setting DHW mode reads live 0x0036 instead of defaulting to unit_mode=1."""
        self.dhw_climate._write_power = AsyncMock()
        del self.coordinator.data["unit_mode"]

        # Live unit is Hot Water Only (0): turning DHW Heat ON keeps mode 0 (does NOT write 3)
        self.coordinator.async_read_register = AsyncMock(return_value=0)
        await self.dhw_climate.async_set_hvac_mode(HVACMode.HEAT)
        self.dhw_climate._write_power.assert_called_once_with(True)
        self.coordinator.async_write_register.assert_not_called()

        # Live unit is Cooling Only (2): turning DHW Heat ON writes 4 (Cooling + DHW), not 3
        self.dhw_climate._write_power.reset_mock()
        self.coordinator.async_read_register = AsyncMock(return_value=2)
        await self.dhw_climate.async_set_hvac_mode(HVACMode.HEAT)
        self.coordinator.async_write_register.assert_called_once_with(
            address=0x0036, value=4, key="unit_mode", scale=1
        )

    async def test_async_set_temperature_reads_live_0x0036_when_cache_missing(self):
        """Setting space temperature reads live 0x0036 instead of defaulting to heating."""
        del self.coordinator.data["unit_mode"]
        self.coordinator.async_read_register = AsyncMock(return_value=2)

        await self.climate.async_set_temperature(**{ATTR_TEMPERATURE: 19.0})
        self.coordinator.async_write_masked_register.assert_called_once_with(
            address=0x00CB,
            raw_value=38,
            mask=0x00FF,
            key="cooling_setpoint",
            cached_value=19.0,
        )

        # Hot Water Only (0) keeps legacy fallback to cooling_setpoint when explicitly read as 0
        self.coordinator.async_write_masked_register.reset_mock()
        self.coordinator.async_read_register = AsyncMock(return_value=0)
        await self.climate.async_set_temperature(**{ATTR_TEMPERATURE: 20.0})
        self.coordinator.async_write_masked_register.assert_called_once_with(
            address=0x00CB,
            raw_value=40,
            mask=0x00FF,
            key="cooling_setpoint",
            cached_value=20.0,
        )

    async def test_climate_writes_raise_home_assistant_error_when_0x0036_unavailable(self):
        """Raise HomeAssistantError and perform zero writes if live 0x0036 read fails or is invalid."""
        self.climate._write_power = AsyncMock()
        self.dhw_climate._write_power = AsyncMock()

        for side_effect in (ConnectionError("offline"), None, 99):
            self.coordinator.async_read_register = AsyncMock(side_effect=side_effect) if isinstance(side_effect, Exception) else AsyncMock(return_value=side_effect)
            self.climate._write_power.reset_mock()
            self.dhw_climate._write_power.reset_mock()
            self.coordinator.async_write_register.reset_mock()
            self.coordinator.async_write_masked_register.reset_mock()

            with self.assertRaises(HomeAssistantError):
                await self.climate.async_set_hvac_mode(HVACMode.HEAT)
            with self.assertRaises(HomeAssistantError):
                await self.climate.async_set_hvac_mode(HVACMode.COOL)
            with self.assertRaises(HomeAssistantError):
                await self.climate.async_set_temperature(**{ATTR_TEMPERATURE: 35.0})
            with self.assertRaises(HomeAssistantError):
                await self.dhw_climate.async_set_hvac_mode(HVACMode.HEAT)

            self.climate._write_power.assert_not_called()
            self.dhw_climate._write_power.assert_not_called()
            self.coordinator.async_write_register.assert_not_called()
            self.coordinator.async_write_masked_register.assert_not_called()

    def test_climate_read_properties_return_none_when_unit_mode_or_power_missing(self):
        """Read properties return None instead of fabricating mode/setpoint when cache lacks keys."""
        del self.coordinator.data["unit_mode"]
        self.assertIsNone(self.climate.hvac_mode)
        self.assertIsNone(self.climate.hvac_action)
        self.assertIsNone(self.climate.native_target_temperature)
        self.assertIsNone(self.dhw_climate.hvac_mode)
        self.assertIsNone(self.dhw_climate.hvac_action)

        self.coordinator.data["unit_mode"] = {"value": 3, "updated_at": 1000.0}
        del self.coordinator.data["_control_0032"]
        self.assertIsNone(self.climate.hvac_mode)
        self.assertIsNone(self.climate.hvac_action)
        self.assertIsNone(self.dhw_climate.hvac_mode)
        self.assertIsNone(self.dhw_climate.hvac_action)


if __name__ == "__main__":
    unittest.main()
