"""Controller-agnostic register models, entity specs, and Modbus codecs."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
import math
import struct
from typing import Any


class RegisterSpace(StrEnum):
    """Modbus register/point address space."""

    HOLDING_REGISTER = "holding_register"  # FC 0x03 read / 0x06, 0x10 write (4xxxx)
    INPUT_REGISTER = "input_register"      # FC 0x04 read (3xxxx)
    DISCRETE_INPUT = "discrete_input"      # FC 0x02 read (1xxxx)
    COIL = "coil"                          # FC 0x01 read / 0x05 write (0xxxx)


class DataType(StrEnum):
    """Supported Modbus value encodings."""

    INT16 = "int16"
    UINT16 = "uint16"
    INT32 = "int32"
    UINT32 = "uint32"
    FLOAT32 = "float32"
    BOOL = "bool"


class WordOrder(StrEnum):
    """Multi-register word ordering for 32-bit values."""

    BIG_ENDIAN = "big_endian"        # AB CD (high word first)
    LITTLE_ENDIAN = "little_endian"  # CD AB (low word first / word-swapped)


@dataclass(frozen=True)
class ModbusBatchSpec:
    """Contiguous Modbus read batch specification."""

    space: RegisterSpace
    start_address: int
    count: int
    description: str = ""


@dataclass(frozen=True)
class SensorSpec:
    """Read-only sensor entity specification (with optional metadata for future write enablement)."""

    key: str
    name: str
    address: int
    space: RegisterSpace = RegisterSpace.HOLDING_REGISTER
    data_type: DataType = DataType.UINT16
    word_order: WordOrder = WordOrder.BIG_ENDIAN
    scale: float | int = 1
    unit: str | None = None
    device_class: str | None = None
    state_class: str | None = None
    diagnostic: bool = False
    clamp_min: float | None = None
    clamp_max: float | None = None
    raw_offset: float | int = 0
    bit_mask: int | None = None
    options: Mapping[int, str] | None = None
    min_value: float | None = None
    max_value: float | None = None
    step: float | None = None
    writable: bool = False
    enabled_default: bool = True

    def as_number_spec(
        self,
        *,
        is_primary: bool = False,
        enabled_default: bool | None = None,
        is_expert: bool = False,
    ) -> NumberSpec:
        """Convert a numeric parameter SensorSpec into a writable NumberSpec."""
        if self.min_value is None or self.max_value is None:
            raise ValueError(f"SensorSpec '{self.key}' lacks min_value/max_value metadata for NumberSpec")
        return NumberSpec(
            key=self.key,
            name=self.name,
            address=self.address,
            space=self.space,
            data_type=self.data_type,
            word_order=self.word_order,
            scale=self.scale,
            unit=self.unit,
            min_value=self.min_value,
            max_value=self.max_value,
            step=self.step if self.step is not None else 1.0,
            device_class=self.device_class,
            is_primary=is_primary,
            raw_offset=self.raw_offset,
            bit_mask=self.bit_mask,
            enabled_default=self.enabled_default if enabled_default is None else enabled_default,
            is_expert=is_expert,
        )

    def as_select_spec(
        self,
        *,
        is_config: bool = True,
        enabled_default: bool | None = None,
        is_expert: bool = False,
    ) -> SelectSpec:
        """Convert an enum parameter SensorSpec into a writable SelectSpec."""
        if not self.options:
            raise ValueError(f"SensorSpec '{self.key}' lacks options metadata for SelectSpec")
        return SelectSpec(
            key=self.key,
            name=self.name,
            address=self.address,
            options=dict(self.options),
            space=self.space,
            is_config=is_config,
            enabled_default=self.enabled_default if enabled_default is None else enabled_default,
            is_expert=is_expert,
        )


@dataclass(frozen=True)
class DerivedSensorSpec:
    """Controller-calculated virtual sensor specification (not backed by a single register)."""

    key: str
    name: str
    value_fn: Callable[[Mapping[str, Any] | None], Any]
    unit: str | None = None
    device_class: str | None = None
    state_class: str | None = None
    options: tuple[str, ...] | None = None
    diagnostic: bool = False
    enabled_default: bool = False
    suggested_display_precision: int | None = None
    description: str = ""
    formula: str = ""
    experimental: bool = False
    disclaimer: str | None = None


@dataclass(frozen=True)
class BinarySensorSpec:
    """Read-only binary sensor specification (bitfield or direct coil/discrete input)."""

    key: str
    name: str
    address: int
    bit: int | None = None
    source_key: str | None = None
    space: RegisterSpace = RegisterSpace.HOLDING_REGISTER
    inverted: bool = False
    diagnostic: bool = False
    device_class: str | None = None
    coil_address: int | None = None
    writable: bool = False
    enabled_default: bool = True

    def as_switch_spec(
        self,
        *,
        cache_key: str | None = None,
        is_config: bool = True,
        enabled_default: bool | None = None,
        is_expert: bool = False,
    ) -> SwitchSpec:
        """Convert a binary parameter spec into a writable SwitchSpec."""
        return SwitchSpec(
            key=self.key,
            name=self.name,
            address=self.address,
            bit=self.bit,
            space=self.space,
            coil_address=self.coil_address,
            cache_key=cache_key if cache_key is not None else self.source_key,
            is_config=is_config,
            inverted=self.inverted,
            enabled_default=self.enabled_default if enabled_default is None else enabled_default,
            is_expert=is_expert,
        )


@dataclass(frozen=True)
class NumberSpec:
    """Read-write numeric parameter specification."""

    key: str
    name: str
    address: int
    space: RegisterSpace = RegisterSpace.HOLDING_REGISTER
    data_type: DataType = DataType.UINT16
    word_order: WordOrder = WordOrder.BIG_ENDIAN
    scale: float | int = 1
    unit: str | None = None
    min_value: float = 0.0
    max_value: float = 100.0
    step: float = 1.0
    device_class: str | None = None
    supports_temp_step_override: bool = False
    is_primary: bool = False
    raw_offset: float | int = 0
    bit_mask: int | None = None
    enabled_default: bool = True
    is_expert: bool = False


@dataclass(frozen=True)
class SelectSpec:
    """Read-write enum selection specification."""

    key: str
    name: str
    address: int
    options: dict[int, str]
    space: RegisterSpace = RegisterSpace.HOLDING_REGISTER
    is_config: bool = True
    enabled_default: bool = True
    is_expert: bool = False


@dataclass(frozen=True)
class SwitchSpec:
    """Read-write boolean switch specification (bitfield or coil)."""

    key: str
    name: str
    address: int
    bit: int | None = None
    space: RegisterSpace = RegisterSpace.HOLDING_REGISTER
    coil_address: int | None = None
    cache_key: str | None = None
    is_config: bool = False
    inverted: bool = False
    enabled_default: bool = True
    is_expert: bool = False


@dataclass(frozen=True)
class ButtonSpec:
    """Momentary write button specification (bitfield, coil, or register)."""

    key: str
    name: str
    address: int
    bit: int | None = None
    space: RegisterSpace = RegisterSpace.HOLDING_REGISTER
    description: str = ""
    write_value: bool | int = True
    diagnostic: bool = True


@dataclass(frozen=True)
class ClimateCapabilities:
    """Controller climate capabilities exposed to Home Assistant climate entities."""

    enabled: bool = True
    hvac_modes: tuple[str, ...] = ("off", "heat", "cool", "heat_cool")
    fan_modes: tuple[str, ...] = ()
    preset_modes: tuple[str, ...] = ()
    supports_target_temperature: bool = True
    supports_fan_mode: bool = False
    supports_preset_mode: bool = False
    min_temp: float = 10.0
    max_temp: float = 55.0
    supports_dhw: bool = False
    dhw_hvac_modes: tuple[str, ...] = ("off", "heat")
    dhw_min_temp: float = 10.0
    dhw_max_temp: float = 55.0
    extra: dict[str, Any] = field(default_factory=dict)


def extract_cache_value(data: Mapping[str, Any] | None, key: str, default: Any = None) -> Any:
    """Extract scalar value from coordinator cache (supports dict and legacy scalar formats)."""
    if not data:
        return default
    cache_entry = data.get(key)
    if cache_entry is not None:
        if isinstance(cache_entry, Mapping):
            return cache_entry.get("value", default)
        return cache_entry
    return default


def registers_per_value(data_type: DataType) -> int:
    """Return number of 16-bit Modbus registers consumed by a data type."""
    if data_type in (DataType.INT32, DataType.UINT32, DataType.FLOAT32):
        return 2
    return 1


def _order_words(words: list[int] | tuple[int, ...], word_order: WordOrder) -> tuple[int, int]:
    """Order two 16-bit words into (high_word, low_word) for big-endian unpacking."""
    w0 = int(words[0]) & 0xFFFF
    w1 = int(words[1]) & 0xFFFF
    if word_order == WordOrder.LITTLE_ENDIAN:
        return w1, w0
    return w0, w1


def decode_registers(
    words: list[int] | tuple[int, ...],
    data_type: DataType,
    scale: float | int = 1,
    word_order: WordOrder = WordOrder.BIG_ENDIAN,
    clamp_min: float | None = None,
    clamp_max: float | None = None,
    raw_offset: float | int = 0,
    bit_mask: int | None = None,
) -> float | int | bool:
    """Decode raw Modbus register word(s) or bit into a scaled Python value."""
    if data_type == DataType.BOOL:
        return bool(words[0])

    if data_type == DataType.UINT16:
        raw_u16 = int(words[0]) & 0xFFFF
        if bit_mask is not None:
            raw_u16 &= bit_mask
        raw: float | int = raw_u16
    elif data_type == DataType.INT16:
        raw_u16 = int(words[0]) & 0xFFFF
        if bit_mask is not None:
            raw_u16 &= bit_mask
            sign_bit = (bit_mask + 1) >> 1
            raw = raw_u16 - (bit_mask + 1) if (bit_mask & (bit_mask + 1) == 0 and raw_u16 >= sign_bit) else raw_u16
        else:
            raw = raw_u16 - 65536 if raw_u16 > 32767 else raw_u16
    elif data_type in (DataType.UINT32, DataType.INT32, DataType.FLOAT32):
        if len(words) < 2:
            raise ValueError(f"Expected 2 registers for {data_type}, got {len(words)}")
        hi, lo = _order_words(words, word_order)
        if data_type == DataType.FLOAT32:
            packed = struct.pack(">HH", hi, lo)
            float_val = struct.unpack(">f", packed)[0]
            if not math.isfinite(float_val):
                raise ValueError(f"Non-finite float32 decoded from words {[hi, lo]}")
            raw = float_val
        else:
            raw_u32 = (hi << 16) | lo
            if data_type == DataType.INT32 and raw_u32 >= 0x80000000:
                raw = raw_u32 - 0x100000000
            else:
                raw = raw_u32
    else:
        raise ValueError(f"Unsupported data type: {data_type}")

    value = (raw + raw_offset) * scale
    if isinstance(value, float) and data_type != DataType.FLOAT32:
        value = round(value, 6)
    if clamp_min is not None and value < clamp_min:
        value = clamp_min
    if clamp_max is not None and value > clamp_max:
        value = clamp_max
    return value


def encode_registers(
    value: float | int | bool,
    data_type: DataType,
    scale: float | int = 1,
    word_order: WordOrder = WordOrder.BIG_ENDIAN,
    raw_offset: float | int = 0,
    bit_mask: int | None = None,
) -> list[int]:
    """Encode a user-facing value into 16-bit Modbus register word(s)."""
    if data_type == DataType.BOOL:
        return [1 if value else 0]

    if scale == 0:
        raise ValueError("Scale must be non-zero")

    scaled = (float(value) / float(scale)) - float(raw_offset)

    if data_type == DataType.UINT16:
        raw_int = int(round(scaled))
        if bit_mask is not None:
            raw_int &= bit_mask
        return [raw_int & 0xFFFF]
    if data_type == DataType.INT16:
        raw_int = int(round(scaled))
        if bit_mask is not None:
            raw_int &= bit_mask
        return [raw_int & 0xFFFF]
    if data_type in (DataType.UINT32, DataType.INT32):
        raw_int = int(round(scaled)) & 0xFFFFFFFF
        hi = (raw_int >> 16) & 0xFFFF
        lo = raw_int & 0xFFFF
        return [lo, hi] if word_order == WordOrder.LITTLE_ENDIAN else [hi, lo]
    if data_type == DataType.FLOAT32:
        packed = struct.pack(">f", scaled)
        hi, lo = struct.unpack(">HH", packed)
        return [lo, hi] if word_order == WordOrder.LITTLE_ENDIAN else [hi, lo]

    raise ValueError(f"Unsupported data type: {data_type}")
