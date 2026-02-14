"""Config flow for SPRSUN Heat Pump Modbus integration."""
import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from pymodbus.client import ModbusTcpClient

from .const import (
    DOMAIN,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_DEVICE_ADDRESS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    CONF_DEVICE_ADDRESS,
    CONF_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


async def validate_connection(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    host = data[CONF_HOST]
    port = data[CONF_PORT]
    device_address = data[CONF_DEVICE_ADDRESS]
    
    def _test_connection():
        """Test connection in executor."""
        client = ModbusTcpClient(host=host, port=port, timeout=5)
        try:
            if not client.connect():
                raise ConnectionError("Cannot connect to Modbus device")
            
            # Try to read first register as test
            result = client.read_holding_registers(
                address=0x0000,
                count=1,
                device_id=device_address
            )
            
            if result.isError():
                raise ConnectionError(f"Modbus read error: {result}")
            
            return True
            
        finally:
            client.close()
    
    try:
        await hass.async_add_executor_job(_test_connection)
    except Exception as err:
        _LOGGER.error("Connection test failed: %s", err)
        raise ConnectionError(f"Cannot connect: {err}") from err
    
    return {"title": data[CONF_NAME]}


class SPRSUNConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SPRSUN Heat Pump."""
    
    VERSION = 1
    
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            try:
                info = await validate_connection(self.hass, user_input)
                
                # Check if already configured
                await self.async_set_unique_id(
                    f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                )
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(title=info["title"], data=user_input)
                
            except ConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
        
        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
                vol.Required(CONF_DEVICE_ADDRESS, default=DEFAULT_DEVICE_ADDRESS): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=247)
                ),
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=5, max=300)
                ),
            }
        )
        
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "elfin_timeout": str(DEFAULT_TIMEOUT),
                "recommended_scan": str(DEFAULT_SCAN_INTERVAL),
            }
        )
    
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return SPRSUNOptionsFlowHandler(config_entry)


class SPRSUNOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for SPRSUN Heat Pump."""
    
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
    
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Update config entry data (not options, for simplicity)
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={**self.config_entry.data, **user_input}
            )
            # Reload the integration to apply changes
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            return self.async_create_entry(title="", data={})
        
        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.data.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=300)),
            }
        )
        
        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            description_placeholders={
                "elfin_timeout": str(DEFAULT_TIMEOUT),
                "current_interval": str(self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)),
            }
        )
