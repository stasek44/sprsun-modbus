"""SPRSUN Heat Pump Modbus Integration."""
from __future__ import annotations

import asyncio
from collections.abc import Callable
import inspect
import json
import logging
from pathlib import Path
import re
import select as sys_select
import socket
import time
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
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
    INTER_WRITE_DELAY,
    PLATFORMS,
)
from .controllers import ControllerBase, get_controller

_LOGGER = logging.getLogger(__name__)

type SPRSUNConfigEntry = ConfigEntry[SPRSUNDataUpdateCoordinator]


def _resolve_platforms(coordinator: Any) -> list[Platform]:
    """Resolve Home Assistant platforms supported by the active controller."""
    controller = getattr(coordinator, "controller", None)
    if isinstance(controller, ControllerBase):
        return [Platform(p) for p in controller.get_platforms()]
    return PLATFORMS


def _read_manifest_version() -> str:
    """Read integration version string from manifest.json."""
    try:
        data = json.loads(Path(__file__).with_name("manifest.json").read_text(encoding="utf-8"))
        return str(data.get("version", ""))
    except Exception:
        return ""


def _is_prerelease_version(version: str) -> bool:
    """Return True for beta/alpha/rc/dev pre-release version strings."""
    lowered = version.strip().lower()
    if any(token in lowered for token in ("alpha", "beta", "dev", "rc")):
        return True
    return bool(re.search(r"\d+(?:a|b|rc)\d*", lowered))


def _configure_prerelease_logging(version: str) -> None:
    """Default package logger level to DEBUG on beta/test pre-release builds."""
    if not _is_prerelease_version(version):
        return
    pkg_logger = logging.getLogger(__package__ or "custom_components.sprsun_modbus")
    if pkg_logger.level in (logging.NOTSET, logging.WARNING):
        pkg_logger.setLevel(logging.DEBUG)
        _LOGGER.debug(
            "Pre-release version %s detected; defaulting integration log level to DEBUG",
            version,
        )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SPRSUN Heat Pump from a config entry."""
    executor = getattr(hass, "async_add_executor_job", None)
    if callable(executor):
        res = executor(_read_manifest_version)
        if inspect.isawaitable(res):
            _configure_prerelease_logging(await res)

    host = entry.options.get(CONF_HOST, entry.data.get(CONF_HOST))
    port = entry.options.get(CONF_PORT, entry.data.get(CONF_PORT))
    device_address = entry.options.get(CONF_DEVICE_ADDRESS, entry.data.get(CONF_DEVICE_ADDRESS))
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
    controller_type = entry.options.get(CONF_CONTROLLER_TYPE, entry.data.get(CONF_CONTROLLER_TYPE, "chico"))

    _LOGGER.info(
        "Setting up SPRSUN Heat Pump (%s controller) at %s:%s (device %s, scan interval %ss)",
        controller_type.upper(),
        host,
        port,
        device_address,
        scan_interval,
    )

    coordinator = SPRSUNDataUpdateCoordinator(
        hass, host, port, device_address, scan_interval, controller_type
    )
    coordinator.config_entry = entry

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    platforms = _resolve_platforms(coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, platforms)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if coordinator is None and hasattr(entry, "runtime_data"):
        coordinator = entry.runtime_data

    platforms = _resolve_platforms(coordinator)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, platforms)

    if unload_ok:
        coordinator = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None) or coordinator
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
        # - RW registers are read on initial refresh and refreshed every 20 cycles
        # - RO registers (sensors) are read every scan_interval
        self._rw_loaded = False
        self._poll_count = 0
        self._rw_refresh_interval = 20

        _LOGGER.info(
            "SPRSUN coordinator initialized (%s controller, scan: %ds, cache staleness: %ds)",
            self.controller.name,
            scan_interval,
            self.cache_staleness_seconds,
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

        self.data = {}

    def _create_modbus_client(self) -> ModbusTcpClient:
        """Create Modbus TCP client with optimal settings."""
        return ModbusTcpClient(
            host=self.host,
            port=self.port,
            timeout=5.0,
            retries=0,
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

    def _is_socket_alive(self) -> bool:
        """Check if client socket is truly open and not closed by remote host."""
        if self.client is None or not getattr(self.client, "connected", False):
            return False
        sock = getattr(self.client, "socket", None)
        if sock is None:
            return True
        try:
            fileno = getattr(sock, "fileno", None)
            if not callable(fileno):
                return True
            fn = fileno()
            if not isinstance(fn, int) or fn < 0:
                return True
            readable, _, exceptional = sys_select.select([sock], [], [sock], 0.0)
            if exceptional:
                return False
            if readable:
                peek = sock.recv(1, socket.MSG_PEEK | socket.MSG_DONTWAIT)
                if not peek:
                    return False
        except (OSError, socket.error):
            return False
        except Exception:
            return True
        return True

    def _ensure_connection(self) -> bool:
        """Ensure client is connected, creating fresh connection if needed."""
        if self.client is not None and getattr(self.client, "connected", False):
            if not self._is_socket_alive():
                _LOGGER.debug("Modbus socket was closed remotely, resetting client")
                self._close_client()

        if self.client is None:
            self.client = self._create_modbus_client()

        if not self.client.connected:
            _LOGGER.debug("Connecting Modbus client to %s:%s", self.host, self.port)
            try:
                if self.client.connect():
                    _LOGGER.debug("Modbus client connected successfully to %s:%s", self.host, self.port)
                    return True
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
        read_rw = (not self._rw_loaded) or (self._poll_count % self._rw_refresh_interval == 0)

        fresh_data = None
        if self._ensure_connection():
            try:
                fresh_data = self.controller.read_all_registers(
                    self.client,
                    self.device_address,
                    initial_read=read_rw,
                )
            except Exception as err:
                _LOGGER.debug("Modbus read attempt 1 failed: %s. Resetting connection and retrying...", err)
                self._close_client()
        else:
            _LOGGER.debug("Failed to ensure connection to %s:%s on attempt 1. Resetting client...", self.host, self.port)
            self._close_client()

        if fresh_data is None:
            time.sleep(0.5)
            if not self._ensure_connection():
                self._close_client()
                raise UpdateFailed(f"Failed to connect to Modbus device at {self.host}:{self.port}")
            try:
                fresh_data = self.controller.read_all_registers(
                    self.client,
                    self.device_address,
                    initial_read=read_rw,
                )
            except Exception as err:
                self._close_client()
                _LOGGER.error("Modbus read failed after reconnect: %s", err)
                raise UpdateFailed(f"Modbus read failed after reconnect: {err}") from err

        if not fresh_data:
            raise UpdateFailed("No data returned from Modbus read")

        if read_rw and self.controller.has_rw_data(fresh_data):
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
                    continue
            updated_data[key] = {"value": value, "updated_at": now}

        self._poll_count += 1
        return updated_data

    def _execute_with_reconnect(self, operation: Callable[[], Any], context: str) -> Any:
        """Execute a synchronous Modbus client operation with one reconnect-and-retry cycle."""
        if not self._ensure_connection():
            self._close_client()
            raise ConnectionError(f"Cannot connect to Modbus device at {self.host}:{self.port}")

        result = operation()
        if result.isError():
            _LOGGER.warning("Modbus error during %s: %s. Reconnecting and retrying once...", context, result)
            self._close_client()
            time.sleep(0.5)
            if not self._ensure_connection():
                self._close_client()
                raise ConnectionError(f"Reconnection failed during {context}")

            result = operation()
            if result.isError():
                self._close_client()
                raise ValueError(f"Modbus error during {context}: {result}")

        return result

    def _sync_write_register(self, address: int, value: int, key: str, scale: float = 1) -> bool:
        """Write single 16-bit holding register synchronously with auto-reconnect."""
        val_to_write = value & 0xFFFF
        self._execute_with_reconnect(
            lambda: self.client.write_register(
                address=address,
                value=val_to_write,
                device_id=self.device_address,
            ),
            f"write to 0x{address:04X}",
        )

        time.sleep(INTER_WRITE_DELAY)

        now = time.time()
        float_val = value / scale if scale != 1 else float(value)
        self.data[key] = {"value": float_val, "updated_at": now}
        _LOGGER.info("Wrote register 0x%04X = %d, cached as %s = %.2f", address, val_to_write, key, float_val)
        return True

    def _sync_write_registers(
        self,
        address: int,
        registers: list[int],
        key: str,
        cached_value: float,
    ) -> bool:
        """Write multiple contiguous holding registers (FC 0x10) with auto-reconnect."""
        vals_to_write = [reg & 0xFFFF for reg in registers]
        self._execute_with_reconnect(
            lambda: self.client.write_registers(
                address=address,
                values=vals_to_write,
                device_id=self.device_address,
            ),
            f"multi-write to 0x{address:04X}",
        )

        time.sleep(INTER_WRITE_DELAY)

        self.data[key] = {"value": cached_value, "updated_at": time.time()}
        _LOGGER.info(
            "Wrote registers 0x%04X (%d words) = %s, cached as %s = %s",
            address,
            len(vals_to_write),
            vals_to_write,
            key,
            cached_value,
        )
        return True

    def _sync_write_bit(self, address: int, bit: int, value: bool, reg_key: str | None = None) -> bool:
        """Read-modify-write a bitfield holding register synchronously."""
        result = self._execute_with_reconnect(
            lambda: self.client.read_holding_registers(
                address=address,
                count=1,
                device_id=self.device_address,
            ),
            f"read before bit-write on 0x{address:04X}",
        )

        current_val = result.registers[0]
        if value:
            new_val = current_val | (1 << bit)
        else:
            new_val = current_val & ~(1 << bit)

        if new_val != current_val:
            self._execute_with_reconnect(
                lambda: self.client.write_register(
                    address=address,
                    value=new_val,
                    device_id=self.device_address,
                ),
                f"bit-write on 0x{address:04X}",
            )

        time.sleep(INTER_WRITE_DELAY)

        now = time.time()
        if reg_key is None:
            reg_key = f"_control_{address:04x}"
        self.data[reg_key] = {"value": new_val, "updated_at": now}
        _LOGGER.info(
            "Bit %d on register 0x%04X set to %s (was 0x%04X, now 0x%04X)",
            bit,
            address,
            value,
            current_val,
            new_val,
        )
        return True

    def _sync_write_coil(self, address: int, value: bool, key: str | None = None) -> bool:
        """Write a single Modbus coil (FC 0x05) synchronously with auto-reconnect."""
        bool_val = bool(value)
        self._execute_with_reconnect(
            lambda: self.client.write_coil(
                address=address,
                value=bool_val,
                device_id=self.device_address,
            ),
            f"coil write to 0x{address:04X}",
        )

        time.sleep(INTER_WRITE_DELAY)

        if key is not None:
            self.data[key] = {"value": bool_val, "updated_at": time.time()}
        _LOGGER.info("Wrote coil 0x%04X = %s (key=%s)", address, bool_val, key)
        return True

    async def async_write_register(self, address: int, value: float, key: str, scale: float = 1) -> None:
        """Async thread-safe wrapper for single holding register write."""
        int_value = int(round(value * scale))
        async with self._lock:
            await self.hass.async_add_executor_job(
                self._sync_write_register,
                address,
                int_value,
                key,
                scale,
            )
        self.async_set_updated_data(self.data)

    async def async_write_registers(
        self,
        address: int,
        registers: list[int],
        key: str,
        value: float,
    ) -> None:
        """Async thread-safe wrapper for multi-register write (FC 0x10)."""
        async with self._lock:
            await self.hass.async_add_executor_job(
                self._sync_write_registers,
                address,
                registers,
                key,
                value,
            )
        self.async_set_updated_data(self.data)

    async def async_write_bit(self, address: int, bit: int, value: bool, reg_key: str | None = None) -> None:
        """Async thread-safe wrapper for bitfield holding register write."""
        async with self._lock:
            await self.hass.async_add_executor_job(
                self._sync_write_bit,
                address,
                bit,
                value,
                reg_key,
            )
        self.async_set_updated_data(self.data)

    async def async_write_coil(self, address: int, value: bool, key: str | None = None) -> None:
        """Async thread-safe wrapper for single coil write (FC 0x05)."""
        async with self._lock:
            await self.hass.async_add_executor_job(
                self._sync_write_coil,
                address,
                value,
                key,
            )
        self.async_set_updated_data(self.data)

    async def async_shutdown(self):
        """Shutdown coordinator."""
        async with self._lock:
            await self.hass.async_add_executor_job(self._close_client)
