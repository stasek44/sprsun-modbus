"""Config flow for SPRSUN Heat Pump Modbus integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector
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
    CONF_CONTROLLER_TYPE,
    CONF_TEMP_STEP,
    DEFAULT_TEMP_STEP,
)

_LOGGER = logging.getLogger(__name__)


async def validate_connection(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    host = data[CONF_HOST]
    port = data[CONF_PORT]
    device_address = data[CONF_DEVICE_ADDRESS]
    
    def _test_connection_and_detect():
        """Test connection and detect controller type in executor."""
        from .controllers import detect_controller_type
        
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
            
            # Auto-detect controller type
            controller_type = detect_controller_type(client, device_address)
            
            if controller_type is None:
                _LOGGER.warning(
                    "Could not auto-detect controller type, defaulting to CHICO"
                )
                controller_type = "chico"
            
            return controller_type
            
        finally:
            client.close()
    
    try:
        controller_type = await hass.async_add_executor_job(_test_connection_and_detect)
    except Exception as err:
        _LOGGER.error("Connection test failed: %s", err)
        raise ConnectionError(f"Cannot connect: {err}") from err
    
    return {
        "title": data[CONF_NAME],
        "controller_type": controller_type,
    }


def _format_temp_step(val: Any) -> str:
    """Format temperature step to string ("1.0" or "0.5")."""
    try:
        return f"{float(val):.1f}"
    except (ValueError, TypeError):
        return "1.0"


def _temp_step_selector() -> selector.SelectSelector:
    """Return SelectSelector for temperature step."""
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value="1.0", label="1.0°C"),
                selector.SelectOptionDict(value="0.5", label="0.5°C"),
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _device_address_selector() -> selector.NumberSelector:
    """Return NumberSelector for device address (box mode, not slider)."""
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=1,
            max=247,
            step=1,
            mode=selector.NumberSelectorMode.BOX,
        )
    )


def _scan_interval_selector() -> selector.NumberSelector:
    """Return NumberSelector for scan interval (box mode, not slider)."""
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=5,
            max=300,
            step=1,
            unit_of_measurement="s",
            mode=selector.NumberSelectorMode.BOX,
        )
    )


class SPRSUNConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SPRSUN Heat Pump."""
    
    VERSION = 1
    
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            try:
                info = await validate_connection(self.hass, user_input)
                
                # Check if already configured
                await self.async_set_unique_id(
                    f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}_{user_input[CONF_DEVICE_ADDRESS]}"
                )
                self._abort_if_unique_id_configured()
                
                # Add controller type to user input
                user_input[CONF_CONTROLLER_TYPE] = info["controller_type"]
                if CONF_TEMP_STEP in user_input:
                    user_input[CONF_TEMP_STEP] = float(user_input[CONF_TEMP_STEP])
                else:
                    user_input[CONF_TEMP_STEP] = DEFAULT_TEMP_STEP
                
                _LOGGER.info(
                    "Detected %s controller at %s:%s (slave %s)",
                    info["controller_type"].upper(),
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                    user_input[CONF_DEVICE_ADDRESS],
                )
                
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
                vol.Required(
                    CONF_DEVICE_ADDRESS, default=DEFAULT_DEVICE_ADDRESS
                ): _device_address_selector(),
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): _scan_interval_selector(),
                vol.Required(CONF_TEMP_STEP, default="1.0"): _temp_step_selector(),
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
        self._config_entry = config_entry

    @property
    def config_entry(self) -> config_entries.ConfigEntry:
        """Return the config entry."""
        if hasattr(self, "_config_entry") and self._config_entry is not None:
            return self._config_entry
        return super().config_entry
    
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            if CONF_TEMP_STEP in user_input:
                user_input[CONF_TEMP_STEP] = float(user_input[CONF_TEMP_STEP])
            return self.async_create_entry(title="", data=user_input)
        
        temp_step_default = _format_temp_step(
            self.config_entry.options.get(
                CONF_TEMP_STEP,
                self.config_entry.data.get(CONF_TEMP_STEP, DEFAULT_TEMP_STEP),
            )
        )
        
        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_HOST,
                    default=self.config_entry.options.get(
                        CONF_HOST, self.config_entry.data.get(CONF_HOST, "")
                    ),
                ): str,
                vol.Required(
                    CONF_PORT,
                    default=self.config_entry.options.get(
                        CONF_PORT, self.config_entry.data.get(CONF_PORT, DEFAULT_PORT)
                    ),
                ): cv.port,
                vol.Required(
                    CONF_DEVICE_ADDRESS,
                    default=self.config_entry.options.get(
                        CONF_DEVICE_ADDRESS,
                        self.config_entry.data.get(
                            CONF_DEVICE_ADDRESS, DEFAULT_DEVICE_ADDRESS
                        ),
                    ),
                ): _device_address_selector(),
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_SCAN_INTERVAL,
                        self.config_entry.data.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ),
                ): _scan_interval_selector(),
                vol.Required(
                    CONF_TEMP_STEP,
                    default=temp_step_default,
                ): _temp_step_selector(),
            }
        )
        
        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            description_placeholders={
                "elfin_timeout": str(DEFAULT_TIMEOUT),
                "current_interval": str(
                    self.config_entry.options.get(
                        CONF_SCAN_INTERVAL,
                        self.config_entry.data.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    )
                ),
            }
        )
