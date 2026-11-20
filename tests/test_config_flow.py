"""Unit tests for config_flow.py."""
import unittest
from unittest.mock import MagicMock, patch, AsyncMock

from tests.conftest import setup_mocks
setup_mocks()

from homeassistant.const import CONF_HOST, CONF_PORT, CONF_NAME
from custom_components.sprsun_modbus.const import (
    DOMAIN,
    CONF_DEVICE_ADDRESS,
    CONF_SCAN_INTERVAL,
    CONF_CONTROLLER_TYPE,
)
from custom_components.sprsun_modbus.config_flow import (
    SPRSUNConfigFlow,
    SPRSUNOptionsFlowHandler,
    validate_connection,
)


class TestConfigFlow(unittest.IsolatedAsyncioTestCase):
    """Test suite for config flow and options flow."""

    async def test_validate_connection_success_chico(self):
        """Test validate_connection successfully connects and detects Chico."""
        hass = MagicMock()
        async def async_add_executor_job(func, *args, **kwargs):
            return func(*args, **kwargs)
        hass.async_add_executor_job = async_add_executor_job

        data = {
            CONF_NAME: "SPRSUN Heat Pump",
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 502,
            CONF_DEVICE_ADDRESS: 1,
        }

        with patch("custom_components.sprsun_modbus.config_flow.ModbusTcpClient") as mock_client_cls, \
             patch("custom_components.sprsun_modbus.controllers.detect_controller_type", return_value="chico"):
            client = MagicMock()
            client.connect.return_value = True
            res = MagicMock(isError=lambda: False)
            client.read_holding_registers.return_value = res
            mock_client_cls.return_value = client

            info = await validate_connection(hass, data)
            self.assertEqual(info["title"], "SPRSUN Heat Pump")
            self.assertEqual(info["controller_type"], "chico")
            client.close.assert_called_once()

    async def test_validate_connection_fallback_to_chico_when_detection_none(self):
        """Test validate_connection defaults to chico if auto-detect returns None."""
        hass = MagicMock()
        async def async_add_executor_job(func, *args, **kwargs):
            return func(*args, **kwargs)
        hass.async_add_executor_job = async_add_executor_job

        data = {
            CONF_NAME: "SPRSUN Heat Pump",
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 502,
            CONF_DEVICE_ADDRESS: 1,
        }

        with patch("custom_components.sprsun_modbus.config_flow.ModbusTcpClient") as mock_client_cls, \
             patch("custom_components.sprsun_modbus.controllers.detect_controller_type", return_value=None):
            client = MagicMock()
            client.connect.return_value = True
            client.read_holding_registers.return_value = MagicMock(isError=lambda: False)
            mock_client_cls.return_value = client

            info = await validate_connection(hass, data)
            self.assertEqual(info["controller_type"], "chico")

    async def test_validate_connection_failure_connect(self):
        """Test validate_connection raises ConnectionError when socket fails."""
        hass = MagicMock()
        async def async_add_executor_job(func, *args, **kwargs):
            return func(*args, **kwargs)
        hass.async_add_executor_job = async_add_executor_job

        data = {
            CONF_NAME: "SPRSUN",
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 502,
            CONF_DEVICE_ADDRESS: 1,
        }

        with patch("custom_components.sprsun_modbus.config_flow.ModbusTcpClient") as mock_client_cls:
            client = MagicMock()
            client.connect.return_value = False
            mock_client_cls.return_value = client

            with self.assertRaises(ConnectionError):
                await validate_connection(hass, data)

    async def test_config_flow_user_step_initial_form(self):
        """Test async_step_user displays the initial configuration form."""
        flow = SPRSUNConfigFlow()
        flow.hass = MagicMock()

        result = await flow.async_step_user(user_input=None)
        self.assertEqual(result["type"], "form")
        self.assertEqual(result["step_id"], "user")
        self.assertEqual(result["errors"], {})

    async def test_config_flow_user_step_success(self):
        """Test async_step_user creates config entry on valid input."""
        flow = SPRSUNConfigFlow()
        flow.hass = MagicMock()

        user_input = {
            CONF_NAME: "My Heat Pump",
            CONF_HOST: "192.168.1.150",
            CONF_PORT: 502,
            CONF_DEVICE_ADDRESS: 1,
            CONF_SCAN_INTERVAL: 10,
        }

        with patch("custom_components.sprsun_modbus.config_flow.validate_connection") as mock_val:
            mock_val.return_value = {
                "title": "My Heat Pump",
                "controller_type": "chico",
            }

            result = await flow.async_step_user(user_input=user_input)

            self.assertEqual(result["type"], "create_entry")
            self.assertEqual(result["title"], "My Heat Pump")
            self.assertEqual(result["data"][CONF_CONTROLLER_TYPE], "chico")
            self.assertEqual(result["data"][CONF_HOST], "192.168.1.150")

    async def test_config_flow_user_step_connection_error(self):
        """Test async_step_user sets cannot_connect error on ConnectionError."""
        flow = SPRSUNConfigFlow()
        flow.hass = MagicMock()

        user_input = {
            CONF_NAME: "My Heat Pump",
            CONF_HOST: "192.168.1.150",
            CONF_PORT: 502,
            CONF_DEVICE_ADDRESS: 1,
        }

        with patch("custom_components.sprsun_modbus.config_flow.validate_connection", side_effect=ConnectionError("Cannot connect")):
            result = await flow.async_step_user(user_input=user_input)
            self.assertEqual(result["type"], "form")
            self.assertEqual(result["errors"]["base"], "cannot_connect")

    async def test_config_flow_user_step_unknown_exception(self):
        """Test async_step_user sets unknown error on unexpected exception."""
        flow = SPRSUNConfigFlow()
        flow.hass = MagicMock()

        user_input = {
            CONF_NAME: "My Heat Pump",
            CONF_HOST: "192.168.1.150",
            CONF_PORT: 502,
            CONF_DEVICE_ADDRESS: 1,
        }

        with patch("custom_components.sprsun_modbus.config_flow.validate_connection", side_effect=RuntimeError("Crash")):
            result = await flow.async_step_user(user_input=user_input)
            self.assertEqual(result["type"], "form")
            self.assertEqual(result["errors"]["base"], "unknown")

    async def test_options_flow_init(self):
        """Test options flow shows form with current scan interval."""
        entry = MagicMock()
        entry.data = {
            CONF_SCAN_INTERVAL: 15,
        }

        flow = SPRSUNOptionsFlowHandler(entry)
        flow.hass = MagicMock()

        result = await flow.async_step_init(user_input=None)
        self.assertEqual(result["type"], "form")
        self.assertEqual(result["step_id"], "init")

    async def test_options_flow_update(self):
        """Test options flow updates entry data and reloads."""
        entry = MagicMock()
        entry.entry_id = "test_entry_id"
        entry.data = {
            CONF_NAME: "Pump",
            CONF_SCAN_INTERVAL: 10,
        }

        flow = SPRSUNOptionsFlowHandler(entry)
        flow.hass = MagicMock()
        flow.hass.config_entries.async_reload = AsyncMock()
        flow.hass.config_entries.async_update_entry = MagicMock()

        user_input = {
            CONF_SCAN_INTERVAL: 20,
        }

        result = await flow.async_step_init(user_input=user_input)
        self.assertEqual(result["type"], "create_entry")
        flow.hass.config_entries.async_update_entry.assert_called_once_with(
            entry, data={"name": "Pump", "scan_interval": 20}
        )
        flow.hass.config_entries.async_reload.assert_called_once_with("test_entry_id")


if __name__ == "__main__":
    unittest.main()
