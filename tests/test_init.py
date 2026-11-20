"""Unit tests for integration setup and teardown (__init__.py)."""
import unittest
from unittest.mock import MagicMock, AsyncMock, patch

from tests.conftest import setup_mocks
setup_mocks()

from homeassistant.const import CONF_HOST, CONF_PORT, CONF_NAME
from custom_components.sprsun_modbus.const import (
    DOMAIN,
    CONF_DEVICE_ADDRESS,
    CONF_SCAN_INTERVAL,
    CONF_CONTROLLER_TYPE,
    PLATFORMS,
)
from custom_components.sprsun_modbus import (
    async_setup_entry,
    async_unload_entry,
    SPRSUNDataUpdateCoordinator,
)


class TestIntegrationLifecycle(unittest.IsolatedAsyncioTestCase):
    """Test suite for integration setup and unload lifecycle."""

    def setUp(self):
        """Set up test environment."""
        self.hass = MagicMock()
        self.hass.data = {}
        self.hass.config_entries = MagicMock()
        self.hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
        self.hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

        self.entry = MagicMock()
        self.entry.entry_id = "test_entry_lifecycle"
        self.entry.options = {}
        self.entry.data = {
            CONF_NAME: "SPRSUN Heat Pump",
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 502,
            CONF_DEVICE_ADDRESS: 1,
            CONF_SCAN_INTERVAL: 10,
            CONF_CONTROLLER_TYPE: "chico",
        }

    async def test_async_setup_entry_success(self):
        """Test successful integration setup forwards to all platforms."""
        with patch.object(
            SPRSUNDataUpdateCoordinator,
            "async_config_entry_first_refresh",
            new_callable=AsyncMock
        ) as mock_refresh:
            result = await async_setup_entry(self.hass, self.entry)

            self.assertTrue(result)
            mock_refresh.assert_called_once()
            self.assertIn(DOMAIN, self.hass.data)
            self.assertIn(self.entry.entry_id, self.hass.data[DOMAIN])
            coordinator = self.hass.data[DOMAIN][self.entry.entry_id]
            self.assertIsInstance(coordinator, SPRSUNDataUpdateCoordinator)

            self.hass.config_entries.async_forward_entry_setups.assert_called_once_with(
                self.entry, PLATFORMS
            )

    async def test_async_unload_entry_success(self):
        """Test successful unload shuts down coordinator and unloads platforms."""
        coordinator = MagicMock()
        coordinator.async_shutdown = AsyncMock()
        self.hass.data = {DOMAIN: {self.entry.entry_id: coordinator}}

        result = await async_unload_entry(self.hass, self.entry)

        self.assertTrue(result)
        self.hass.config_entries.async_unload_platforms.assert_called_once_with(
            self.entry, PLATFORMS
        )
        coordinator.async_shutdown.assert_called_once()
        self.assertNotIn(self.entry.entry_id, self.hass.data[DOMAIN])


if __name__ == "__main__":
    unittest.main()
