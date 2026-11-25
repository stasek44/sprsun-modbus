"""Shared Modbus batch read and decoding helpers for controller drivers."""
from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from .models import (
    BinarySensorSpec,
    ModbusBatchSpec,
    NumberSpec,
    RegisterSpace,
    SelectSpec,
    SensorSpec,
    SwitchSpec,
    decode_registers,
    registers_per_value,
)

if TYPE_CHECKING:
    from pymodbus.client import ModbusTcpClient

_LOGGER = logging.getLogger(__name__)


class ModbusBatchError(ValueError):
    """Raised when a Modbus batch read returns an error response."""


class ModbusDesyncError(ModbusBatchError):
    """Raised when a Modbus batch response length mismatches the requested count."""


def read_modbus_batch(
    client: ModbusTcpClient,
    device_address: int,
    batch: ModbusBatchSpec,
    turnaround_delay: float = 0.0,
) -> list[int] | list[bool]:
    """Read a contiguous Modbus batch across any supported register/bit space."""
    if turnaround_delay > 0:
        time.sleep(turnaround_delay)

    if batch.space == RegisterSpace.HOLDING_REGISTER:
        result = client.read_holding_registers(
            address=batch.start_address,
            count=batch.count,
            device_id=device_address,
        )
    elif batch.space == RegisterSpace.INPUT_REGISTER:
        result = client.read_input_registers(
            address=batch.start_address,
            count=batch.count,
            device_id=device_address,
        )
    elif batch.space == RegisterSpace.DISCRETE_INPUT:
        result = client.read_discrete_inputs(
            address=batch.start_address,
            count=batch.count,
            device_id=device_address,
        )
    elif batch.space == RegisterSpace.COIL:
        result = client.read_coils(
            address=batch.start_address,
            count=batch.count,
            device_id=device_address,
        )
    else:
        raise ValueError(f"Unsupported register space: {batch.space}")

    if result.isError():
        raise ModbusBatchError(f"Modbus read error: {result}")

    if batch.space in (RegisterSpace.DISCRETE_INPUT, RegisterSpace.COIL):
        bits = getattr(result, "bits", None)
        if bits is None or len(bits) < batch.count:
            got = len(bits) if bits is not None else 0
            raise ModbusDesyncError(
                f"Modbus read error: expected {batch.count} bits, got {got}"
            )
        return [bool(b) for b in bits[: batch.count]]

    regs = getattr(result, "registers", None)
    if not regs or len(regs) != batch.count:
        got = len(regs) if regs else 0
        raise ModbusDesyncError(
            f"Modbus read error: expected {batch.count} registers, got {got}"
        )
    return list(regs)


def decode_batch_into_data(
    specs: list[SensorSpec | BinarySensorSpec | NumberSpec | SelectSpec | SwitchSpec]
    | tuple[SensorSpec | BinarySensorSpec | NumberSpec | SelectSpec | SwitchSpec, ...],
    space: RegisterSpace,
    start_address: int,
    raw_values: list[int] | list[bool],
    data: dict[str, Any],
) -> int:
    """Decode matching specs from a batch response into coordinator data dict.

    Returns the number of decoded entries written to ``data``.
    """
    end_address = start_address + len(raw_values)
    decoded = 0

    for spec in specs:
        if spec.space != space:
            continue

        if isinstance(spec, BinarySensorSpec):
            # Bitfield binary sensors read from a shared word via source_key; direct ones read 1 bit.
            if spec.bit is not None:
                continue
            if start_address <= spec.address < end_address:
                idx = spec.address - start_address
                val = bool(raw_values[idx])
                data[spec.key] = (not val) if spec.inverted else val
                decoded += 1
            continue

        if isinstance(spec, SwitchSpec):
            if spec.bit is not None:
                # Bitfield switch shares a holding register word under cache_key
                if start_address <= spec.address < end_address:
                    idx = spec.address - start_address
                    cache_key = spec.cache_key or f"_control_{spec.address:04x}"
                    if cache_key not in data:
                        data[cache_key] = int(raw_values[idx])
                        decoded += 1
            elif start_address <= spec.address < end_address:
                idx = spec.address - start_address
                val = bool(raw_values[idx])
                data[spec.key] = (not val) if spec.inverted else val
                decoded += 1
            continue

        if isinstance(spec, SelectSpec):
            if start_address <= spec.address < end_address:
                idx = spec.address - start_address
                data[spec.key] = int(raw_values[idx])
                decoded += 1
            continue

        # SensorSpec or NumberSpec
        reg_count = registers_per_value(spec.data_type)
        if spec.address < start_address or spec.address + reg_count > end_address:
            continue
        idx = spec.address - start_address
        words = [int(w) for w in raw_values[idx : idx + reg_count]]
        clamp_min = getattr(spec, "clamp_min", None)
        clamp_max = getattr(spec, "clamp_max", None)
        data[spec.key] = decode_registers(
            words=words,
            data_type=spec.data_type,
            scale=spec.scale,
            word_order=spec.word_order,
            clamp_min=clamp_min,
            clamp_max=clamp_max,
        )
        decoded += 1

    return decoded
