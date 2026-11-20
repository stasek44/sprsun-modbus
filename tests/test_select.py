"""Unit tests for select.py."""
import unittest
from unittest.mock import MagicMock, AsyncMock

from tests.conftest import setup_mocks
setup_mocks()

from homeassistant.const import CONF_NAME, CONF_HOST, CONF_PORT
from custom_components.sprsun_modbus.const import (
    DOMAIN,
    CONF_DEVICE_ADDRESS,
    REGISTERS_SELECT,
)
from custom_components.sprsun_modbus.select import SPRSUNSelect, async_setup_entry


class TestSPRSUNSelect(unittest.IsolatedAsyncioTestCase):
    """Test suite for SPRSUN select entities."""

    def setUp(self):
        """Set up test environment."""
        self.coordinator = MagicMock()
        self.coordinator.last_update_success = True
        self.coordinator.async_write_register = AsyncMock()
        self.coordinator.data = {
            "unit_mode": {"value": 3, "updated_at": 1000.0},  # Heating + Hot Water
            "fan_mode": 1,  # Legacy scalar: Economic
            "pump_mode": {"value": 2, "updated_at": 1000.0},  # Demand
        }

        self.config_entry = MagicMock()
        self.config_entry.entry_id = "test_entry_select"
        self.config_entry.data = {
            CONF_NAME: "SPRSUN Heat Pump",
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 502,
            CONF_DEVICE_ADDRESS: 1,
        }

    async def test_async_setup_entry_creates_all_selects(self):
        """Test async_setup_entry creates all select entities."""
        hass = MagicMock()
        hass.data = {DOMAIN: {self.config_entry.entry_id: self.coordinator}}
        async_add_entities = MagicMock()

        await async_setup_entry(hass, self.config_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        self.assertEqual(len(entities), len(REGISTERS_SELECT))

    def test_select_attributes(self):
        """Test select naming, unique_id and options list."""
        key, name, options = REGISTERS_SELECT[0x0036]  # unit_mode
        select = SPRSUNSelect(
            self.coordinator,
            self.config_entry,
            key,
            name,
            0x0036,
            options,
        )

        self.assertEqual(select.name, "SPRSUN Heat Pump Unit Mode")
        self.assertEqual(select.unique_id, "test_entry_select_unit_mode")
        self.assertEqual(len(select.options), 5)
        self.assertIn("Heating + Hot Water", select.options)
        self.assertEqual(select.device_info["identifiers"], {(DOMAIN, "test_entry_select")})

    def test_current_option_resolution(self):
        """Test current_option translates register value to human string."""
        unit_select = SPRSUNSelect(
            self.coordinator, self.config_entry, "unit_mode", "Unit Mode",
            0x0036, REGISTERS_SELECT[0x0036][2]
        )
        self.assertEqual(unit_select.current_option, "Heating + Hot Water")

        fan_select = SPRSUNSelect(
            self.coordinator, self.config_entry, "fan_mode", "Fan Mode",
            0x0190, REGISTERS_SELECT[0x0190][2]
        )
        self.assertEqual(fan_select.current_option, "Economic")

    def test_availability(self):
        """Test select availability depends on coordinator status and key presence."""
        select = SPRSUNSelect(
            self.coordinator, self.config_entry, "unit_mode", "Unit Mode",
            0x0036, REGISTERS_SELECT[0x0036][2]
        )
        self.assertTrue(select.available)

        self.coordinator.last_update_success = False
        self.assertFalse(select.available)

        self.coordinator.last_update_success = True
        del self.coordinator.data["unit_mode"]
        self.assertFalse(select.available)

    async def test_async_select_option(self):
        """Test selecting option writes integer value to coordinator."""
        select = SPRSUNSelect(
            self.coordinator, self.config_entry, "unit_mode", "Unit Mode",
            0x0036, REGISTERS_SELECT[0x0036][2]
        )

        await select.async_select_option("Heating Only")

        # "Heating Only" maps to integer 1
        self.coordinator.async_write_register.assert_called_once_with(
            address=0x0036,
            value=1.0,
            key="unit_mode",
            scale=1,
        )

    async def test_async_select_option_invalid(self):
        """Test selecting invalid option does not write."""
        select = SPRSUNSelect(
            self.coordinator, self.config_entry, "unit_mode", "Unit Mode",
            0x0036, REGISTERS_SELECT[0x0036][2]
        )

        await select.async_select_option("Nonexistent Option")
        self.coordinator.async_write_register.assert_not_called()


if __name__ == "__main__":
    unittest.main()
