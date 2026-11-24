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
    CONF_TEMP_STEP,
)
from custom_components.sprsun_modbus.config_flow import (
    SPRSUNConfigFlow,
    SPRSUNOptionsFlowHandler,
    validate_connection,
    _format_temp_step,
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

        self.assertEqual(flow.config_entry, entry)
        self.assertEqual(flow._config_entry, entry)

        result = await flow.async_step_init(user_input=None)
        self.assertEqual(result["type"], "form")
        self.assertEqual(result["step_id"], "init")

    async def test_options_flow_update(self):
        """Test options flow returns create_entry with user options."""
        entry = MagicMock()
        entry.entry_id = "test_entry_id"
        entry.data = {
            CONF_NAME: "Pump",
            CONF_SCAN_INTERVAL: 10,
        }
        entry.options = {}

        flow = SPRSUNOptionsFlowHandler(entry)
        flow.hass = MagicMock()

        user_input = {
            CONF_SCAN_INTERVAL: 20,
            CONF_TEMP_STEP: 1.0,
        }

        result = await flow.async_step_init(user_input=user_input)
        self.assertEqual(result["type"], "create_entry")
        self.assertEqual(result["data"], user_input)

    async def test_config_flow_user_step_with_temp_step(self):
        """Test async_step_user creates config entry with custom temp_step."""
        flow = SPRSUNConfigFlow()
        flow.hass = MagicMock()

        user_input = {
            CONF_NAME: "My Heat Pump 1C",
            CONF_HOST: "192.168.1.155",
            CONF_PORT: 502,
            CONF_DEVICE_ADDRESS: 1,
            CONF_SCAN_INTERVAL: 10,
            CONF_TEMP_STEP: "1.0",
        }

        with patch("custom_components.sprsun_modbus.config_flow.validate_connection") as mock_val:
            mock_val.return_value = {
                "title": "My Heat Pump 1C",
                "controller_type": "chico",
            }

            result = await flow.async_step_user(user_input=user_input)

            self.assertEqual(result["type"], "create_entry")
            self.assertEqual(result["title"], "My Heat Pump 1C")
            self.assertEqual(result["data"][CONF_CONTROLLER_TYPE], "chico")
            self.assertEqual(result["data"][CONF_TEMP_STEP], 1.0)

    def test_format_temp_step(self):
        """Test _format_temp_step formats floats and strings to clean 1-decimal strings."""
        self.assertEqual(_format_temp_step(0.5), "0.5")
        self.assertEqual(_format_temp_step(1.0), "1.0")
        self.assertEqual(_format_temp_step(1), "1.0")
        self.assertEqual(_format_temp_step("0.5"), "0.5")
        self.assertEqual(_format_temp_step("1.0"), "1.0")
        self.assertEqual(_format_temp_step("1"), "1.0")
        self.assertEqual(_format_temp_step(None), "1.0")
        self.assertEqual(_format_temp_step("invalid"), "1.0")

    async def test_options_flow_preserves_saved_temp_step(self):
        """Test options flow form schema has saved temp_step as default."""
        entry = MagicMock()
        entry.entry_id = "test_entry_step"
        entry.data = {CONF_SCAN_INTERVAL: 10}
        entry.options = {CONF_TEMP_STEP: 1.0}

        flow = SPRSUNOptionsFlowHandler(entry)
        flow.hass = MagicMock()

        result = await flow.async_step_init(user_input=None)
        self.assertEqual(result["type"], "form")

        # Verify that temp_step is in schema and default value is "1.0"
        schema_dict = result["data_schema"].schema
        # Find the CONF_TEMP_STEP marker in schema
        step_marker = next(k for k in schema_dict if getattr(k, "schema", None) == CONF_TEMP_STEP or str(k) == CONF_TEMP_STEP)
        self.assertEqual(step_marker.default(), "1.0")

    async def test_options_flow_converts_string_step_to_float(self):
        """Test options flow converts string selector input to float."""
        entry = MagicMock()
        entry.entry_id = "test_entry_step"
        entry.data = {}
        entry.options = {}

        flow = SPRSUNOptionsFlowHandler(entry)
        flow.hass = MagicMock()

        result = await flow.async_step_init(user_input={CONF_TEMP_STEP: "1.0"})
        self.assertEqual(result["type"], "create_entry")
        self.assertEqual(result["data"][CONF_TEMP_STEP], 1.0)
        self.assertIsInstance(result["data"][CONF_TEMP_STEP], float)


if __name__ == "__main__":
    unittest.main()
