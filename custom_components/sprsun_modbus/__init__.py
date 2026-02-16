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
    CONF_CONTROLLER_TYPE,
    DEFAULT_SCAN_INTERVAL,
    PLATFORMS,
    REGISTERS_READ_ONLY,
    REGISTERS_NUMBER,
    REGISTERS_SELECT,
    REGISTERS_SWITCH,
    REGISTERS_BUTTON,
    BINARY_SENSOR_BITS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SPRSUN Heat Pump from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    device_address = entry.data[CONF_DEVICE_ADDRESS]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    controller_type = entry.data.get(CONF_CONTROLLER_TYPE, "chico")  # Default to CHICO for backwards compatibility
    
    _LOGGER.info(
        "Setting up SPRSUN Heat Pump (%s controller) at %s:%s (device %s, scan interval %ss)",
        controller_type.upper(), host, port, device_address, scan_interval
    )
    
    coordinator = SPRSUNDataUpdateCoordinator(
        hass, host, port, device_address, scan_interval, controller_type
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
        controller_type: str,
    ) -> None:
        """Initialize."""
        from .controllers import get_controller
        
        self.host = host
        self.port = port
        self.device_address = device_address
        
        # Dual connection architecture:
        # Connection #1: Read operations (coordinator polling)
        # Connection #2: Write operations (entity writes)
        # Initialize both clients immediately to avoid connection errors
        self.read_client = ModbusTcpClient(host=host, port=port, timeout=5)
        self.write_client = ModbusTcpClient(host=host, port=port, timeout=5)
        
        # Legacy property for backwards compatibility
        self.client = self.read_client
        
        self.controller_type = controller_type
        self.controller = get_controller(controller_type)
        
        # Cache staleness window: Skip re-reading recently written registers
        # Set to 2x scan_interval to prevent revert glitches
        self.cache_staleness_seconds = scan_interval * 2
        
        _LOGGER.info(
            "Using %s controller (cache staleness: %ds)",
            self.controller.name,
            self.cache_staleness_seconds
        )
        
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
        import time
        
        # Connect read client if not connected (Connection #1)
        if not self.read_client.connected:
            _LOGGER.debug("Connecting read client to %s:%s", self.host, self.port)
            if not self.read_client.connect():
                raise UpdateFailed("Failed to connect to Modbus device")
        
        # Use controller-specific implementation to read registers
        try:
            # Read all registers (RO + RW)
            fresh_data = self.controller.read_all_registers(
                self.read_client,
                self.device_address,
                initial_read=True  # Always read RW now
            )
            
            # Phase 2: Migrate to timestamp-based cache
            # Merge fresh data with cache, respecting timestamps
            now = time.time()
            updated_data = {}
            
            for key, value in fresh_data.items():
                # Check if we have a cached entry
                cached = self.data.get(key) if isinstance(self.data, dict) else None
                
                # Handle both old format (float) and new format (dict with timestamp)
                if isinstance(cached, dict) and "updated_at" in cached:
                    # New format: respect timestamp
                    if (now - cached["updated_at"]) < self.cache_staleness_seconds:
                        # Cache is fresh (recently written), preserve it
                        updated_data[key] = cached
                    else:
                        # Cache is stale, use fresh value from device
                        updated_data[key] = {"value": value, "updated_at": now}
                else:
                    # Old format or no cache: use fresh value
                    updated_data[key] = {"value": value, "updated_at": now}
            
            return updated_data
            
        except Exception as err:
            _LOGGER.error("Error reading %s registers: %s", self.controller.name, err)
            raise UpdateFailed(f"Register read failed: {err}") from err
    
    def write_register(self, address: int, value: int) -> bool:
        """Write a single register (synchronous, runs in executor) - LEGACY.
        
        Note: Use write_register_with_cache() for new code.
        """
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
    
    def write_register_with_cache(self, address: int, value: int, key: str, scale: float = 1) -> bool:
        """Write register via dedicated write connection and update cache (Phase 4).
        
        Args:
            address: Modbus register address
            value: Raw integer value to write (already scaled)
            key: Cache key to update
            scale: Scale factor to convert back to float for cache
        
        Returns:
            True if write succeeded
        """
        import time
        
        # Connect write client if not connected (Connection #2)
        if not self.write_client.connected:
            _LOGGER.debug("Connecting write client to %s:%s", self.host, self.port)
            if not self.write_client.connect():
                raise ConnectionError("Cannot connect to Modbus write device")
        
        # Write via Connection #2
        result = self.write_client.write_register(
            address=address,
            value=value,
            device_id=self.device_address
        )
        
        if result.isError():
            raise ValueError(f"Modbus write error: {result}")
        
        # Update cache immediately with timestamp (prevents revert glitch)
        self.data[key] = {
            "value": value / scale if scale != 1 else float(value),
            "updated_at": time.time()
        }
        
        _LOGGER.debug(
            "Wrote register 0x%04X = %d, cached as %s = %.2f",
            address, value, key, self.data[key]["value"]
        )
        
        return True
    
    async def async_write_register(self, address: int, value: float, key: str, scale: float = 1) -> None:
        """Async wrapper for write_register_with_cache (Phase 4).
        
        Args:
            address: Modbus register address
            value: Float value to write (will be scaled)
            key: Cache key to update
            scale: Scale factor (value will be multiplied by this)
        """
        # Convert float to scaled integer
        int_value = int(value * scale)
        
        await self.hass.async_add_executor_job(
            self.write_register_with_cache,
            address,
            int_value,
            key,
            scale
        )
    
    async def async_shutdown(self):
        """Shutdown coordinator."""
        if self.read_client:
            await self.hass.async_add_executor_job(self.read_client.close)
            self.read_client = None
        
        if self.write_client:
            await self.hass.async_add_executor_job(self.write_client.close)
            self.write_client = None
        
        # Clear legacy reference
        self.client = None
