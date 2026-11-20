"""Unit tests for button.py."""
import unittest
from unittest.mock import MagicMock, AsyncMock

from tests.conftest import setup_mocks
setup_mocks()

from homeassistant.const import CONF_NAME
from custom_components.sprsun_modbus.const import DOMAIN, REGISTERS_BUTTON
from custom_components.sprsun_modbus.button import SPRSUNButton, async_setup_entry


class TestSPRSUNButton(unittest.IsolatedAsyncioTestCase):
    """Test suite for SPRSUN button entities."""

    def setUp(self):
        """Set up test environment."""
        self.coordinator = MagicMock()
        self.coordinator.device_address = 1
        self.coordinator.last_update_success = True
        self.coordinator.async_write_bit = AsyncMock()
        self.coordinator.data = {}

        self.hass = MagicMock()
        self.config_entry = MagicMock()
        self.config_entry.entry_id = "test_entry_btn"
        self.config_entry.data = {
            CONF_NAME: "SPRSUN Heat Pump",
        }

    async def test_async_setup_entry_creates_all_buttons(self):
        """Test async_setup_entry creates all button entities."""
        hass = MagicMock()
        hass.data = {DOMAIN: {self.config_entry.entry_id: self.coordinator}}
        async_add_entities = MagicMock()

        await async_setup_entry(hass, self.config_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        self.assertEqual(len(entities), len(REGISTERS_BUTTON))

    def test_button_attributes(self):
        """Test button naming, description, unique_id and device info."""
        addr, bit, name, desc = REGISTERS_BUTTON["failure_reset"]
        button = SPRSUNButton(
            self.coordinator,
            self.config_entry,
            "failure_reset",
            name,
            addr,
            bit,
            desc,
        )

        self.assertEqual(button.name, name)
        self.assertTrue(button.has_entity_name)
        self.assertEqual(button.unique_id, "test_entry_btn_failure_reset")
        self.assertEqual(button.entity_description.key, "failure_reset")
        self.assertEqual(button.device_info["identifiers"], {(DOMAIN, "test_entry_btn")})
        self.assertTrue(button.available)

    async def test_button_press(self):
        """Test pressing failure reset button calls coordinator.async_write_bit."""
        button = SPRSUNButton(
            self.coordinator,
            self.config_entry,
            "failure_reset",
            "Failure Reset",
            0x0033,
            7,
            "Reset",
        )

        await button.async_press()

        self.coordinator.async_write_bit.assert_called_once_with(0x0033, 7, True)


if __name__ == "__main__":
    unittest.main()
