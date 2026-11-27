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
    is_derived_sensors_enabled,
    is_expert_writes_enabled,
)
from .controllers import ControllerBase, get_controller
from .dashboard import async_register_dashboard

_LOGGER = logging.getLogger(__name__)

MAX_BACKOFF_SECONDS = 300

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


def _sync_entity_registry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    controller: ControllerBase,
) -> None:
    """Prune opted-out expert/derived entities and un-disable integration-disabled derived ones."""
    try:
        from homeassistant.helpers import entity_registry as er

        ent_reg = er.async_get(hass)
        entries = er.async_entries_for_config_entry(ent_reg, entry.entry_id)
        if not isinstance(entries, (list, tuple)):
            return
    except Exception:
        return

    expert_enabled = is_expert_writes_enabled(entry)
    derived_enabled = is_derived_sensors_enabled(entry)
    prefix = f"{entry.entry_id}_"

    expert_ids: set[tuple[str, str]] = (
        {("sensor", f"{prefix}{s.key}") for s in controller.get_expert_sensors()}
        | {("binary_sensor", f"{prefix}{s.key}") for s in controller.get_expert_binary_sensors()}
        | {("number", f"{prefix}{s.key}") for s in controller.get_expert_numbers()}
        | {("select", f"{prefix}{s.key}") for s in controller.get_expert_selects()}
        | {("switch", f"{prefix}{s.key}") for s in controller.get_expert_switches()}
    )
    derived_ids: set[tuple[str, str]] = {
        ("sensor", f"{prefix}{s.key}") for s in controller.get_derived_sensors()
    }

    disabler_enum = getattr(er, "RegistryEntryDisabler", None)
    integration_disabler = getattr(disabler_enum, "INTEGRATION", "integration")

    for reg_entry in list(entries):
        identity = (reg_entry.domain, reg_entry.unique_id)
        if not expert_enabled and identity in expert_ids:
            ent_reg.async_remove(reg_entry.entity_id)
        elif not derived_enabled and identity in derived_ids:
            ent_reg.async_remove(reg_entry.entity_id)
        elif (
            derived_enabled
            and identity in derived_ids
            and reg_entry.disabled_by == integration_disabler
        ):
            ent_reg.async_update_entity(reg_entry.entity_id, disabled_by=None)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SPRSUN Heat Pump from a config entry."""
    manifest_version = ""
    executor = getattr(hass, "async_add_executor_job", None)
    if callable(executor):
        res = executor(_read_manifest_version)
        if inspect.isawaitable(res):
            manifest_version = str(await res or "")
            _configure_prerelease_logging(manifest_version)

    host = entry.options.get(CONF_HOST, entry.data.get(CONF_HOST))
    port = int(entry.options.get(CONF_PORT, entry.data.get(CONF_PORT)))
    device_address = int(
        entry.options.get(CONF_DEVICE_ADDRESS, entry.data.get(CONF_DEVICE_ADDRESS))
    )
    scan_interval = int(
        entry.options.get(
            CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )
    )
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

    await coordinator.async_init_derived_store(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    _sync_entity_registry(hass, entry, coordinator.controller)

    platforms = _resolve_platforms(coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, platforms)

    await async_register_dashboard(hass, manifest_version)

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
        self.port = int(port)
        self.device_address = int(device_address)
        scan_interval = int(scan_interval)
        self._base_scan_interval = scan_interval
        self._max_backoff_seconds = max(MAX_BACKOFF_SECONDS, scan_interval)
        self._consecutive_failures = 0

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
        self._derived_store: Any = None
        self._last_derived_save_ts: float = 0.0
        self._last_derived_signature: Any = None

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

    def _record_poll_success(self) -> None:
        """Reset consecutive failure counter and restore base scan interval."""
        if self._consecutive_failures > 0:
            _LOGGER.info(
                "Modbus communication recovered after %d failed poll(s); restoring scan interval to %ds",
                self._consecutive_failures,
                self._base_scan_interval,
            )
        self._consecutive_failures = 0
        self.update_interval = timedelta(seconds=self._base_scan_interval)

    def _record_poll_failure(self, err: Exception) -> None:
        """Increment failure counter and apply exponential backoff to update_interval."""
        self._consecutive_failures += 1
        backoff_seconds = min(
            self._max_backoff_seconds,
            self._base_scan_interval * (2 ** self._consecutive_failures),
        )
        self.update_interval = timedelta(seconds=backoff_seconds)
        if self._consecutive_failures == 1:
            _LOGGER.warning(
                "Modbus poll failed (%s); backing off next poll to %ds",
                err,
                backoff_seconds,
            )
        else:
            _LOGGER.debug(
                "Modbus poll failure #%d (%s); next poll in %ds",
                self._consecutive_failures,
                err,
                backoff_seconds,
            )

    async def _async_update_data(self):
        """Fetch data from Modbus under mutex lock."""
        async with self._lock:
            try:
                data = await self.hass.async_add_executor_job(self._sync_update)
            except UpdateFailed as err:
                self._record_poll_failure(err)
                raise
            except (ModbusException, ConnectionError, TimeoutError, OSError, ValueError) as err:
                self._record_poll_failure(err)
                raise UpdateFailed(f"Error communicating with Modbus: {err}") from err
            self._record_poll_success()
            self._schedule_derived_state_save()
            return data

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

        self._apply_derived_data(updated_data, now)
        self._poll_count += 1
        return updated_data

    def _apply_derived_data(self, target_data: dict[str, Any], now: float) -> None:
        """Compute and merge controller-derived sensor values into coordinator data."""
        compute_fn = getattr(self.controller, "compute_derived_data", None)
        if not callable(compute_fn):
            return
        derived_specs = self.controller.get_derived_sensors() if hasattr(self.controller, "get_derived_sensors") else ()
        derived_values = compute_fn(target_data, now) or {}
        for spec in derived_specs:
            val = derived_values.get(spec.key)
            if val is not None:
                target_data[spec.key] = {"value": val, "updated_at": now}
            else:
                target_data.pop(spec.key, None)

    def _notify_updated_data(self) -> None:
        """Recompute derived data after a write and notify listeners."""
        if isinstance(self.data, dict):
            self._apply_derived_data(self.data, time.time())
        self.async_set_updated_data(self.data)

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

    def _sync_read_register(
        self,
        address: int,
        key: str | None = None,
        scale: float = 1,
    ) -> int | float:
        """Read a single 16-bit holding register synchronously with auto-reconnect."""
        result = self._execute_with_reconnect(
            lambda: self.client.read_holding_registers(
                address=address,
                count=1,
                device_id=self.device_address,
            ),
            f"read of 0x{address:04X}",
        )
        regs = getattr(result, "registers", None)
        if not regs:
            raise ValueError(f"Empty register response reading 0x{address:04X}")

        raw_value = int(regs[0])
        value: int | float = raw_value / scale if scale != 1 else raw_value
        if key is not None:
            if not isinstance(self.data, dict):
                self.data = {}
            self.data[key] = {"value": value, "updated_at": time.time()}
        return value

    def _sync_write_register(
        self,
        address: int,
        value: int,
        key: str,
        scale: float = 1,
        cached_value: float | None = None,
    ) -> bool:
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
        if cached_value is not None:
            float_val = float(cached_value)
        else:
            float_val = value / scale if scale != 1 else float(value)
        self.data[key] = {"value": float_val, "updated_at": now}
        _LOGGER.info("Wrote register 0x%04X = %d, cached as %s = %.2f", address, val_to_write, key, float_val)
        return True

    def _sync_write_masked_register(
        self,
        address: int,
        raw_value: int,
        mask: int,
        key: str,
        cached_value: float,
    ) -> bool:
        """Read-modify-write selected bits of a holding register while preserving other bits."""
        result = self._execute_with_reconnect(
            lambda: self.client.read_holding_registers(
                address=address,
                count=1,
                device_id=self.device_address,
            ),
            f"read before masked write on 0x{address:04X}",
        )
        current_val = result.registers[0]
        new_val = (current_val & ~mask) | (raw_value & mask)

        if new_val != current_val:
            self._execute_with_reconnect(
                lambda: self.client.write_register(
                    address=address,
                    value=new_val & 0xFFFF,
                    device_id=self.device_address,
                ),
                f"masked write to 0x{address:04X}",
            )

        time.sleep(INTER_WRITE_DELAY)

        self.data[key] = {"value": float(cached_value), "updated_at": time.time()}
        _LOGGER.info(
            "Masked write on 0x%04X (mask=0x%04X): was 0x%04X, now 0x%04X, cached as %s = %.2f",
            address,
            mask,
            current_val,
            new_val,
            key,
            float(cached_value),
        )
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

    async def async_read_register(
        self,
        address: int,
        key: str | None = None,
        scale: float = 1,
    ) -> int | float:
        """Async thread-safe wrapper for single holding register read."""
        async with self._lock:
            return await self.hass.async_add_executor_job(
                self._sync_read_register,
                address,
                key,
                scale,
            )

    async def async_write_register(
        self,
        address: int,
        value: float,
        key: str,
        scale: float = 1,
        cached_value: float | None = None,
    ) -> None:
        """Async thread-safe wrapper for single holding register write."""
        int_value = int(round(value * scale))
        async with self._lock:
            await self.hass.async_add_executor_job(
                self._sync_write_register,
                address,
                int_value,
                key,
                scale,
                cached_value,
            )
        self._notify_updated_data()

    async def async_write_masked_register(
        self,
        address: int,
        raw_value: int,
        mask: int,
        key: str,
        cached_value: float,
    ) -> None:
        """Async thread-safe wrapper for read-modify-write masked holding register writes."""
        async with self._lock:
            await self.hass.async_add_executor_job(
                self._sync_write_masked_register,
                address,
                raw_value,
                mask,
                key,
                cached_value,
            )
        self._notify_updated_data()

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
        self._notify_updated_data()

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
        self._notify_updated_data()

    async def async_write_coil(self, address: int, value: bool, key: str | None = None) -> None:
        """Async thread-safe wrapper for single coil write (FC 0x05)."""
        async with self._lock:
            await self.hass.async_add_executor_job(
                self._sync_write_coil,
                address,
                value,
                key,
            )
        self._notify_updated_data()

    async def async_init_derived_store(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Load persisted rolling 24h derived-sensor intervals when derived sensors are enabled."""
        if not is_derived_sensors_enabled(entry):
            return
        try:
            from homeassistant.helpers import storage as ha_storage

            store_cls = getattr(ha_storage, "Store", None)
            if not callable(store_cls):
                return
            store = store_cls(hass, 1, f"{DOMAIN}.derived_{entry.entry_id}")
            self._derived_store = store
            res = store.async_load()
            loaded = await res if inspect.isawaitable(res) else res
            if isinstance(loaded, dict):
                restore_fn = getattr(self.controller, "restore_derived_state", None)
                if callable(restore_fn):
                    restore_fn(loaded, time.time())
        except Exception as err:
            _LOGGER.debug("Skipping derived state restore: %s", err)

    def _schedule_derived_state_save(self) -> None:
        """Schedule debounced persistence of rolling 24h derived state on the event loop."""
        if self._derived_store is None or not hasattr(self._derived_store, "async_delay_save"):
            return
        export_fn = getattr(self.controller, "export_derived_state", None)
        if not callable(export_fn):
            return
        now = time.time()
        state = export_fn(now)
        if not isinstance(state, dict):
            return
        signature = tuple(
            (
                key,
                len(val.get("intervals", [])) if isinstance(val, dict) else 0,
                val.get("active_start") if isinstance(val, dict) else None,
            )
            for key, val in sorted(state.items())
        )
        if signature == self._last_derived_signature and (now - self._last_derived_save_ts) < 300.0:
            return
        self._last_derived_signature = signature
        self._last_derived_save_ts = now
        self._derived_store.async_delay_save(
            lambda: export_fn(time.time()) or {},
            15,
        )

    async def async_save_derived_state(self) -> None:
        """Flush persisted rolling 24h derived state immediately on shutdown/unload."""
        if self._derived_store is None or not hasattr(self._derived_store, "async_save"):
            return
        export_fn = getattr(self.controller, "export_derived_state", None)
        if not callable(export_fn):
            return
        state = export_fn(time.time())
        if isinstance(state, dict):
            res = self._derived_store.async_save(state)
            if inspect.isawaitable(res):
                await res

    async def async_shutdown(self):
        """Shutdown coordinator."""
        try:
            await self.async_save_derived_state()
        except Exception as err:
            _LOGGER.debug("Failed to flush derived state on shutdown: %s", err)
        async with self._lock:
            await self.hass.async_add_executor_job(self._close_client)
