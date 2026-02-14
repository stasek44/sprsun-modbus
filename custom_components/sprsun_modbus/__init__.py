"""SPRSUN Heat Pump Modbus Integration."""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import (
    DOMAIN,
    CONF_DEVICE_ADDRESS,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    PLATFORMS,
    REGISTERS_READ_ONLY,
    REGISTERS_NUMBER,
    REGISTERS_SELECT,
    BINARY_SENSOR_BITS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SPRSUN Heat Pump from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    device_address = entry.data[CONF_DEVICE_ADDRESS]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    
    _LOGGER.info(
        "Setting up SPRSUN Heat Pump at %s:%s (device %s, scan interval %ss)",
        host, port, device_address, scan_interval
    )
    
    coordinator = SPRSUNDataUpdateCoordinator(
        hass, host, port, device_address, scan_interval
    )
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()
    
    return unload_ok


class SPRSUNDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching SPRSUN data from Modbus."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        device_address: int,
        scan_interval: int,
    ) -> None:
        """Initialize."""
        self.host = host
        self.port = port
        self.device_address = device_address
        self.client = None
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
    
    async def _async_update_data(self):
        """Fetch data from Modbus."""
        try:
            return await self.hass.async_add_executor_job(self._sync_update)
        except ModbusException as err:
            raise UpdateFailed(f"Error communicating with Modbus: {err}") from err
    
    def _sync_update(self):
        """Synchronous update (runs in executor)."""
        if self.client is None:
            self.client = ModbusTcpClient(
                host=self.host,
                port=self.port,
                timeout=30,  # Long timeout for safety
            )
        
        if not self.client.connected:
            _LOGGER.debug("Connecting to %s:%s", self.host, self.port)
            if not self.client.connect():
                raise UpdateFailed("Failed to connect to Modbus device")
        
        data = {}
        
        # Registers that should be interpreted as signed int16 (can be negative)
        # Read-Only temperature sensors:
        SIGNED_REGISTERS = {
            0x0011,  # ambient_temp
            0x0015,  # suction_gas_temp
            0x0016,  # coil_temp
            0x0022,  # driving_temp
            0x0028,  # evap_temp
        }
        # Read-Write ambient temperature settings:
        SIGNED_RW_REGISTERS = {
            0x0169, 0x016A, 0x016B, 0x016C,  # E01-E04: Economic heat ambient
            0x016D, 0x016E, 0x016F, 0x0170,  # E05-E08: Economic water ambient
            0x0171, 0x0172, 0x0173, 0x0174,  # E09-E12: Economic cool ambient
            0x0183,  # G07: Hotwater heater external temp
            0x0184,  # G05: Heating heater external temp
            0x0192,  # G10: Ambient temp switch setpoint
        }
        
        # Read all read-only registers in one batch (0x0000-0x0031 = 50 registers)
        try:
            result = self.client.read_holding_registers(
                address=0x0000,
                count=50,
                device_id=self.device_address
            )
            
            if result.isError():
                raise UpdateFailed(f"Modbus read error: {result}")
            
            # Parse read-only registers
            for address, (key, name, scale, unit, device_class) in REGISTERS_READ_ONLY.items():
                index = address - 0x0000
                if index < len(result.registers):
                    raw_value = result.registers[index]
                    
                    # Convert to signed int16 if needed
                    if address in SIGNED_REGISTERS:
                        if raw_value > 32767:
                            raw_value = raw_value - 65536
                    
                    data[key] = raw_value * scale
            
            _LOGGER.debug("Read %d read-only registers successfully", len(data))
            
        except Exception as err:
            _LOGGER.error("Error reading batch registers: %s", err)
            raise UpdateFailed(f"Batch read failed: {err}") from err
        
        # Read status register for binary sensors (R 0x0003)
        try:
            result = self.client.read_holding_registers(
                address=0x0003,
                count=1,
                device_id=self.device_address
            )
            
            if not result.isError() and len(result.registers) == 1:
                data["working_status_register"] = result.registers[0]
            else:
                _LOGGER.warning("Failed to read working status register 0x0003")
                
        except Exception as err:
            _LOGGER.warning("Error reading 0x0003: %s", err)
        
        # Read R/W registers for number and select entities
        # Read them individually since they're scattered across the address space
        rw_addresses = {}
        rw_addresses.update({addr: (*config, 1) for addr, config in REGISTERS_NUMBER.items()})  # scale is third item
        rw_addresses.update({addr: (config[0], config[1], 1, None, None) for addr, config in REGISTERS_SELECT.items()})  # add dummy scale
        
        for address, config in rw_addresses.items():
            key = config[0]
            scale = config[2]
            
            try:
                result = self.client.read_holding_registers(
                    address=address,
                    count=1,
                    device_id=self.device_address
                )
                
                if not result.isError() and len(result.registers) == 1:
                    raw_value = result.registers[0]
                    
                    # Convert to signed int16 if this is an RW temperature register
                    if address in SIGNED_RW_REGISTERS:
                        if raw_value > 32767:
                            raw_value = raw_value - 65536
                    
                    data[key] = raw_value * scale
                    
            except Exception as err:
                _LOGGER.debug("Error reading RW register 0x%04X: %s", address, err)
        
        return data
    
    def write_register(self, address: int, value: int) -> bool:
        """Write a single register (synchronous, runs in executor)."""
        if self.client is None or not self.client.connected:
            if not self.client.connect():
                raise ConnectionError("Cannot connect to Modbus device")
        
        result = self.client.write_register(
            address=address,
            value=value,
            device_id=self.device_address
        )
        
        if result.isError():
            raise ValueError(f"Modbus write error: {result}")
        
        return True
    
    async def async_shutdown(self):
        """Shutdown coordinator."""
        if self.client:
            await self.hass.async_add_executor_job(self.client.close)
            self.client = None
