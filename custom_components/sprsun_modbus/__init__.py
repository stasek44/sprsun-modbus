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
        # Initialize both clients with keep-alive and longer timeout
        self.read_client = self._create_modbus_client(host, port)
        self.write_client = self._create_modbus_client(host, port)
        
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
    
    def _create_modbus_client(self, host: str, port: int) -> ModbusTcpClient:
        """Create Modbus TCP client with optimal settings."""
        return ModbusTcpClient(
            host=host,
            port=port,
            timeout=10,  # Longer timeout to prevent premature disconnects
            retries=0,    # We handle retries manually
            retry_on_empty=False,
            close_comm_on_error=False,  # Keep connection alive on errors
            strict=False,
        )
    
    def _ensure_connection(self, client: ModbusTcpClient, name: str = "client") -> bool:
        """Ensure client is connected, reconnect if needed."""
        if not client.connected:
            _LOGGER.debug("Reconnecting %s to %s:%s", name, self.host, self.port)
            try:
                if client.connect():
                    # Enable TCP keep-alive on the socket
                    if hasattr(client, 'socket') and client.socket:
                        import socket
                        client.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                        # Linux-specific keep-alive settings
                        if hasattr(socket, 'TCP_KEEPIDLE'):
                            client.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 30)
                            client.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
                            client.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
                    _LOGGER.debug("%s connected successfully", name)
                    return True
                else:
                    _LOGGER.warning("%s connection failed", name)
                    return False
            except Exception as err:
                _LOGGER.error("Exception connecting %s: %s", name, err)
                return False
        return True
    
    async def _async_update_data(self):
        """Fetch data from Modbus."""
        try:
            return await self.hass.async_add_executor_job(self._sync_update)
        except ModbusException as err:
            raise UpdateFailed(f"Error communicating with Modbus: {err}") from err
    
    def _sync_update(self):
        """Synchronous update (runs in executor)."""
        import time
        
        # Ensure read client is connected (Connection #1)
        if not self._ensure_connection(self.read_client, "read_client"):
            raise UpdateFailed("Failed to connect read_client to Modbus device")
        
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
        
        # Ensure write client is connected (Connection #2)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if not self._ensure_connection(self.write_client, "write_client"):
                    if attempt < max_retries - 1:
                        _LOGGER.warning("Write client connection failed (attempt %d/%d), retrying...",
                                       attempt + 1, max_retries)
                        time.sleep(0.5)  # Wait before retry
                        continue
                    raise ConnectionError("Cannot connect to Modbus write device after retries")
                
                # Write via Connection #2
                result = self.write_client.write_register(
                    address=address,
                    value=value,
                    device_id=self.device_address
                )
                
                if result.isError():
                    if attempt < max_retries - 1:
                        _LOGGER.warning("Write error on attempt %d/%d: %s, retrying...", 
                                       attempt + 1, max_retries, result)
                        # Reconnect and retry
                        self.write_client.close()
                        time.sleep(0.5)
                        continue
                    raise ValueError(f"Modbus write error: {result}")
                
                # Success - update cache immediately with timestamp (prevents revert glitch)
                self.data[key] = {
                    "value": value / scale if scale != 1 else float(value),
                    "updated_at": time.time()
                }
                
                _LOGGER.debug(
                    "Wrote register 0x%04X = %d, cached as %s = %.2f (attempt %d)",
                    address, value, key, self.data[key]["value"], attempt + 1
                )
                
                return True
                
            except Exception as err:
                if attempt < max_retries - 1:
                    _LOGGER.warning("Exception on write attempt %d/%d: %s, retrying...", 
                                   attempt + 1, max_retries, err)
                    # Close and reconnect
                    try:
                        self.write_client.close()
                    except:
                        pass
                    time.sleep(0.5)
                else:
                    _LOGGER.error("Failed to write after %d attempts: %s", max_retries, err)
                    raise
        
        raise ConnectionError(f"Failed to write register after {max_retries} attempts")
    
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
