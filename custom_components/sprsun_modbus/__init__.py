"""SPRSUN Heat Pump Modbus Integration."""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
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
)

_LOGGER = logging.getLogger(__name__)

type SPRSUNConfigEntry = ConfigEntry[SPRSUNDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SPRSUN Heat Pump from a config entry."""
    # Allow reading overrides from options if user modified them via options flow
    host = entry.options.get(CONF_HOST, entry.data.get(CONF_HOST))
    port = entry.options.get(CONF_PORT, entry.data.get(CONF_PORT))
    device_address = entry.options.get(CONF_DEVICE_ADDRESS, entry.data.get(CONF_DEVICE_ADDRESS))
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
    controller_type = entry.options.get(CONF_CONTROLLER_TYPE, entry.data.get(CONF_CONTROLLER_TYPE, "chico"))
    
    _LOGGER.info(
        "Setting up SPRSUN Heat Pump (%s controller) at %s:%s (device %s, scan interval %ss)",
        controller_type.upper(), host, port, device_address, scan_interval
    )
    
    coordinator = SPRSUNDataUpdateCoordinator(
        hass, host, port, device_address, scan_interval, controller_type
    )
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    entry.runtime_data = coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register update listener to reload config entry when options change
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        coordinator = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        if coordinator is None and hasattr(entry, "runtime_data"):
            coordinator = entry.runtime_data
        if DOMAIN in hass.data and not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN, None)
        if coordinator and hasattr(coordinator, "async_shutdown"):
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
        
        # Async lock to guarantee atomic, thread-safe access to Modbus connection
        self._lock = asyncio.Lock()
        
        # Modbus client instance (created on demand, closed cleanly on error)
        self.client: ModbusTcpClient | None = None
        
        self.controller_type = controller_type
        self.controller = get_controller(controller_type)
        
        # Cache staleness window: Skip re-reading recently written registers
        self.cache_staleness_seconds = scan_interval * 2
        
        # Polling state:
        # - RW registers are read on initial refresh and refreshed every 20 cycles (~5-10 min)
        # - RO registers (sensors) are read every scan_interval (~150ms batch)
        self._rw_loaded = False
        self._poll_count = 0
        self._rw_refresh_interval = 20
        
        _LOGGER.info(
            "SPRSUN coordinator initialized (%s controller, scan: %ds, cache staleness: %ds)",
            self.controller.name,
            scan_interval,
            self.cache_staleness_seconds
        )
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        
        # Initialize data dictionary
        self.data = {}
    
    def _create_modbus_client(self) -> ModbusTcpClient:
        """Create Modbus TCP client with optimal settings."""
        return ModbusTcpClient(
            host=self.host,
            port=self.port,
            timeout=5.0,  # 5 seconds is plenty for Modbus TCP over LAN
            retries=0,    # We handle retries and reconnects cleanly at coordinator level
        )
    
    def _close_client(self) -> None:
        """Safely close and clean up Modbus client."""
        if self.client is not None:
            try:
                self.client.close()
            except Exception as err:
                _LOGGER.debug("Error closing Modbus client: %s", err)
            finally:
                self.client = None
    
    def _ensure_connection(self) -> bool:
        """Ensure client is connected, creating fresh connection if needed."""
        if self.client is None:
            self.client = self._create_modbus_client()
            
        if not self.client.connected:
            _LOGGER.debug("Connecting Modbus client to %s:%s", self.host, self.port)
            try:
                if self.client.connect():
                    _LOGGER.debug("Modbus client connected successfully to %s:%s", self.host, self.port)
                    return True
                else:
                    _LOGGER.warning("Modbus connection to %s:%s failed", self.host, self.port)
                    self._close_client()
                    return False
            except Exception as err:
                _LOGGER.error("Exception connecting to %s:%s: %s", self.host, self.port, err)
                self._close_client()
                return False
        return True
    
    async def _async_update_data(self):
        """Fetch data from Modbus under mutex lock."""
        async with self._lock:
            try:
                return await self.hass.async_add_executor_job(self._sync_update)
            except (ModbusException, ConnectionError, TimeoutError, OSError, ValueError) as err:
                raise UpdateFailed(f"Error communicating with Modbus: {err}") from err
    
    def _sync_update(self):
        """Synchronous update (runs in executor)."""
        # Determine whether we need to read RW registers in this cycle
        read_rw = (not self._rw_loaded) or (self._poll_count % self._rw_refresh_interval == 0)
        
        fresh_data = None
        # Attempt 1: Using current/ensured connection
        if self._ensure_connection():
            try:
                fresh_data = self.controller.read_all_registers(
                    self.client,
                    self.device_address,
                    initial_read=read_rw
                )
            except Exception as err:
                _LOGGER.warning("Modbus read error: %s. Resetting connection and retrying...", err)
                self._close_client()
        else:
            _LOGGER.warning("Failed to ensure connection to %s:%s. Resetting client...", self.host, self.port)
            self._close_client()
        
        # Attempt 2: If attempt 1 failed, wait 0.5s for gateway, reconnect and retry once
        if fresh_data is None:
            time.sleep(0.5)
            if not self._ensure_connection():
                self._close_client()
                raise UpdateFailed(f"Failed to connect to Modbus device at {self.host}:{self.port}")
            try:
                fresh_data = self.controller.read_all_registers(
                    self.client,
                    self.device_address,
                    initial_read=read_rw
                )
            except Exception as err:
                self._close_client()
                raise UpdateFailed(f"Modbus read failed after reconnect: {err}") from err
        
        if not fresh_data:
            raise UpdateFailed("No data returned from Modbus read")
        
        # If we read RW registers and got setpoints, mark RW as successfully loaded
        if read_rw and "heating_setpoint" in fresh_data:
            self._rw_loaded = True
            _LOGGER.debug("RW parameters successfully loaded and cached")
        
        now = time.time()
        if not isinstance(self.data, dict):
            self.data = {}
            
        updated_data = dict(self.data)
        
        for key, value in fresh_data.items():
            cached = updated_data.get(key)
            if isinstance(cached, dict) and "updated_at" in cached:
                if (now - cached["updated_at"]) < self.cache_staleness_seconds:
                    # Recently written by user, preserve local setpoint
                    continue
            updated_data[key] = {"value": value, "updated_at": now}
        
        self._poll_count += 1
        return updated_data
    
    def _sync_write_register(self, address: int, value: int, key: str, scale: float = 1) -> bool:
        """Write single register synchronously with auto-reconnect."""
        if not self._ensure_connection():
            self._close_client()
            raise ConnectionError(f"Cannot connect to Modbus device at {self.host}:{self.port}")
        
        # Ensure unsigned 16-bit int for Modbus protocol (handles negative signed values like -5°C)
        val_to_write = value & 0xFFFF
        
        result = self.client.write_register(
            address=address,
            value=val_to_write,
            device_id=self.device_address
        )
        
        if result.isError():
            _LOGGER.warning("Write error on 0x%04X: %s. Reconnecting and retrying once...", address, result)
            self._close_client()
            time.sleep(0.5)
            if not self._ensure_connection():
                self._close_client()
                raise ConnectionError(f"Reconnection failed during write to 0x{address:04X}")
            
            result = self.client.write_register(
                address=address,
                value=val_to_write,
                device_id=self.device_address
            )
            if result.isError():
                self._close_client()
                raise ValueError(f"Modbus write error on 0x{address:04X}: {result}")
        
        # Update cache immediately with timestamp
        now = time.time()
        float_val = value / scale if scale != 1 else float(value)
        self.data[key] = {"value": float_val, "updated_at": now}
        _LOGGER.info("Wrote register 0x%04X = %d, cached as %s = %.2f", address, val_to_write, key, float_val)
        return True

    def _sync_write_bit(self, address: int, bit: int, value: bool, reg_key: str | None = None) -> bool:
        """Read-modify-write a bitfield register synchronously."""
        if not self._ensure_connection():
            self._close_client()
            raise ConnectionError(f"Cannot connect to Modbus device at {self.host}:{self.port}")
        
        # Read current register value
        result = self.client.read_holding_registers(
            address=address,
            count=1,
            device_id=self.device_address
        )
        
        if result.isError():
            _LOGGER.warning("Read error before bit-write on 0x%04X: %s. Retrying after reconnect...", address, result)
            self._close_client()
            time.sleep(0.5)
            if not self._ensure_connection():
                self._close_client()
                raise ConnectionError(f"Reconnection failed before bit-write on 0x{address:04X}")
            result = self.client.read_holding_registers(
                address=address,
                count=1,
                device_id=self.device_address
            )
            if result.isError():
                self._close_client()
                raise ValueError(f"Modbus read error on 0x{address:04X}: {result}")
        
        current_val = result.registers[0]
        if value:
            new_val = current_val | (1 << bit)
        else:
            new_val = current_val & ~(1 << bit)
        
        if new_val != current_val:
            w_res = self.client.write_register(
                address=address,
                value=new_val,
                device_id=self.device_address
            )
            if w_res.isError():
                _LOGGER.warning("Bit-write error on 0x%04X: %s. Retrying...", address, w_res)
                self._close_client()
                time.sleep(0.5)
                if not self._ensure_connection():
                    self._close_client()
                    raise ConnectionError(f"Reconnection failed on bit-write to 0x{address:04X}")
                w_res = self.client.write_register(
                    address=address,
                    value=new_val,
                    device_id=self.device_address
                )
                if w_res.isError():
                    self._close_client()
                    raise ValueError(f"Modbus bit-write error on 0x{address:04X}: {w_res}")
        
        # Update cache immediately
        now = time.time()
        if reg_key is None:
            reg_key = f"_control_{address:04x}"
        self.data[reg_key] = {"value": new_val, "updated_at": now}
        _LOGGER.info(
            "Bit %d on register 0x%04X set to %s (was 0x%04X, now 0x%04X)",
            bit, address, value, current_val, new_val
        )
        return True
    
    async def async_write_register(self, address: int, value: float, key: str, scale: float = 1) -> None:
        """Async thread-safe wrapper for register write."""
        int_value = int(value * scale)
        async with self._lock:
            await self.hass.async_add_executor_job(
                self._sync_write_register,
                address,
                int_value,
                key,
                scale
            )
        self.async_set_updated_data(self.data)

    async def async_write_bit(self, address: int, bit: int, value: bool, reg_key: str | None = None) -> None:
        """Async thread-safe wrapper for bit write."""
        async with self._lock:
            await self.hass.async_add_executor_job(
                self._sync_write_bit,
                address,
                bit,
                value,
                reg_key
            )
        self.async_set_updated_data(self.data)

    async def async_shutdown(self):
        """Shutdown coordinator."""
        async with self._lock:
            await self.hass.async_add_executor_job(self._close_client)
