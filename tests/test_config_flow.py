"""Unit tests for config_flow.py"""
import pytest
from unittest.mock import MagicMock, patch
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_NAME
from homeassistant.data_entry_flow import FlowResultType

from custom_components.sprsun_modbus.const import DOMAIN, CONF_DEVICE_ADDRESS, CONF_SCAN_INTERVAL


@pytest.mark.asyncio
async def test_config_flow_user_init(hass_mock):
    """Test user-initiated config flow."""
    from custom_components.sprsun_modbus.config_flow import SPRSUNConfigFlow
    
    flow = SPRSUNConfigFlow()
    flow.hass = hass_mock
    
    result = await flow.async_step_user(user_input=None)
    
    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert CONF_HOST in result["data_schema"].schema
    assert CONF_PORT in result["data_schema"].schema


@pytest.mark.asyncio
async def test_config_flow_user_success(hass_mock, mock_modbus_client):
    """Test successful config flow with valid connection."""
    from custom_components.sprsun_modbus.config_flow import SPRSUNConfigFlow
    
    flow = SPRSUNConfigFlow()
    flow.hass = hass_mock
    flow.context = {}  # Initialize mutable context
    flow._abort_if_unique_id_configured = MagicMock()  # Mock to prevent abort
    
    user_input = {
        CONF_NAME: "Test Heat Pump",
        CONF_HOST: "192.168.1.234",
        CONF_PORT: 502,
        CONF_DEVICE_ADDRESS: 1,
        CONF_SCAN_INTERVAL: 10,
    }
    
    with patch("custom_components.sprsun_modbus.config_flow.ModbusTcpClient") as mock:
        client = MagicMock()
        client.connect.return_value = True
        client.connected = True
        
        response = MagicMock()
        response.isError.return_value = False
        response.registers = [100]
        client.read_holding_registers.return_value = response
        
        mock.return_value = client
        
        result = await flow.async_step_user(user_input=user_input)
    
    assert result["type"] == "create_entry"
    assert result["title"] == "Test Heat Pump"
    assert result["data"][CONF_HOST] == "192.168.1.234"


@pytest.mark.asyncio
async def test_config_flow_connection_error(hass_mock):
    """Test config flow with connection error."""
    from custom_components.sprsun_modbus.config_flow import SPRSUNConfigFlow
    
    flow = SPRSUNConfigFlow()
    flow.hass = hass_mock
    
    user_input = {
        CONF_NAME: "Test Heat Pump",
        CONF_HOST: "192.168.1.234",
        CONF_PORT: 502,
        CONF_DEVICE_ADDRESS: 1,
        CONF_SCAN_INTERVAL: 10,
    }
    
    with patch("custom_components.sprsun_modbus.config_flow.ModbusTcpClient") as mock:
        client = MagicMock()
        client.connect.return_value = False
        mock.return_value = client
        
        result = await flow.async_step_user(user_input=user_input)
    
    assert result["type"] == "form"
    assert "errors" in result
    assert "base" in result["errors"]


@pytest.mark.asyncio
async def test_options_flow(hass_mock):
    """Test options flow for updating scan interval."""
    from custom_components.sprsun_modbus.config_flow import SPRSUNOptionsFlowHandler
    
    config_entry = MagicMock()
    config_entry.data = {
        CONF_NAME: "Test",
        CONF_HOST: "192.168.1.234",
        CONF_PORT: 502,
        CONF_DEVICE_ADDRESS: 1,
        CONF_SCAN_INTERVAL: 10,
    }
    
    flow = SPRSUNOptionsFlowHandler(config_entry)
    flow.hass = hass_mock
    
    result = await flow.async_step_init(user_input=None)
    
    assert result["type"] == "form"
    assert result["step_id"] == "init"
    assert CONF_SCAN_INTERVAL in result["data_schema"].schema


@pytest.mark.asyncio
async def test_options_flow_update(hass_mock):
    """Test options flow updates configuration."""
    from custom_components.sprsun_modbus.config_flow import SPRSUNOptionsFlowHandler
    
    config_entry = MagicMock()
    config_entry.entry_id = "test_entry"
    config_entry.data = {
        CONF_NAME: "Test",
        CONF_HOST: "192.168.1.234",
        CONF_PORT: 502,
        CONF_DEVICE_ADDRESS: 1,
        CONF_SCAN_INTERVAL: 10,
    }
    
    # Mock hass.config_entries.async_reload
    async def mock_reload(entry_id):
        pass
    
    hass_mock.config_entries = MagicMock()
    hass_mock.config_entries.async_reload = mock_reload
    
    flow = SPRSUNOptionsFlowHandler(config_entry)
    flow.hass = hass_mock
    
    user_input = {CONF_SCAN_INTERVAL: 20}
    
    result = await flow.async_step_init(user_input=user_input)
    
    assert result["type"] == "create_entry"
