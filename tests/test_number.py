"""Unit tests for number.py."""
import unittest
from unittest.mock import MagicMock, AsyncMock

from tests.conftest import setup_mocks
setup_mocks()

from homeassistant.const import CONF_NAME, CONF_HOST, CONF_PORT
from custom_components.sprsun_modbus.const import (
    DOMAIN,
    CONF_DEVICE_ADDRESS,
    REGISTERS_NUMBER,
)
from custom_components.sprsun_modbus.number import SPRSUNNumber, async_setup_entry


class TestSPRSUNNumber(unittest.IsolatedAsyncioTestCase):
    """Test suite for SPRSUN number entities."""

    def setUp(self):
        """Set up test environment."""
        self.coordinator = MagicMock()
        self.coordinator.last_update_success = True
        self.coordinator.async_write_register = AsyncMock()
        self.coordinator.data = {
            "heating_setpoint": {"value": 38.5, "updated_at": 1000.0},
            "econ_heat_ambi_1": {"value": -15.0, "updated_at": 1000.0},  # Signed negative
            "temp_diff_heating_cooling": 5,  # Legacy scalar
        }

        self.config_entry = MagicMock()
        self.config_entry.entry_id = "test_entry_num"
        self.config_entry.data = {
            CONF_NAME: "SPRSUN Heat Pump",
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 502,
            CONF_DEVICE_ADDRESS: 1,
        }

    async def test_async_setup_entry_creates_all_numbers(self):
        """Test async_setup_entry creates all 42 number entities."""
        hass = MagicMock()
        hass.data = {DOMAIN: {self.config_entry.entry_id: self.coordinator}}
        async_add_entities = MagicMock()

        await async_setup_entry(hass, self.config_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        self.assertEqual(len(entities), len(REGISTERS_NUMBER))

    def test_number_attributes(self):
        """Test number attributes (min, max, step, units, device_class)."""
        # 0x00CC: ("heating_setpoint", "Heating Setpoint", 0.5, "°C", 10, 55, 0.5, "temperature")
        key, name, scale, unit, min_val, max_val, step, device_class = REGISTERS_NUMBER[0x00CC]
        number = SPRSUNNumber(
            self.coordinator,
            self.config_entry,
            key,
            name,
            0x00CC,
            scale,
            unit,
            min_val,
            max_val,
            step,
            device_class,
        )

        self.assertEqual(number.name, name)
        self.assertTrue(number.has_entity_name)
        self.assertEqual(number.unique_id, "test_entry_num_heating_setpoint")
        self.assertEqual(number._attr_native_min_value, 10)
        self.assertEqual(number._attr_native_max_value, 55)
        self.assertEqual(number._attr_native_step, 0.5)
        self.assertEqual(number.native_unit_of_measurement, "°C")
        self.assertEqual(str(number.device_class), "temperature")

    def test_native_value_extraction(self):
        """Test native_value handles both dict format and legacy scalar format."""
        num_dict = SPRSUNNumber(
            self.coordinator, self.config_entry, "heating_setpoint", "Heating Setpoint",
            0x00CC, 0.5, "°C", 10, 55, 0.5, "temperature"
        )
        self.assertEqual(num_dict.native_value, 38.5)

        num_signed = SPRSUNNumber(
            self.coordinator, self.config_entry, "econ_heat_ambi_1", "Economic Ambient 1",
            0x0169, 1.0, "°C", -30, 50, 1.0, "temperature"
        )
        self.assertEqual(num_signed.native_value, -15.0)

        num_scalar = SPRSUNNumber(
            self.coordinator, self.config_entry, "temp_diff_heating_cooling", "Temp Diff",
            0x00C6, 1.0, "°C", 2, 18, 1.0, "temperature"
        )
        self.assertEqual(num_scalar.native_value, 5)

    def test_availability(self):
        """Test availability reflects coordinator status and data presence."""
        number = SPRSUNNumber(
            self.coordinator, self.config_entry, "heating_setpoint", "Heating Setpoint",
            0x00CC, 0.5, "°C", 10, 55, 0.5, "temperature"
        )
        self.assertTrue(number.available)

        self.coordinator.last_update_success = False
        self.assertFalse(number.available)

        self.coordinator.last_update_success = True
        del self.coordinator.data["heating_setpoint"]
        self.assertFalse(number.available)

    async def test_async_set_native_value(self):
        """Test async_set_native_value converts scale and delegates to coordinator."""
        number = SPRSUNNumber(
            self.coordinator, self.config_entry, "heating_setpoint", "Heating Setpoint",
            0x00CC, 0.5, "°C", 10, 55, 0.5, "temperature"
        )

        await number.async_set_native_value(42.5)

        # Scale for coordinator is 1 / 0.5 = 2.0
        self.coordinator.async_write_register.assert_called_once_with(
            address=0x00CC,
            value=42.5,
            key="heating_setpoint",
            scale=2.0,
        )


if __name__ == "__main__":
    unittest.main()
