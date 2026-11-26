"""Calculated/derived sensor definitions and stateful trackers for CHICO controllers."""
from __future__ import annotations

from collections.abc import Mapping
import time
from typing import Any

from .models import DerivedSensorSpec, extract_cache_value

DEFROST_AMBIENT_HOLD_SECONDS = 420.0

OPERATING_STATE_OPTIONS: tuple[str, ...] = (
    "off",
    "idle",
    "heating",
    "cooling",
    "hot_water",
    "heating_hot_water",
    "cooling_hot_water",
    "defrost",
    "antilegionella",
    "alarm",
)

_ECO_CURVE_KEYS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "hot_water": (
        ("econ_water_ambi_1", "econ_water_ambi_2", "econ_water_ambi_3", "econ_water_ambi_4"),
        ("econ_water_temp_1", "econ_water_temp_2", "econ_water_temp_3", "econ_water_temp_4"),
    ),
    "cooling": (
        ("econ_cool_ambi_1", "econ_cool_ambi_2", "econ_cool_ambi_3", "econ_cool_ambi_4"),
        ("econ_cool_temp_1", "econ_cool_temp_2", "econ_cool_temp_3", "econ_cool_temp_4"),
    ),
    "heating": (
        ("econ_heat_ambi_1", "econ_heat_ambi_2", "econ_heat_ambi_3", "econ_heat_ambi_4"),
        ("econ_heat_temp_1", "econ_heat_temp_2", "econ_heat_temp_3", "econ_heat_temp_4"),
    ),
}


def _get_float(data: Mapping[str, Any] | None, key: str) -> float | None:
    """Extract float value from coordinator data or return None."""
    val = extract_cache_value(data, key)
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _get_int(data: Mapping[str, Any] | None, key: str) -> int | None:
    """Extract integer value from coordinator data or return None."""
    val = extract_cache_value(data, key)
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _get_bit(data: Mapping[str, Any] | None, key: str, bit: int) -> bool | None:
    """Extract boolean bit from a status/control register word."""
    raw = _get_int(data, key)
    if raw is None:
        return None
    return bool(raw & (1 << bit))


def _compute_diff(data: Mapping[str, Any] | None, minuend_key: str, subtrahend_key: str) -> float | None:
    """Return rounded difference (minuend - subtrahend) when both inputs are present."""
    val_a = _get_float(data, minuend_key)
    val_b = _get_float(data, subtrahend_key)
    if val_a is None or val_b is None:
        return None
    return round(val_a - val_b, 2)


def compute_coil_ambient_delta(data: Mapping[str, Any] | None) -> float | None:
    """Return filtered outdoor-to-coil temperature difference (ambient - coil) for frost tracking."""
    amb = _get_float(data, "ambient_temp_filtered")
    if amb is None:
        amb = _get_float(data, "ambient_temp")
    coil = _get_float(data, "coil_temp")
    if amb is None or coil is None:
        return None
    return round(amb - coil, 2)


def compute_operating_state(data: Mapping[str, Any] | None) -> str | None:
    """Resolve human-readable CHICO operating state from status/output/control registers."""
    ws = _get_int(data, "working_status_register")
    out1 = _get_int(data, "output_symbol_1")
    if ws is None or out1 is None:
        return None

    if ws & (1 << 6):
        return "alarm"

    power_word = _get_int(data, "_control_0032")
    if power_word is not None and not (power_word & 1):
        return "off"

    if ws & (1 << 7):
        return "defrost"
    if ws & (1 << 4):
        return "antilegionella"

    out2 = _get_int(data, "output_symbol_2") or 0
    comp_on = bool(out1 & 1)
    heater_on = bool(out2 & ((1 << 5) | (1 << 7)))
    if not comp_on and not heater_on:
        return "idle"

    hw_demand = bool(ws & (1 << 0))
    heat_demand = bool(ws & (1 << 1))
    cool_demand = bool(ws & (1 << 5))

    if hw_demand and heat_demand:
        return "heating_hot_water"
    if hw_demand and cool_demand:
        return "cooling_hot_water"
    if hw_demand:
        return "hot_water"
    if heat_demand:
        return "heating"
    if cool_demand:
        return "cooling"

    if out2 & (1 << 6):
        return "hot_water"

    unit_mode = _get_int(data, "unit_mode")
    if unit_mode in (2, 4):
        return "cooling"
    if unit_mode == 0:
        return "hot_water"
    return "heating"


def _resolve_active_curve(data: Mapping[str, Any] | None) -> str:
    """Select active ECO curve ('hot_water', 'cooling', or 'heating') from current state."""
    ws = _get_int(data, "working_status_register") or 0
    out2 = _get_int(data, "output_symbol_2") or 0
    unit_mode = _get_int(data, "unit_mode")

    if (ws & (1 << 0)) or (out2 & (1 << 6)) or unit_mode == 0:
        return "hot_water"
    if (ws & (1 << 5)) or unit_mode in (2, 4):
        return "cooling"
    return "heating"


def compute_eco_curve_setpoint(data: Mapping[str, Any] | None) -> float | None:
    """Compute piecewise-linear ECO curve setpoint (E01-E24) for active mode & outdoor temp."""
    amb = _get_float(data, "ambient_temp_filtered")
    if amb is None:
        amb = _get_float(data, "ambient_temp")
    if amb is None:
        return None

    curve_name = _resolve_active_curve(data)
    ambi_keys, temp_keys = _ECO_CURVE_KEYS[curve_name]

    points: list[tuple[float, float]] = []
    for ak, tk in zip(ambi_keys, temp_keys):
        x = _get_float(data, ak)
        y = _get_float(data, tk)
        if x is None or y is None:
            return None
        points.append((x, y))

    points.sort(key=lambda pair: pair[0])
    # Deduplicate identical ambient breakpoints (keep latest sorted entry)
    deduped: list[tuple[float, float]] = []
    for x, y in points:
        if deduped and deduped[-1][0] == x:
            deduped[-1] = (x, y)
        else:
            deduped.append((x, y))

    if amb <= deduped[0][0]:
        return round(deduped[0][1], 1)
    if amb >= deduped[-1][0]:
        return round(deduped[-1][1], 1)

    for (x0, y0), (x1, y1) in zip(deduped, deduped[1:]):
        if x0 <= amb <= x1:
            ratio = (amb - x0) / (x1 - x0)
            return round(y0 + ratio * (y1 - y0), 1)
    return round(deduped[-1][1], 1)


def compute_eco_setpoint_delta(data: Mapping[str, Any] | None) -> float | None:
    """Return outlet water offset relative to the active ECO curve setpoint."""
    outlet = _get_float(data, "outlet_temp")
    eco = _get_float(data, "eco_active_setpoint")
    if eco is None:
        eco = compute_eco_curve_setpoint(data)
    if outlet is None or eco is None:
        return None
    return round(outlet - eco, 2)


def compute_estimated_power(data: Mapping[str, Any] | None) -> float | None:
    """Estimate electrical input power (W) using an empirical 2-state physical model."""
    hz = _get_float(data, "compressor_frequency")
    if hz is None:
        return None

    chassis_on = bool(_get_bit(data, "output_symbol_2", 0))
    chassis_w = 43.0 if chassis_on else 0.0

    if hz <= 0:
        return round(90.0 + chassis_w, 1)

    tcond = _get_float(data, "cond_temp")
    tamb = _get_float(data, "ambient_temp_filtered")
    if tamb is None:
        tamb = _get_float(data, "ambient_temp")
    if tcond is None or tamb is None:
        return None

    lift = max(0.0, tcond - tamb)
    est = 256.85 - (5.51 * hz) + (26.11 * hz * (lift / 30.0)) + chassis_w
    return round(max(0.0, est), 1)


class _ActiveDurationTracker:
    """Track elapsed duration (minutes) of an active boolean cycle and hold last value."""

    def __init__(self) -> None:
        self._active_since: float | None = None
        self._last_duration_min: float = 0.0

    def update(self, is_active: bool | None, now: float) -> float | None:
        """Update cycle state and return current or last completed duration in minutes."""
        if is_active is None:
            return None
        if is_active:
            if self._active_since is None:
                self._active_since = now
            elapsed = round(max(0.0, (now - self._active_since) / 60.0), 1)
            self._last_duration_min = elapsed
            return elapsed
        if self._active_since is not None:
            self._last_duration_min = round(max(0.0, (now - self._active_since) / 60.0), 1)
            self._active_since = None
        return self._last_duration_min


class _DefrostIntervalTracker:
    """Track elapsed time (minutes) since last defrost ended and hold completed interval."""

    def __init__(self) -> None:
        self._last_end_ts: float | None = None
        self._was_active: bool = False
        self._held_interval_min: float = 0.0

    def update(self, is_defrost: bool | None, now: float) -> float | None:
        """Update defrost interval state and return live or held interval in minutes."""
        if is_defrost is None:
            return None
        if is_defrost:
            if not self._was_active:
                if self._last_end_ts is not None:
                    self._held_interval_min = round(max(0.0, (now - self._last_end_ts) / 60.0), 1)
                self._was_active = True
            return self._held_interval_min

        if self._was_active:
            self._last_end_ts = now
            self._was_active = False
            self._held_interval_min = 0.0
            return 0.0

        if self._last_end_ts is not None:
            return round(max(0.0, (now - self._last_end_ts) / 60.0), 1)
        return 0.0


class ChicoDerivedTracker:
    """Stateful per-controller tracker for time-dependent CHICO derived sensors."""

    def __init__(self) -> None:
        """Initialize trackers for ambient defrost filtering and cycle durations."""
        self._last_non_defrost_ambient: float | None = None
        self._held_ambient: float | None = None
        self._ambient_hold_until: float | None = None
        self._was_defrost: bool = False
        self._compressor_duration = _ActiveDurationTracker()
        self._defrost_duration = _ActiveDurationTracker()
        self._defrost_interval = _DefrostIntervalTracker()

    def update_ambient_filtered(self, data: Mapping[str, Any], now: float) -> float | None:
        """Freeze ambient temperature during defrost and a 7-minute post-defrost cooldown."""
        raw_amb = _get_float(data, "ambient_temp")
        if raw_amb is None:
            return None

        defrost = bool(_get_bit(data, "working_status_register", 7))
        if defrost:
            if not self._was_defrost:
                self._held_ambient = (
                    self._last_non_defrost_ambient
                    if self._last_non_defrost_ambient is not None
                    else raw_amb
                )
            self._was_defrost = True
            self._ambient_hold_until = now + DEFROST_AMBIENT_HOLD_SECONDS
            return self._held_ambient

        if self._was_defrost:
            self._was_defrost = False
            self._ambient_hold_until = now + DEFROST_AMBIENT_HOLD_SECONDS

        if self._ambient_hold_until is not None and self._held_ambient is not None:
            if now < self._ambient_hold_until and raw_amb > self._held_ambient:
                return self._held_ambient
            self._ambient_hold_until = None
            self._held_ambient = None

        self._last_non_defrost_ambient = raw_amb
        return raw_amb

    def compute(self, data: Mapping[str, Any], now: float | None = None) -> dict[str, Any]:
        """Compute all derived sensor values from the current coordinator snapshot."""
        ts = time.time() if now is None else float(now)
        results: dict[str, Any] = {}

        # Update stateful sensors first so downstream derived formulas can reuse filtered ambient
        amb_filtered = self.update_ambient_filtered(data, ts)
        if amb_filtered is not None:
            results["ambient_temp_filtered"] = amb_filtered

        comp_dur = self._compressor_duration.update(
            _get_bit(data, "output_symbol_1", 0),
            ts,
        )
        if comp_dur is not None:
            results["compressor_last_run_duration"] = comp_dur

        defr_dur = self._defrost_duration.update(
            _get_bit(data, "working_status_register", 7),
            ts,
        )
        if defr_dur is not None:
            results["defrost_last_duration"] = defr_dur

        defr_int = self._defrost_interval.update(
            _get_bit(data, "working_status_register", 7),
            ts,
        )
        if defr_int is not None:
            results["defrost_last_interval"] = defr_int

        merged: dict[str, Any] = dict(data)
        if amb_filtered is not None:
            merged["ambient_temp_filtered"] = amb_filtered

        for spec in CHICO_DERIVED_SENSORS:
            if spec.key in results:
                continue
            val = spec.value_fn(merged)
            if val is not None:
                results[spec.key] = val

        return results


CHICO_DERIVED_SENSORS: tuple[DerivedSensorSpec, ...] = (
    DerivedSensorSpec(
        key="ambient_temp_filtered",
        name="Filtered Ambient Temperature",
        value_fn=lambda data: _get_float(data, "ambient_temp_filtered")
        if _get_float(data, "ambient_temp_filtered") is not None
        else _get_float(data, "ambient_temp"),
        unit="°C",
        device_class="temperature",
        state_class="measurement",
        diagnostic=False,
        enabled_default=True,
        suggested_display_precision=1,
        description=(
            "Outdoor temperature with defrost heat spikes filtered out: freezes the last valid "
            "ambient reading during defrost and for up to 7 minutes afterward until the sensor cools down."
        ),
        formula="ambient_temp held while defrost_active or within 7 min cooldown",
    ),
    DerivedSensorSpec(
        key="operating_state",
        name="Operating State",
        value_fn=compute_operating_state,
        unit=None,
        device_class="enum",
        state_class="none",
        options=OPERATING_STATE_OPTIONS,
        diagnostic=False,
        enabled_default=True,
        description=(
            "Human-readable heat pump operating state derived from power, alarm, defrost, "
            "antilegionella, compressor, heater, and demand flags."
        ),
        formula="priority(alarm -> off -> defrost -> antilegionella -> active demand -> idle)",
    ),
    DerivedSensorSpec(
        key="eco_active_setpoint",
        name="ECO Curve Target Setpoint",
        value_fn=compute_eco_curve_setpoint,
        unit="°C",
        device_class="temperature",
        state_class="measurement",
        diagnostic=False,
        enabled_default=True,
        suggested_display_precision=1,
        description=(
            "Target water temperature calculated from CHICO Economic Mode curves (E01-E24) "
            "using the filtered ambient temperature and active mode."
        ),
        formula="linear_interp(E01..E12, E13..E24, ambient_temp_filtered)",
    ),
    DerivedSensorSpec(
        key="eco_setpoint_delta",
        name="ECO Curve Setpoint Delta",
        value_fn=compute_eco_setpoint_delta,
        unit="°C",
        device_class="temperature",
        state_class="measurement",
        diagnostic=False,
        enabled_default=True,
        suggested_display_precision=1,
        description=(
            "Difference between outlet water temperature and the active ECO weather curve "
            "setpoint. Positive values indicate supply water is warmer than the curve."
        ),
        formula="outlet_temp - eco_active_setpoint",
    ),
    DerivedSensorSpec(
        key="compressor_last_run_duration",
        name="Compressor Last Run Duration",
        value_fn=lambda data: _get_float(data, "compressor_last_run_duration"),
        unit="min",
        device_class="duration",
        state_class="measurement",
        diagnostic=False,
        enabled_default=True,
        suggested_display_precision=1,
        description=(
            "Live duration of the active compressor cycle in minutes, or the held duration of the "
            "most recently completed cycle (tracked since HA startup)."
        ),
        formula="(now - compressor_start_ts) / 60",
    ),
    DerivedSensorSpec(
        key="defrost_last_duration",
        name="Last Defrost Duration",
        value_fn=lambda data: _get_float(data, "defrost_last_duration"),
        unit="min",
        device_class="duration",
        state_class="measurement",
        diagnostic=False,
        enabled_default=True,
        suggested_display_precision=1,
        description=(
            "Live duration of the active defrost cycle in minutes, or the held duration of the "
            "last completed defrost (tracked since HA startup)."
        ),
        formula="(now - defrost_start_ts) / 60",
    ),
    DerivedSensorSpec(
        key="defrost_last_interval",
        name="Defrost Interval",
        value_fn=lambda data: _get_float(data, "defrost_last_interval"),
        unit="min",
        device_class="duration",
        state_class="measurement",
        diagnostic=False,
        enabled_default=True,
        suggested_display_precision=1,
        description=(
            "Elapsed minutes since the previous defrost ended, or the held interval between "
            "consecutive defrosts while defrosting (tracked since HA startup)."
        ),
        formula="(now - last_defrost_end_ts) / 60",
    ),
    DerivedSensorSpec(
        key="coil_ambient_delta",
        name="Coil-Ambient Temperature Delta",
        value_fn=compute_coil_ambient_delta,
        unit="°C",
        device_class="temperature",
        state_class="measurement",
        diagnostic=False,
        enabled_default=True,
        suggested_display_precision=1,
        description=(
            "Temperature difference between filtered outdoor air and evaporator coil. "
            "Rising values indicate frost accumulation approaching defrost thresholds (H07/H10/H13)."
        ),
        formula="ambient_temp_filtered - coil_temp",
    ),
    DerivedSensorSpec(
        key="water_delta_t",
        name="Water Delta T",
        value_fn=lambda data: _compute_diff(data, "outlet_temp", "inlet_temp"),
        unit="°C",
        device_class="temperature",
        state_class="measurement",
        diagnostic=False,
        enabled_default=True,
        suggested_display_precision=1,
        description="Temperature difference across the water heat exchanger (outlet minus inlet).",
        formula="outlet_temp - inlet_temp",
    ),
    DerivedSensorSpec(
        key="condenser_approach_temp",
        name="Condenser Approach Temperature",
        value_fn=lambda data: _compute_diff(data, "cond_temp", "outlet_temp"),
        unit="°C",
        device_class="temperature",
        state_class="measurement",
        diagnostic=True,
        enabled_default=True,
        suggested_display_precision=1,
        description=(
            "Temperature gap between refrigerant condensation and leaving water. "
            "High values may indicate heat exchanger fouling or low water flow."
        ),
        formula="cond_temp - outlet_temp",
    ),
    DerivedSensorSpec(
        key="suction_superheat",
        name="Suction Superheat",
        value_fn=lambda data: _compute_diff(data, "suction_gas_temp", "evap_temp"),
        unit="°C",
        device_class="temperature",
        state_class="measurement",
        diagnostic=True,
        enabled_default=True,
        suggested_display_precision=1,
        description="Evaporator suction superheat indicating EEV expansion valve regulation health.",
        formula="suction_gas_temp - evap_temp",
    ),
    DerivedSensorSpec(
        key="discharge_superheat",
        name="Discharge Superheat",
        value_fn=lambda data: _compute_diff(data, "exhaust_temp", "cond_temp"),
        unit="°C",
        device_class="temperature",
        state_class="measurement",
        diagnostic=True,
        enabled_default=True,
        suggested_display_precision=1,
        description="Compressor discharge superheat above condensation temperature.",
        formula="exhaust_temp - cond_temp",
    ),
    DerivedSensorSpec(
        key="estimated_power",
        name="Estimated Electrical Power (Experimental)",
        value_fn=compute_estimated_power,
        unit="W",
        device_class="power",
        state_class="measurement",
        diagnostic=False,
        enabled_default=True,
        suggested_display_precision=0,
        experimental=True,
        description=(
            "Experimental electrical input power estimate derived from compressor frequency, "
            "condensation-to-ambient temperature lift, and chassis heater state."
        ),
        formula=(
            "idle: 90 + 43*chassis_heater; run: 256.85 - 5.51*Hz + "
            "26.11*Hz*max(cond_temp - ambient_temp_filtered, 0)/30 + 43*chassis_heater"
        ),
        disclaimer=(
            "EXPERIMENTAL APPROXIMATION ONLY: Calibrated empirically on a single 3-phase unit "
            "without backup immersion heaters. Do not rely on this value for billing, protection, "
            "or accurate energy accounting across different heat pump capacities."
        ),
    ),
)
