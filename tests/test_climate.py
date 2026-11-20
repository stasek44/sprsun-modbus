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
    PRESET_BOOST,
)
from homeassistant.const import CONF_NAME, ATTR_TEMPERATURE
from custom_components.sprsun_modbus.const import DOMAIN
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
        # Current temp is water returning from emitters (inlet_temp)
        self.assertEqual(self.climate.current_temperature, 26.5)

        # In heating mode, target temp is heating_setpoint
        self.assertEqual(self.climate.target_temperature, 38.0)

        # In cooling mode, target temp is cooling_setpoint
        self.coordinator.data["unit_mode"]["value"] = 2
        self.assertEqual(self.climate.target_temperature, 18.0)

    def test_climate_fan_and_preset_modes(self):
        """Test fan mode and preset mode properties."""
        # Fan mode 0 -> normal
        self.assertEqual(self.climate.fan_mode, "normal")
        self.assertEqual(self.climate.preset_mode, PRESET_BOOST)

        # Mode control enable 1 -> eco preset
        self.coordinator.data["mode_control_enable"]["value"] = 1
        self.assertEqual(self.climate.preset_mode, PRESET_ECO)

    async def test_async_set_temperature_heating(self):
        """Test setting temperature in heating mode writes P01 (0x00CC)."""
        self.coordinator.data["unit_mode"]["value"] = 3

        await self.climate.async_set_temperature(**{ATTR_TEMPERATURE: 41.5})

        self.coordinator.async_write_register.assert_called_once_with(
            address=0x00CC,
            value=41.5,
            key="heating_setpoint",
            scale=2,
        )

    async def test_async_set_temperature_cooling(self):
        """Test setting temperature in cooling mode writes P02 (0x00CB)."""
        self.coordinator.data["unit_mode"]["value"] = 2

        await self.climate.async_set_temperature(**{ATTR_TEMPERATURE: 21.0})

        self.coordinator.async_write_register.assert_called_once_with(
            address=0x00CB,
            value=21.0,
            key="cooling_setpoint",
            scale=2,
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
        self.assertEqual(self.dhw_climate.hvac_mode, HVACMode.HEAT)
        self.assertEqual(self.dhw_climate.current_temperature, 48.0)
        self.assertEqual(self.dhw_climate.target_temperature, 50.0)

        # Unit mode 1 (Heating only) does NOT include DHW -> OFF
        self.coordinator.data["unit_mode"]["value"] = 1
        self.assertEqual(self.dhw_climate.hvac_mode, HVACMode.OFF)

    async def test_dhw_climate_set_temperature(self):
        """Test setting DHW setpoint writes P04 (0x00CA)."""
        await self.dhw_climate.async_set_temperature(**{ATTR_TEMPERATURE: 52.5})
        self.coordinator.async_write_register.assert_called_once_with(
            address=0x00CA,
            value=52.5,
            key="hotwater_setpoint",
            scale=2,
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


if __name__ == "__main__":
    unittest.main()
