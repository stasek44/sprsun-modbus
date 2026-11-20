"""Unit tests for switch.py."""
import unittest
from unittest.mock import MagicMock, AsyncMock

from tests.conftest import setup_mocks
setup_mocks()

from homeassistant.const import CONF_NAME
from custom_components.sprsun_modbus.const import DOMAIN, REGISTERS_SWITCH
from custom_components.sprsun_modbus.switch import SPRSUNSwitch, async_setup_entry


class TestSPRSUNSwitch(unittest.IsolatedAsyncioTestCase):
    """Test suite for SPRSUN switch entities."""

    def setUp(self):
        """Set up test environment."""
        self.client = MagicMock()
        self.client.connected = True
        
        self.coordinator = MagicMock()
        self.coordinator.client = self.client
        self.coordinator.device_address = 1
        self.coordinator.last_update_success = True
        self.coordinator._ensure_connection = MagicMock(return_value=True)
        self.coordinator.async_write_bit = AsyncMock()
        self.coordinator.data = {
            "_control_0032": {"value": 1, "updated_at": 1000.0},  # Bit 0 = 1 (Power ON)
            "_control_0034": {"value": 2, "updated_at": 1000.0},  # Bit 0 = 0 (Antilegionella OFF), Bit 1 = 1 (Two/Three ON)
        }

        self.hass = MagicMock()
        async def async_add_executor_job(func, *args, **kwargs):
            return func(*args, **kwargs)
        self.hass.async_add_executor_job = async_add_executor_job

        self.config_entry = MagicMock()
        self.config_entry.entry_id = "test_entry_switch"
        self.config_entry.data = {
            CONF_NAME: "SPRSUN Heat Pump",
        }

    async def test_async_setup_entry_creates_switches(self):
        """Test async_setup_entry creates all configured switches."""
        hass = MagicMock()
        hass.data = {DOMAIN: {self.config_entry.entry_id: self.coordinator}}
        async_add_entities = MagicMock()

        await async_setup_entry(hass, self.config_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        self.assertEqual(len(entities), len(REGISTERS_SWITCH))

    def test_switch_attributes(self):
        """Test switch entity naming and unique_id."""
        switch = SPRSUNSwitch(
            self.coordinator,
            self.config_entry,
            "power_switch",
            "Power",
            0x0032,
            0,
        )
        self.assertEqual(switch.name, "SPRSUN Heat Pump Power")
        self.assertEqual(switch.unique_id, "test_entry_switch_power_switch")
        self.assertEqual(switch.device_info["identifiers"], {(DOMAIN, "test_entry_switch")})

    def test_switch_is_on(self):
        """Test switch state reflects bitfield value in cache."""
        power_sw = SPRSUNSwitch(
            self.coordinator, self.config_entry, "power_switch", "Power", 0x0032, 0
        )
        self.assertTrue(power_sw.is_on)

        # Bit 0 of 0x0034 is antilegionella (currently value 2 -> bit 0 is 0)
        legionella_sw = SPRSUNSwitch(
            self.coordinator, self.config_entry, "antilegionella_enable", "Antilegionella", 0x0034, 0
        )
        self.assertFalse(legionella_sw.is_on)

        # Bit 1 of 0x0034 is two_three_function (currently value 2 -> bit 1 is 1)
        two_three_sw = SPRSUNSwitch(
            self.coordinator, self.config_entry, "two_three_function", "Two/Three", 0x0034, 1
        )
        self.assertTrue(two_three_sw.is_on)

    def test_switch_availability(self):
        """Test switch availability depends on coordinator and register cache."""
        switch = SPRSUNSwitch(
            self.coordinator, self.config_entry, "power_switch", "Power", 0x0032, 0
        )
        self.assertTrue(switch.available)

        self.coordinator.last_update_success = False
        self.assertFalse(switch.available)

        self.coordinator.last_update_success = True
        del self.coordinator.data["_control_0032"]
        self.assertFalse(switch.available)

    async def test_switch_turn_on(self):
        """Test turn_on calls coordinator.async_write_bit with True."""
        switch = SPRSUNSwitch(
            self.coordinator, self.config_entry, "antilegionella_enable", "Antilegionella", 0x0034, 0
        )
        switch.hass = self.hass

        await switch.async_turn_on()

        self.coordinator.async_write_bit.assert_called_once_with(
            0x0034, 0, True, reg_key="_control_0034"
        )

    async def test_switch_turn_off(self):
        """Test turn_off calls coordinator.async_write_bit with False."""
        switch = SPRSUNSwitch(
            self.coordinator, self.config_entry, "power_switch", "Power", 0x0032, 0
        )
        switch.hass = self.hass

        await switch.async_turn_off()

        self.coordinator.async_write_bit.assert_called_once_with(
            0x0032, 0, False, reg_key="_control_0032"
        )


if __name__ == "__main__":
    unittest.main()
