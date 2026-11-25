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
    _configure_prerelease_logging,
    _is_prerelease_version,
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
        self.assertNotIn(self.entry.entry_id, self.hass.data.get(DOMAIN, {}))

    def test_prerelease_version_detection_and_default_debug_logging(self):
        """Pre-release/beta builds default logger level to DEBUG while stable builds stay untouched."""
        import logging

        self.assertTrue(_is_prerelease_version("5.2.0b3"))
        self.assertTrue(_is_prerelease_version("5.2.0-beta.2"))
        self.assertTrue(_is_prerelease_version("5.3.0a1"))
        self.assertTrue(_is_prerelease_version("5.3.0rc1"))
        self.assertTrue(_is_prerelease_version("5.3.0dev0"))
        self.assertFalse(_is_prerelease_version("5.2.0"))
        self.assertFalse(_is_prerelease_version("5.1.9"))

        pkg_logger = logging.getLogger("custom_components.sprsun_modbus")
        orig_level = pkg_logger.level
        try:
            pkg_logger.setLevel(logging.WARNING)
            _configure_prerelease_logging("5.2.0")
            self.assertEqual(pkg_logger.level, logging.WARNING)

            _configure_prerelease_logging("5.2.0b3")
            self.assertEqual(pkg_logger.level, logging.DEBUG)

            pkg_logger.setLevel(logging.ERROR)
            _configure_prerelease_logging("5.2.0b3")
            self.assertEqual(pkg_logger.level, logging.ERROR)
        finally:
            pkg_logger.setLevel(orig_level)


if __name__ == "__main__":
    unittest.main()
