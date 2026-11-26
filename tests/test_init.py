"""Unit tests for integration setup and teardown (__init__.py)."""
import unittest
from unittest.mock import MagicMock, AsyncMock, patch

from tests.conftest import setup_mocks
setup_mocks()

from homeassistant.const import CONF_HOST, CONF_PORT, CONF_NAME
from custom_components.sprsun_modbus.const import (
    DOMAIN,
    CONF_DEVICE_ADDRESS,
    CONF_ENABLE_DERIVED_SENSORS,
    CONF_ENABLE_EXPERT_WRITES,
    CONF_SCAN_INTERVAL,
    CONF_CONTROLLER_TYPE,
    PLATFORMS,
)
from custom_components.sprsun_modbus import (
    _configure_prerelease_logging,
    _is_prerelease_version,
    _sync_entity_registry,
    async_setup_entry,
    async_unload_entry,
    SPRSUNDataUpdateCoordinator,
)
from custom_components.sprsun_modbus.controllers.chico import ChicoController


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

    def test_sync_entity_registry_prunes_and_reenables(self):
        """Prune opted-out expert/derived entities and un-disable integration-disabled derived ones."""
        from homeassistant.helpers import entity_registry as er

        ctrl = ChicoController()
        entry_id = self.entry.entry_id

        core_entry = MagicMock(
            domain="sensor",
            unique_id=f"{entry_id}_inlet_temp",
            entity_id="sensor.sprsun_inlet_temp",
            disabled_by=None,
        )
        expert_ro_entry = MagicMock(
            domain="sensor",
            unique_id=f"{entry_id}_h01_defrost_freq",
            entity_id="sensor.sprsun_h01_defrost_freq",
            disabled_by=er.RegistryEntryDisabler.INTEGRATION,
        )
        expert_rw_entry = MagicMock(
            domain="number",
            unique_id=f"{entry_id}_h01_defrost_freq",
            entity_id="number.sprsun_h01_defrost_freq",
            disabled_by=None,
        )
        derived_int_disabled = MagicMock(
            domain="sensor",
            unique_id=f"{entry_id}_water_delta_t",
            entity_id="sensor.sprsun_water_delta_t",
            disabled_by=er.RegistryEntryDisabler.INTEGRATION,
        )
        derived_user_disabled = MagicMock(
            domain="sensor",
            unique_id=f"{entry_id}_estimated_power",
            entity_id="sensor.sprsun_estimated_power",
            disabled_by=er.RegistryEntryDisabler.USER,
        )

        mock_reg = MagicMock()
        all_entries = [
            core_entry,
            expert_ro_entry,
            expert_rw_entry,
            derived_int_disabled,
            derived_user_disabled,
        ]

        # Both flags False: removes expert RO, expert RW, and both derived entities; keeps core
        self.entry.options = {CONF_ENABLE_EXPERT_WRITES: False, CONF_ENABLE_DERIVED_SENSORS: False}
        with (
            patch.object(er, "async_get", return_value=mock_reg),
            patch.object(er, "async_entries_for_config_entry", return_value=all_entries),
        ):
            _sync_entity_registry(self.hass, self.entry, ctrl)
        removed = {call.args[0] for call in mock_reg.async_remove.call_args_list}
        self.assertEqual(
            removed,
            {
                "sensor.sprsun_h01_defrost_freq",
                "number.sprsun_h01_defrost_freq",
                "sensor.sprsun_water_delta_t",
                "sensor.sprsun_estimated_power",
            },
        )
        mock_reg.async_update_entity.assert_not_called()

        # Derived True, Expert True: keeps all, un-disables integration-disabled derived only
        mock_reg.reset_mock()
        self.entry.options = {CONF_ENABLE_EXPERT_WRITES: True, CONF_ENABLE_DERIVED_SENSORS: True}
        with (
            patch.object(er, "async_get", return_value=mock_reg),
            patch.object(er, "async_entries_for_config_entry", return_value=all_entries),
        ):
            _sync_entity_registry(self.hass, self.entry, ctrl)
        mock_reg.async_remove.assert_not_called()
        mock_reg.async_update_entity.assert_called_once_with(
            "sensor.sprsun_water_delta_t", disabled_by=None
        )


if __name__ == "__main__":
    unittest.main()
