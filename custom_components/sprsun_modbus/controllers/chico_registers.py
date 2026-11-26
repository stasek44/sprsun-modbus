"""CHICO controller register map and declarative entity specifications."""
from __future__ import annotations

from collections.abc import Mapping

from .models import (
    BinarySensorSpec,
    ButtonSpec,
    DataType,
    ModbusBatchSpec,
    NumberSpec,
    RegisterSpace,
    SelectSpec,
    SensorSpec,
    SwitchSpec,
)

# Status register keys for binary sensor bitfield decoding
CHICO_STATUS_REGISTER_KEYS: dict[int, str] = {
    0x0002: "switching_input_symbol",
    0x0003: "working_status_register",  # Backward-compatible key name
    0x0004: "output_symbol_1",
    0x0005: "output_symbol_2",
    0x0006: "output_symbol_3",
    0x0007: "failure_symbol_1",
    0x0008: "failure_symbol_2",
    0x0009: "failure_symbol_3",
    0x000A: "failure_symbol_4",
    0x000B: "failure_symbol_5",
    0x000C: "failure_symbol_6",
    0x000D: "failure_symbol_7",
}

# Control bitfield registers stored as raw words during RW batch reads
CHICO_CONTROL_REGISTER_KEYS: dict[int, str] = {
    0x0032: "_control_0032",
    0x0033: "_control_0033",
    0x0034: "_control_0034",
    0x0035: "_control_0035",
}

CHICO_DIAGNOSTIC_SENSOR_KEYS: frozenset[str] = frozenset({
    "software_version_year",
    "software_version_month_day",
    "controller_version",
    "display_version",
    "switching_input_symbol",
    "working_status_mark",
    "output_symbol_1",
    "output_symbol_2",
    "output_symbol_3",
    "failure_symbol_1",
    "failure_symbol_2",
    "failure_symbol_3",
    "failure_symbol_4",
    "failure_symbol_5",
    "failure_symbol_6",
    "failure_symbol_7",
    "freq_conversion_failure_1",
    "freq_conversion_failure_2",
    "freq_conversion_fault_high",
    "freq_conversion_fault_low",
})

CHICO_RO_BATCH = ModbusBatchSpec(
    space=RegisterSpace.HOLDING_REGISTER,
    start_address=0x0000,
    count=50,
    description="Read-Only Status & Telemetry (0x0000-0x0031)",
)

# Contiguous holding-register batches across valid RW / expert ranges (skipping PDF Invalid gaps,
# keeping batch size <= 62 registers for RS485 / Elfin EW11 UART buffer safety).
CHICO_RW_BATCHES: tuple[ModbusBatchSpec, ...] = (
    ModbusBatchSpec(
        space=RegisterSpace.HOLDING_REGISTER,
        start_address=0x0032,
        count=5,
        description="Control Marks + Timeband + Unit Mode (0x0032-0x0036)",
    ),
    ModbusBatchSpec(
        space=RegisterSpace.HOLDING_REGISTER,
        start_address=0x0037,
        count=51,
        description="Defrost H01-H16 + Main EEV A01-A51 + Aux EEV B02-B20 (0x0037-0x0069)",
    ),
    ModbusBatchSpec(
        space=RegisterSpace.HOLDING_REGISTER,
        start_address=0x0070,
        count=2,
        description="Aux EEV Water Initial B27-B28 (0x0070-0x0071)",
    ),
    ModbusBatchSpec(
        space=RegisterSpace.HOLDING_REGISTER,
        start_address=0x0078,
        count=62,
        description="Aux EEV + HP/LP Protect F02-F05 + DC Fan D03-D20 (0x0078-0x00B5)",
    ),
    ModbusBatchSpec(
        space=RegisterSpace.HOLDING_REGISTER,
        start_address=0x00B6,
        count=55,
        description="Aux EEV Diffs + P01-P05 + Defrost Temps + Superheat + F39-F50 (0x00B6-0x00EC)",
    ),
    ModbusBatchSpec(
        space=RegisterSpace.HOLDING_REGISTER,
        start_address=0x00ED,
        count=43,
        description="Aux EEV SH B12-B18 + AC Fan + Exhaust TP + Normal Freq Curves R00-R33 (0x00ED-0x0117)",
    ),
    ModbusBatchSpec(
        space=RegisterSpace.HOLDING_REGISTER,
        start_address=0x0119,
        count=12,
        description="Timeband 1-3 ON/OFF Schedules (0x0119-0x0124)",
    ),
    ModbusBatchSpec(
        space=RegisterSpace.HOLDING_REGISTER,
        start_address=0x012D,
        count=60,
        description="ECO / Night / Test Compressor Frequency Curves R34-R93 (0x012D-0x0168)",
    ),
    ModbusBatchSpec(
        space=RegisterSpace.HOLDING_REGISTER,
        start_address=0x0169,
        count=29,
        description="Economic Curves E01-E24 + General Settings G03-G08 (0x0169-0x0185)",
    ),
    ModbusBatchSpec(
        space=RegisterSpace.HOLDING_REGISTER,
        start_address=0x0186,
        count=54,
        description="Factory F13-F56 + G02/G04/G09-G11 + Antilegionella + Timeband Temps + R94 (0x0186-0x01BB)",
    ),
)

# Optional batches for reserved gaps deduced from 8-bin tables (marked Invalid in V1.2 PDF).
# Read independently so IllegalDataAddress on older firmware never impacts confirmed batches.
CHICO_OPTIONAL_RW_BATCHES: tuple[ModbusBatchSpec, ...] = (
    ModbusBatchSpec(
        space=RegisterSpace.HOLDING_REGISTER,
        start_address=0x006A,
        count=6,
        description="Deduced Aux EEV Heat Initial B21-B26 (0x006A-0x006F)",
    ),
    ModbusBatchSpec(
        space=RegisterSpace.HOLDING_REGISTER,
        start_address=0x0072,
        count=6,
        description="Deduced Aux EEV Water Initial B29-B34 (0x0072-0x0077)",
    ),
)


def _ro_sensor(
    address: int,
    key: str,
    name: str,
    scale: float | int = 1,
    unit: str | None = None,
    device_class: str | None = None,
    data_type: DataType = DataType.UINT16,
    clamp_min: float | None = None,
) -> SensorSpec:
    """Create a CHICO read-only SensorSpec with consistent defaults."""
    state_class = (
        "measurement"
        if device_class in ("temperature", "pressure", "power", "current", "frequency", "voltage")
        else None
    )
    return SensorSpec(
        key=key,
        name=name,
        address=address,
        space=RegisterSpace.HOLDING_REGISTER,
        data_type=data_type,
        scale=scale,
        unit=unit,
        device_class=device_class,
        state_class=state_class,
        diagnostic=key in CHICO_DIAGNOSTIC_SENSOR_KEYS,
        clamp_min=clamp_min,
    )


CHICO_CORE_SENSORS: tuple[SensorSpec, ...] = (
    # System Status
    _ro_sensor(0x0000, "compressor_runtime", "Compressor Runtime", 1, "h"),
    _ro_sensor(0x0001, "cop", "COP", 1),
    _ro_sensor(0x0013, "software_version_year", "Software Version (Year)", 1),
    _ro_sensor(0x0014, "software_version_month_day", "Software Version (Month/Day)", 1),
    _ro_sensor(0x002C, "controller_version", "Controller Version", 1),
    _ro_sensor(0x002D, "display_version", "Display Version", 1),
    # Input/Output/Status Flags
    _ro_sensor(0x0002, "switching_input_symbol", "Switching Input Symbol", 1),
    _ro_sensor(0x0003, "working_status_mark", "Working Status Mark", 1),
    _ro_sensor(0x0004, "output_symbol_1", "Output Symbol 1", 1),
    _ro_sensor(0x0005, "output_symbol_2", "Output Symbol 2", 1),
    _ro_sensor(0x0006, "output_symbol_3", "Output Symbol 3", 1),
    # Failure/Alarm Flags
    _ro_sensor(0x0007, "failure_symbol_1", "Failure Symbol 1", 1),
    _ro_sensor(0x0008, "failure_symbol_2", "Failure Symbol 2", 1),
    _ro_sensor(0x0009, "failure_symbol_3", "Failure Symbol 3", 1),
    _ro_sensor(0x000A, "failure_symbol_4", "Failure Symbol 4", 1),
    _ro_sensor(0x000B, "failure_symbol_5", "Failure Symbol 5", 1),
    _ro_sensor(0x000C, "failure_symbol_6", "Failure Symbol 6", 1),
    _ro_sensor(0x000D, "failure_symbol_7", "Failure Symbol 7", 1),
    # Temperature Sensors
    _ro_sensor(0x000E, "inlet_temp", "Inlet Water Temperature", 0.1, "°C", "temperature"),
    _ro_sensor(0x000F, "hotwater_temp", "Hot Water Temperature", 0.1, "°C", "temperature"),
    _ro_sensor(0x0011, "ambient_temp", "Ambient Temperature", 0.5, "°C", "temperature", DataType.INT16),
    _ro_sensor(0x0012, "outlet_temp", "Outlet Water Temperature", 0.1, "°C", "temperature"),
    _ro_sensor(0x0015, "suction_gas_temp", "Suction Gas Temperature", 0.5, "°C", "temperature", DataType.INT16),
    _ro_sensor(0x0016, "coil_temp", "Coil Temperature", 0.5, "°C", "temperature", DataType.INT16),
    _ro_sensor(0x001B, "exhaust_temp", "Exhaust Temperature", 1, "°C", "temperature"),
    _ro_sensor(0x0022, "driving_temp", "Driving Temperature", 0.5, "°C", "temperature", DataType.INT16),
    _ro_sensor(0x0028, "evap_temp", "Evaporation Temperature", 0.1, "°C", "temperature", DataType.INT16),
    _ro_sensor(0x0029, "cond_temp", "Condensation Temperature", 0.1, "°C", "temperature", DataType.INT16),
    # System Measurements
    _ro_sensor(0x0017, "ac_voltage", "AC Voltage", 1, "V", "voltage"),
    _ro_sensor(0x0018, "pump_flow", "Pump Flow", 1, "m³/h"),
    _ro_sensor(0x0019, "heating_cooling_capacity", "Heating/Cooling Capacity", 1, "W", "power"),
    _ro_sensor(0x001A, "ac_current", "AC Current", 1, "A", "current", DataType.INT16, clamp_min=0),
    _ro_sensor(0x001C, "eev1_step", "EEV1 Step", 1, "steps"),
    _ro_sensor(0x001D, "eev2_step", "EEV2 Step", 1, "steps", data_type=DataType.INT16),
    _ro_sensor(0x001E, "compressor_frequency", "Compressor Frequency", 1, "Hz", "frequency"),
    _ro_sensor(0x0021, "dc_bus_voltage", "DC Bus Voltage", 1, "V", "voltage"),
    _ro_sensor(0x0023, "compressor_current", "Compressor Current", 1, "A", "current", DataType.INT16, clamp_min=0),
    _ro_sensor(0x0024, "target_frequency", "Target Frequency", 1, "Hz", "frequency"),
    _ro_sensor(0x0026, "dc_fan1_speed", "DC Fan 1 Speed", 1, "rpm"),
    _ro_sensor(0x0027, "dc_fan2_speed", "DC Fan 2 Speed", 1, "rpm"),
    _ro_sensor(0x002E, "dc_pump_speed", "DC Pump Speed", 1, "%"),
    # Pressure sensors: swapped in manufacturer's docs (0x002F=discharge, 0x0030=suction)
    _ro_sensor(0x002F, "discharge_pressure", "Discharge Pressure", 0.0069, "bar", "pressure"),
    _ro_sensor(0x0030, "suction_pressure", "Suction Pressure", 0.0069, "bar", "pressure"),
    _ro_sensor(0x0031, "dc_fan_target", "DC Fan Target", 1, "rpm"),
    # Inverter Status
    _ro_sensor(0x001F, "freq_conversion_failure_1", "Frequency Conversion Failure 1", 1),
    _ro_sensor(0x0020, "freq_conversion_failure_2", "Frequency Conversion Failure 2", 1),
    _ro_sensor(0x0025, "smart_grid_status", "Smart Grid Status", 1),
    _ro_sensor(0x002A, "freq_conversion_fault_high", "Freq. Conversion Fault High", 1),
    _ro_sensor(0x002B, "freq_conversion_fault_low", "Freq. Conversion Fault Low", 1),
)

_HEATING_AMBIENT_BINS: tuple[str, ...] = (
    "T>=14°C",
    "9..14°C",
    "4..9°C",
    "-5..4°C",
    "-10..-5°C",
    "-16..-10°C",
    "-23..-16°C",
    "T<-23°C",
)

_COOLING_AMBIENT_BINS: tuple[str, ...] = (
    "T>=38°C",
    "30..38°C",
    "25..30°C",
    "T<25°C",
)

_CHICO_MODEL_OPTIONS: dict[int, str] = {
    1: "A102508",
    2: "A202508",
    3: "A103008",
    4: "A203008",
    5: "A104008",
    6: "A204008",
    7: "A105008",
    8: "A205008",
    9: "A106008",
    10: "A206008",
}

_DC_PUMP_MODE_OPTIONS: dict[int, str] = {
    0: "Manual",
    1: "Auto",
}


def _expert_sensor(
    address: int,
    key: str,
    name: str,
    scale: float | int = 1,
    unit: str | None = None,
    min_value: float | None = None,
    max_value: float | None = None,
    step: float = 1.0,
    device_class: str | None = None,
    data_type: DataType = DataType.UINT16,
    raw_offset: float | int = 0,
    bit_mask: int | None = None,
    options: Mapping[int, str] | None = None,
    enabled_default: bool = False,
    writable: bool = True,
) -> SensorSpec:
    """Create a read-only CHICO expert parameter SensorSpec (hidden by default in HA)."""
    return SensorSpec(
        key=key,
        name=name,
        address=address,
        space=RegisterSpace.HOLDING_REGISTER,
        data_type=data_type,
        scale=scale,
        unit=unit,
        device_class=device_class,
        state_class="none",
        diagnostic=True,
        raw_offset=raw_offset,
        bit_mask=bit_mask,
        options=options,
        min_value=min_value,
        max_value=max_value,
        step=step,
        writable=writable,
        enabled_default=enabled_default,
    )


def _ambient_curve(
    start_address: int,
    codes: tuple[str, ...],
    key_prefix: str,
    name_prefix: str,
    bins: tuple[str, ...],
    *,
    scale: float | int = 1,
    unit: str | None = None,
    min_value: float | None = None,
    max_value: float | None = None,
    step: float = 1.0,
    device_class: str | None = None,
    data_type: DataType = DataType.UINT16,
    start_index: int = 0,
    enabled_default: bool = False,
    writable: bool = True,
    address_offset: int = 0,
) -> tuple[SensorSpec, ...]:
    """Generate ambient-temperature indexed curve specs concisely."""
    return tuple(
        _expert_sensor(
            start_address + offset,
            f"{code.lower()}_{key_prefix}_{start_index + address_offset + offset}",
            f"{code} {name_prefix} {start_index + address_offset + offset} ({bins[address_offset + offset]})",
            scale=scale,
            unit=unit,
            min_value=min_value,
            max_value=max_value,
            step=step,
            device_class=device_class,
            data_type=data_type,
            enabled_default=enabled_default,
            writable=writable,
        )
        for offset, code in enumerate(codes)
    )


def _timeband_sensors() -> tuple[SensorSpec, ...]:
    """Generate Timeband 1-3 schedule, setpoint, and weekday diagnostic sensors."""
    specs: list[SensorSpec] = []
    for tb in (1, 2, 3):
        sched_base = 0x0119 + (tb - 1) * 4
        specs.extend([
            _expert_sensor(sched_base + 0, f"timeband_{tb}_on_hour", f"Timeband {tb} ON Hour", 1, "h", 0, 23),
            _expert_sensor(sched_base + 1, f"timeband_{tb}_on_minute", f"Timeband {tb} ON Minute", 1, "min", 0, 59),
            _expert_sensor(sched_base + 2, f"timeband_{tb}_off_hour", f"Timeband {tb} OFF Hour", 1, "h", 0, 23),
            _expert_sensor(sched_base + 3, f"timeband_{tb}_off_minute", f"Timeband {tb} OFF Minute", 1, "min", 0, 59),
        ])
        temp_base = 0x01A4 + (tb - 1) * 3
        specs.extend([
            _expert_sensor(
                temp_base + 0,
                f"timeband_{tb}_hotwater_setp",
                f"Timeband {tb} Hot Water Setpoint",
                0.5,
                "°C",
                28.0,
                60.0,
                0.5,
                "temperature",
                bit_mask=0xFF,
            ),
            _expert_sensor(
                temp_base + 1,
                f"timeband_{tb}_heat_setp",
                f"Timeband {tb} Heating Setpoint",
                0.5,
                "°C",
                15.0,
                50.0,
                0.5,
                "temperature",
                bit_mask=0xFF,
            ),
            _expert_sensor(
                temp_base + 2,
                f"timeband_{tb}_cool_setp",
                f"Timeband {tb} Cooling Setpoint",
                0.5,
                "°C",
                7.0,
                30.0,
                0.5,
                "temperature",
                bit_mask=0xFF,
            ),
            _expert_sensor(
                0x01AD + (tb - 1),
                f"timeband_{tb}_weekday",
                f"Timeband {tb} Weekday Mask",
                1,
                None,
                0,
                127,
            ),
        ])
    return tuple(specs)


CHICO_EXPERT_SENSORS: tuple[SensorSpec, ...] = (
    # Defrost Settings (H01-H18)
    _expert_sensor(0x0037, "h01_defrost_freq", "H01 Defrost Frequency", 1, "Hz", 30, 120, 1, "frequency"),
    _expert_sensor(0x00D4, "h03_defrost_in_stp", "H03 Defrost Start Coil Temp", 1, "°C", -15, -1, 1, "temperature", DataType.INT16),
    _expert_sensor(0x00D5, "h04_defrost_exit_stp", "H04 Defrost Exit Coil Temp", 1, "°C", 1, 40, 1, "temperature"),
    _expert_sensor(0x003D, "h05_defrost_time", "H05 Defrost Max Time", 1, "min", 5, 20),
    _expert_sensor(0x00DB, "defrost_ambi_stp_00db", "Defrost Ambient Setpoint 3 (0x00DB / PDF: H04)", 1, "°C", -30, 30, 1, "temperature", DataType.INT16),
    _expert_sensor(0x00D6, "h07_defrost_ambi_coil_1", "H07 Defrost Ambient-Coil Diff 1", 1, "°C", 0, 30, 1, "temperature"),
    _expert_sensor(0x0038, "h08_defrost_period_1", "H08 Defrost Period 1", 1, "min", 10, 120),
    _expert_sensor(0x00D9, "h09_defrost_ambi_stp_1", "H09 Defrost Ambient Setpoint 1", 1, "°C", -30, 30, 1, "temperature", DataType.INT16),
    _expert_sensor(0x00D7, "h10_defrost_ambi_coil_2", "H10 Defrost Ambient-Coil Diff 2", 1, "°C", 0, 30, 1, "temperature"),
    _expert_sensor(0x0039, "h11_defrost_period_2", "H11 Defrost Period 2", 1, "min", 10, 120),
    _expert_sensor(0x00DA, "h12_defrost_ambi_stp_2", "H12 Defrost Ambient Setpoint 2", 1, "°C", -30, 30, 1, "temperature", DataType.INT16),
    _expert_sensor(0x00D8, "h13_defrost_ambi_coil_3", "H13 Defrost Ambient-Coil Diff 3", 1, "°C", 0, 30, 1, "temperature"),
    _expert_sensor(0x003A, "h14_defrost_period_3", "H14 Defrost Period 3", 1, "min", 10, 120),
    _expert_sensor(0x003B, "h15_comp_total_run", "H15 Defrost Comp Total Run", 5, "min", 5, 300, 5),
    _expert_sensor(0x003C, "h16_comp_continuous_run", "H16 Defrost Comp Continuous Run", 1, "min", 5, 90),
    _expert_sensor(0x01B0, "h17_def_fan_high_press", "H17 Defrost Fan High Pressure", 1, "bar", 20, 40, 1, "pressure"),
    _expert_sensor(0x01B1, "h18_def_fan_speed", "H18 Defrost Fan Speed", 10, "rpm", 200, 1000, 10),
    # Main Expansion Valve Settings (A01-A51)
    _expert_sensor(0x003E, "a01_mv_period", "A01 MV Adjust Period", 1, "s", 20, 90),
    *_ambient_curve(0x00DC, ("A02", "A03", "A04", "A05", "A06", "A07", "A08", "A09"), "mv_heating_sh", "MV Heating Superheat", _HEATING_AMBIENT_BINS, scale=1, unit="°C", min_value=-5, max_value=10, device_class="temperature", data_type=DataType.INT16, start_index=1),
    *_ambient_curve(0x00E4, ("A10", "A11", "A12", "A13"), "mv_cooling_sh", "MV Cooling Superheat", _COOLING_AMBIENT_BINS, scale=1, unit="°C", min_value=-5, max_value=10, device_class="temperature", data_type=DataType.INT16, start_index=1),
    *_ambient_curve(0x003F, ("A14", "A15", "A16", "A17", "A18", "A19", "A20", "A21"), "mv_heat_initial", "MV Heat Initial", _HEATING_AMBIENT_BINS, scale=2, unit="steps", min_value=0, max_value=480, step=2),
    *_ambient_curve(0x0047, ("A22", "A23", "A24", "A25"), "mv_cool_initial", "MV Cool Initial", _COOLING_AMBIENT_BINS, scale=2, unit="steps", min_value=0, max_value=480, step=2),
    *_ambient_curve(0x004B, ("A26", "A27", "A28", "A29", "A30", "A31", "A32", "A33"), "mv_water_init", "MV Water Initial", _HEATING_AMBIENT_BINS, scale=2, unit="steps", min_value=0, max_value=480, step=2),
    *_ambient_curve(0x0053, ("A34", "A35", "A36", "A37", "A38", "A39", "A40", "A41"), "mv_heat_lower", "MV Heat Lower", _HEATING_AMBIENT_BINS, scale=2, unit="steps", min_value=0, max_value=480, step=2),
    _expert_sensor(0x00E8, "a42_mv_exhaust_stp", "A42 MV Exhaust Setpoint", 1, "°C", 70, 125, 1, "temperature"),
    _expert_sensor(0x005B, "a43_mv_defrost_open", "A43 MV Defrost Opening", 2, "steps", 0, 480, 2),
    _expert_sensor(0x005C, "a44_mv_water_lower", "A44 MV Water Lower Limit", 2, "steps", 0, 150, 2),
    _expert_sensor(0x005D, "a46_mv_manual_open", "A46 MV Manual Opening", 2, "steps", 20, 450, 2),
    _expert_sensor(0x005E, "a47_mv_sh_ratio", "A47 MV Superheat Ratio", 1, None, 1, 6),
    _expert_sensor(0x005F, "a48_mv_sh_diff", "A48 MV Superheat Diff", 1, None, 1, 180),
    _expert_sensor(0x0060, "a50_mv_comp_keep_time", "A50 MV Compressor Keep Time", 2, "s", 0, 500, 2),
    _expert_sensor(0x0061, "a51_mv_def_keep_time", "A51 MV Defrost Keep Time", 2, "s", 0, 500, 2),
    # Aux Expansion Valve Settings (B02-B93)
    _expert_sensor(0x0062, "b02_av_manual_open", "B02 AV Manual Opening", 2, "steps", 20, 450, 2),
    _expert_sensor(0x00E9, "b03_av_start_ambi", "B03 AV Start Ambient Temp", 1, "°C", 11, 45, 1, "temperature"),
    _expert_sensor(0x0063, "b04_av_exhaust_ratio", "B04 AV Exhaust Ratio", 1, None, 1, 6),
    _expert_sensor(0x0064, "b05_av_exhaust_diff", "B05 AV Exhaust Diff", 1, None, 0, 180),
    _expert_sensor(0x0065, "b06_av_sh_ratio", "B06 AV Superheat Ratio", 1, None, 1, 6),
    _expert_sensor(0x0066, "b07_av_sh_diff", "B07 AV Superheat Diff", 1, None, 0, 180),
    _expert_sensor(0x0067, "b08_av_period", "B08 AV Adjust Period", 1, "s", 10, 20),
    _expert_sensor(0x00EA, "b09_av_exhaust_stp", "B09 AV Exhaust Setpoint", 1, "°C", 70, 120, 1, "temperature"),
    _expert_sensor(0x00EB, "b10_av_off_exh_stp", "B10 AV Off Exhaust Setpoint", 1, "°C", 40, 70, 1, "temperature"),
    *_ambient_curve(0x00EC, ("B11", "B12", "B13", "B14", "B15", "B16", "B17", "B18"), "av_heating_sh", "AV Heating Superheat", _HEATING_AMBIENT_BINS, scale=1, unit="°C", min_value=-10, max_value=10, device_class="temperature", data_type=DataType.INT16, start_index=1),
    *_ambient_curve(0x0068, ("B19", "B20"), "av_heat_initial", "AV Heat Initial", _HEATING_AMBIENT_BINS, scale=2, unit="steps", min_value=0, max_value=480, step=2),
    *_ambient_curve(0x006A, ("B21", "B22", "B23", "B24", "B25", "B26"), "av_heat_initial", "AV Heat Initial", _HEATING_AMBIENT_BINS, scale=2, unit="steps", min_value=0, max_value=480, step=2, address_offset=2, writable=False),
    *_ambient_curve(0x0070, ("B27", "B28"), "av_water_initial", "AV Water Initial", _HEATING_AMBIENT_BINS, scale=2, unit="steps", min_value=0, max_value=480, step=2),
    *_ambient_curve(0x0072, ("B29", "B30", "B31", "B32", "B33", "B34"), "av_water_initial", "AV Water Initial", _HEATING_AMBIENT_BINS, scale=2, unit="steps", min_value=0, max_value=480, step=2, address_offset=2, writable=False),
    *_ambient_curve(0x0078, ("B35", "B36", "B37", "B38", "B39", "B40", "B41", "B42"), "av_heat_lower", "AV Heat Lower", _HEATING_AMBIENT_BINS, scale=2, unit="steps", min_value=0, max_value=480, step=2),
    _expert_sensor(0x0080, "b43_av_defrost_open", "B43 AV Defrost Opening", 2, "steps", 0, 480, 2),
    _expert_sensor(0x0081, "b44_av_cool_open", "B44 AV Cool Opening", 2, "steps", 0, 480, 2),
    *_ambient_curve(0x0098, ("B45", "B46", "B47", "B48", "B49", "B50", "B51", "B52"), "av_water_lower", "AV Water Lower", _HEATING_AMBIENT_BINS, scale=2, unit="steps", min_value=0, max_value=480, step=2),
    *_ambient_curve(0x00A0, ("B53", "B54", "B55", "B56", "B57", "B58", "B59", "B60"), "av_heat_exhaust", "AV Heat Exhaust", _HEATING_AMBIENT_BINS, scale=1, unit="°C", min_value=50, max_value=125, device_class="temperature"),
    *_ambient_curve(0x00A8, ("B61", "B62", "B63", "B64", "B65", "B66", "B67", "B68"), "av_water_exhaust", "AV Water Exhaust", _HEATING_AMBIENT_BINS, scale=1, unit="°C", min_value=50, max_value=125, device_class="temperature"),
    *_ambient_curve(0x00B0, ("B69", "B70", "B71", "B72"), "av_cool_exhaust", "AV Cool Exhaust", _COOLING_AMBIENT_BINS, scale=1, unit="°C", min_value=50, max_value=125, device_class="temperature"),
    _expert_sensor(0x00B4, "b73_av_open_delay", "B73 AV Open Delay", 1, "s", 0, 180),
    _expert_sensor(0x00B5, "b75_av_off_exh_diff", "B75 AV Off Exhaust Diff", 1, "°C", 0, 30, 1, "temperature"),
    *_ambient_curve(0x00B6, ("B76", "B77", "B78", "B79", "B80", "B81", "B82", "B83"), "av_heat_exh_diff", "AV Heat Exhaust Diff", _HEATING_AMBIENT_BINS, scale=1, unit="°C", min_value=0, max_value=125, device_class="temperature"),
    *_ambient_curve(0x00BE, ("B84", "B85", "B86", "B87", "B88", "B89", "B90", "B91"), "av_water_exh_diff", "AV Water Exhaust Diff", _HEATING_AMBIENT_BINS, scale=1, unit="°C", min_value=0, max_value=125, device_class="temperature"),
    _expert_sensor(0x01B5, "b93_av_init_outlet_stp", "B93 AV Init Outlet Setpoint", 1, "°C", 20, 60, 1, "temperature"),
    # DC / AC Fan Settings (D03-D22)
    _expert_sensor(0x0086, "d03_cool_dcfan_max_speed", "D03 Cool DC Fan Max Speed", 10, "rpm", 0, 1000, 10),
    _expert_sensor(0x0087, "d04_cool_dcfan_min_speed", "D04 Cool DC Fan Min Speed", 10, "rpm", 0, 1000, 10),
    _expert_sensor(0x0088, "d05_cool_dcfan_high_press", "D05 Cool DC Fan High Pressure", 1, "bar", 10, 40, 1, "pressure"),
    _expert_sensor(0x0089, "d06_cool_dcfan_open_diff", "D06 Cool DC Fan Open Diff", 1, "bar", 2, 10, 1, "pressure"),
    _expert_sensor(0x008A, "d07_cool_dcfan_close_diff", "D07 Cool DC Fan Close Diff", 1, "bar", 2, 10, 1, "pressure"),
    _expert_sensor(0x008B, "d08_cool_dcfan_init_speed", "D08 Cool DC Fan Init Speed", 10, "rpm", 0, 1000, 10),
    _expert_sensor(0x008C, "d09_heat_dcfan_max_speed", "D09 Heat DC Fan Max Speed", 10, "rpm", 0, 1000, 10),
    _expert_sensor(0x008D, "d10_heat_dcfan_min_speed", "D10 Heat DC Fan Min Speed", 10, "rpm", 0, 1000, 10),
    _expert_sensor(0x008E, "d11_heat_dcfan_low_press", "D11 Heat DC Fan Low Pressure", 1, "bar", 5, 15, 1, "pressure"),
    _expert_sensor(0x008F, "d12_heat_dcfan_open_diff", "D12 Heat DC Fan Open Diff", 1, "bar", 2, 10, 1, "pressure"),
    _expert_sensor(0x0090, "d13_heat_dcfan_close_diff", "D13 Heat DC Fan Close Diff", 1, "bar", 2, 10, 1, "pressure"),
    _expert_sensor(0x0091, "d14_heat_dcfan_init_speed", "D14 Heat DC Fan Init Speed", 10, "rpm", 0, 1000, 10),
    _expert_sensor(0x0092, "d15_dcfan_adjust_period", "D15 DC Fan Adjust Period", 1, "s", 0, 30),
    _expert_sensor(0x0093, "d16_dcfan_adjust_speed_1", "D16 DC Fan Adjust Speed 1 (Diff>=200)", 1, "rpm", 0, 100),
    _expert_sensor(0x0094, "d17_dcfan_adjust_speed_2", "D17 DC Fan Adjust Speed 2 (100..200)", 1, "rpm", 0, 100),
    _expert_sensor(0x0095, "d18_dcfan_adjust_speed_3", "D18 DC Fan Adjust Speed 3 (50..100)", 1, "rpm", 0, 100),
    _expert_sensor(0x0096, "d19_dcfan_adjust_speed_4", "D19 DC Fan Adjust Speed 4 (20..50)", 1, "rpm", 0, 100),
    _expert_sensor(0x0097, "d20_dcfan_adjust_speed_5", "D20 DC Fan Adjust Speed 5 (5..20)", 1, "rpm", 0, 100),
    _expert_sensor(0x00F4, "d21_ac_fan_switch_ambi_1", "D21 AC Fan Switch Ambient 1", 1, "°C", -10, 50, 1, "temperature", DataType.INT16),
    _expert_sensor(0x00F5, "d22_ac_fan_switch_ambi_2", "D22 AC Fan Switch Ambient 2", 1, "°C", -10, 50, 1, "temperature", DataType.INT16),
    # Factory / Protection / Pump / Calibration (F02-F56)
    _expert_sensor(0x0082, "f02_hp_protect_value", "F02 High Pressure Protect", 0.1, "bar", 25.0, 50.0, 0.1, "pressure", raw_offset=250),
    _expert_sensor(0x0083, "f03_hp_recover_value", "F03 High Pressure Recover", 0.1, "bar", 25.0, 50.0, 0.1, "pressure", raw_offset=250),
    _expert_sensor(0x0084, "f04_lp_protect_value", "F04 Low Pressure Protect", 0.1, "bar", 0.0, 20.0, 0.1, "pressure"),
    _expert_sensor(0x0085, "f05_lp_recover_value", "F05 Low Pressure Recover", 0.1, "bar", 0.0, 20.0, 0.1, "pressure"),
    _expert_sensor(0x0186, "f13_dc_pump_mode", "F13 DC Pump Mode", 1, None, 0, 1, 1, options=_DC_PUMP_MODE_OPTIONS),
    _expert_sensor(0x0187, "f14_dc_pump_cycle", "F14 DC Pump Cycle", 1, "s", 10, 120),
    _expert_sensor(0x0188, "f15_dc_pump_freq_set", "F15 DC Pump Manual Speed", 1, "%", 10, 100),
    _expert_sensor(0x0189, "f16_dc_pump_max_freq", "F16 DC Pump Max Speed", 1, "%", 10, 100),
    _expert_sensor(0x018A, "f17_dc_pump_min_freq", "F17 DC Pump Min Speed", 1, "%", 10, 100),
    _expert_sensor(0x018B, "f18_dc_pump_scale_factor", "F18 DC Pump Scale Factor", 1, None, 1, 10),
    _expert_sensor(0x018C, "f19_dc_pump_diff", "F19 DC Pump Diff", 1, None, 0, 100),
    _expert_sensor(0x018E, "f21_comp_freq_scale_factor", "F21 Compressor Freq Scale Factor", 1, None, 1, 10),
    _expert_sensor(0x018F, "f22_comp_freq_diff", "F22 Compressor Freq Diff", 1, None, 0, 100),
    _expert_sensor(0x0194, "f27_limit_freq_temp_diff", "F27 Limit Freq Temp Diff", 1, "°C", 5, 20, 1, "temperature"),
    _expert_sensor(0x0195, "f28_dec_freq_temp_diff", "F28 Decrease Freq Temp Diff", 1, "°C", 5, 20, 1, "temperature"),
    _expert_sensor(0x0196, "f29_limit_freq_outlet_low", "F29 Limit Freq Outlet Low", 1, "°C", 0, 20, 1, "temperature"),
    _expert_sensor(0x0197, "f30_dec_freq_outlet_low", "F30 Decrease Freq Outlet Low", 1, "°C", 0, 20, 1, "temperature"),
    _expert_sensor(0x0198, "f31_limit_freq_outlet_high", "F31 Limit Freq Outlet High", 1, "°C", 30, 80, 1, "temperature"),
    _expert_sensor(0x0199, "f32_dec_freq_outlet_high", "F32 Decrease Freq Outlet High", 1, "°C", 30, 80, 1, "temperature"),
    _expert_sensor(0x019F, "f35_antifreeze_cycle", "F35 Antifreeze Cycle", 1, "min", 1, 60),
    _expert_sensor(0x01A0, "f36_three_way_valve_cycle", "F36 3-Way Valve Cycle", 1, "h", 1, 60),
    _expert_sensor(0x01A1, "f37_pump_cycle_in_error", "F37 Pump Cycle In Error", 1, "min", 1, 120),
    _expert_sensor(0x01A2, "f38_comp_freq_cycle", "F38 Compressor Freq Cycle", 1, "s", 20, 60),
    _expert_sensor(0x00C7, "f39_ac_constant_temp_diff", "F39 AC Constant Temp Diff", 1, "°C", 1, 10, 1, "temperature"),
    _expert_sensor(0x00C9, "f40_wt_constant_temp_diff", "F40 Water Tank Constant Temp Diff", 1, "°C", 0, 10, 1, "temperature"),
    _expert_sensor(0x01A3, "f41_air_too_low_stp", "F41 Air Too Low Setpoint", 1, "°C", -40, 0, 1, "temperature", DataType.INT16),
    _expert_sensor(0x00D2, "f42_water_temp_offset", "F42 Water Temp Offset", 1, "°C", 0, 50, 1, "temperature"),
    _expert_sensor(0x00D3, "f43_inlet_temp_offset", "F43 Inlet Temp Offset", 1, "°C", 0, 50, 1, "temperature"),
    _expert_sensor(0x00CD, "f44_wt_temp_calibration", "F44 Water Tank Temp Calibration", 1, "°C", -30, 30, 1, "temperature", DataType.INT16),
    _expert_sensor(0x00CE, "f45_inlet_temp_calibration", "F45 Inlet Temp Calibration", 1, "°C", -30, 30, 1, "temperature", DataType.INT16),
    _expert_sensor(0x00CF, "f46_outlet_temp_calibration", "F46 Outlet Temp Calibration", 1, "°C", -30, 30, 1, "temperature", DataType.INT16),
    _expert_sensor(0x01B2, "f47_high_press_adjust", "F47 High Pressure Calibration", 1, None, -50, 50, 1, data_type=DataType.INT16),
    _expert_sensor(0x01B3, "f48_low_press_adjust", "F48 Low Pressure Calibration", 1, None, -50, 50, 1, data_type=DataType.INT16),
    _expert_sensor(0x00D0, "f49_wt_temp_offset_stp", "F49 Water Tank Temp Offset Setpoint", 1, "°C", 30, 55, 1, "temperature"),
    _expert_sensor(0x00D1, "f50_inlet_temp_offset_stp", "F50 Inlet Temp Offset Setpoint", 1, "°C", 30, 55, 1, "temperature"),
    _expert_sensor(0x01B4, "f51_air_too_low_diff", "F51 Air Too Low Diff", 1, "°C", 1, 10, 1, "temperature"),
    _expert_sensor(0x01B7, "f52_outlet_temp_offset", "F52 Outlet Temp Offset", 1, "°C", 0, 50, 1, "temperature"),
    _expert_sensor(0x01B6, "f53_outlet_temp_offset_stp", "F53 Outlet Temp Offset Setpoint", 1, "°C", 30, 55, 1, "temperature"),
    _expert_sensor(0x01B8, "f54_heat_upper_limit_stp", "F54 Heat Upper Limit Setpoint", 1, "°C", 10, 80, 1, "temperature"),
    _expert_sensor(0x01B9, "f55_cool_lower_limit_stp", "F55 Cool Lower Limit Setpoint", 1, "°C", 7, 30, 1, "temperature"),
    _expert_sensor(0x01BA, "f56_model_selection", "F56 Model Selection", 1, None, 1, 10, 1, options=_CHICO_MODEL_OPTIONS),
    # Compressor Frequency Curves & Exhaust Thresholds (R00-R94 + Manual Freq)
    _expert_sensor(0x00F6, "r16_exhaust_high_tp0", "R16 Exhaust High TP0", 1, "°C", 50, 125, 1, "temperature"),
    _expert_sensor(0x00F7, "r17_exhaust_high_tp1", "R17 Exhaust High TP1", 1, "°C", 50, 125, 1, "temperature"),
    _expert_sensor(0x00F8, "r18_exhaust_high_tp2", "R18 Exhaust High TP2", 1, "°C", 50, 125, 1, "temperature"),
    _expert_sensor(0x00F9, "r19_exhaust_high_tp3", "R19 Exhaust High TP3", 1, "°C", 50, 125, 1, "temperature"),
    _expert_sensor(0x00FA, "r20_exhaust_high_tp4", "R20 Exhaust High TP4", 1, "°C", 50, 125, 1, "temperature"),
    _expert_sensor(0x00FB, "manual_frequency_setting", "Manual Frequency Setting", 1, "Hz", 30, 120, 1, "frequency"),
    *_ambient_curve(0x00FC, ("R00", "R01", "R02", "R03", "R30", "R31", "R32", "R33"), "water_freq", "Normal Water Freq", _HEATING_AMBIENT_BINS, scale=1, unit="Hz", min_value=30, max_value=120, device_class="frequency"),
    *_ambient_curve(0x0104, ("R04", "R05", "R06", "R07", "R08", "R09", "R10", "R11"), "heat_freq", "Normal Heat Freq", _HEATING_AMBIENT_BINS, scale=1, unit="Hz", min_value=30, max_value=120, device_class="frequency"),
    *_ambient_curve(0x010C, ("R12", "R13", "R14", "R15"), "cool_freq", "Normal Cool Freq", _COOLING_AMBIENT_BINS, scale=1, unit="Hz", min_value=30, max_value=120, device_class="frequency"),
    _expert_sensor(0x0110, "r21_freq_adj_lower_limit", "R21 Freq Adj Lower Limit", 1, "Hz", 0, 125, 1, "frequency"),
    _expert_sensor(0x0111, "r22_freq_adj_lower_limit", "R22 Freq Adj Lower Limit", 1, "Hz", 0, 125, 1, "frequency"),
    _expert_sensor(0x0112, "r23_freq_adj_lower_limit", "R23 Freq Adj Lower Limit", 1, "Hz", 0, 125, 1, "frequency"),
    _expert_sensor(0x0113, "r24_freq_adj_lower_limit", "R24 Freq Adj Lower Limit", 1, "Hz", 0, 125, 1, "frequency"),
    _expert_sensor(0x0114, "r25_freq_adj_upper_limit", "R25 Freq Adj Upper Limit", 1, "Hz", 0, 125, 1, "frequency"),
    _expert_sensor(0x0115, "r26_freq_adj_upper_limit", "R26 Freq Adj Upper Limit", 1, "Hz", 0, 125, 1, "frequency"),
    _expert_sensor(0x0116, "r27_freq_adj_upper_limit", "R27 Freq Adj Upper Limit", 1, "Hz", 0, 125, 1, "frequency"),
    _expert_sensor(0x0117, "r28_freq_adj_upper_limit", "R28 Freq Adj Upper Limit", 1, "Hz", 0, 125, 1, "frequency"),
    *_ambient_curve(0x012D, ("R34", "R35", "R36", "R37", "R38", "R39", "R40", "R41"), "eco_water_freq", "ECO Water Freq", _HEATING_AMBIENT_BINS, scale=1, unit="Hz", min_value=30, max_value=120, device_class="frequency"),
    *_ambient_curve(0x0135, ("R42", "R43", "R44", "R45", "R46", "R47", "R48", "R49"), "eco_heat_freq", "ECO Heat Freq", _HEATING_AMBIENT_BINS, scale=1, unit="Hz", min_value=30, max_value=120, device_class="frequency"),
    *_ambient_curve(0x013D, ("R50", "R51", "R52", "R53"), "eco_cool_freq", "ECO Cool Freq", _COOLING_AMBIENT_BINS, scale=1, unit="Hz", min_value=30, max_value=120, device_class="frequency"),
    *_ambient_curve(0x0141, ("R54", "R55", "R56", "R57", "R58", "R59", "R60", "R61"), "night_water_freq", "Night Water Freq", _HEATING_AMBIENT_BINS, scale=1, unit="Hz", min_value=30, max_value=120, device_class="frequency"),
    *_ambient_curve(0x0149, ("R62", "R63", "R64", "R65", "R66", "R67", "R68", "R69"), "night_heat_freq", "Night Heat Freq", _HEATING_AMBIENT_BINS, scale=1, unit="Hz", min_value=30, max_value=120, device_class="frequency"),
    *_ambient_curve(0x0151, ("R70", "R71", "R72", "R73"), "night_cool_freq", "Night Cool Freq", _COOLING_AMBIENT_BINS, scale=1, unit="Hz", min_value=30, max_value=120, device_class="frequency"),
    *_ambient_curve(0x0155, ("R74", "R75", "R76", "R77", "R78", "R79", "R80", "R81"), "test_water_freq", "Test Water Freq", _HEATING_AMBIENT_BINS, scale=1, unit="Hz", min_value=30, max_value=120, device_class="frequency"),
    *_ambient_curve(0x015D, ("R82", "R83", "R84", "R85", "R86", "R87", "R88", "R89"), "test_heat_freq", "Test Heat Freq", _HEATING_AMBIENT_BINS, scale=1, unit="Hz", min_value=30, max_value=120, device_class="frequency"),
    *_ambient_curve(0x0165, ("R90", "R91", "R92", "R93"), "test_cool_freq", "Test Cool Freq", _COOLING_AMBIENT_BINS, scale=1, unit="Hz", min_value=30, max_value=120, device_class="frequency"),
    _expert_sensor(0x01BB, "r94_oil_return_freq", "R94 Oil Return Frequency", 1, "Hz", 10, 70, 1, "frequency"),
    # Timeband 1-3 Schedule & Setpoints
    *_timeband_sensors(),
)

CHICO_SENSORS: tuple[SensorSpec, ...] = CHICO_CORE_SENSORS + CHICO_EXPERT_SENSORS


def _bin_sensor(key: str, address: int, bit: int, name: str) -> BinarySensorSpec:
    """Create a CHICO bitfield BinarySensorSpec."""
    return BinarySensorSpec(
        key=key,
        name=name,
        address=address,
        bit=bit,
        source_key=CHICO_STATUS_REGISTER_KEYS[address],
        space=RegisterSpace.HOLDING_REGISTER,
        diagnostic=key.startswith("error_") or key == "alarm_stop",
    )


CHICO_CORE_BINARY_SENSORS: tuple[BinarySensorSpec, ...] = (
    # Working Status Mark (0x0003)
    _bin_sensor("hotwater_demand", 0x0003, 0, "Hot Water Demand"),
    _bin_sensor("heating_demand", 0x0003, 1, "Heating Demand"),
    _bin_sensor("cooling_demand", 0x0003, 5, "Cooling Demand"),
    _bin_sensor("antilegionella_active", 0x0003, 4, "Antilegionella Active"),
    _bin_sensor("defrost_active", 0x0003, 7, "Defrost Active"),
    _bin_sensor("alarm_stop", 0x0003, 6, "Alarm Stop"),
    # Switching Input Symbol (0x0002)
    _bin_sensor("ac_linkage_switch", 0x0002, 0, "A/C Linkage Switch"),
    _bin_sensor("linkage_switch", 0x0002, 1, "Linkage Switch"),
    _bin_sensor("heating_linkage", 0x0002, 2, "Heating Linkage"),
    _bin_sensor("cooling_linkage", 0x0002, 3, "Cooling Linkage"),
    _bin_sensor("flow_switch", 0x0002, 4, "Flow Switch"),
    _bin_sensor("high_pressure_switch", 0x0002, 5, "High Pressure Switch"),
    _bin_sensor("phase_sequence_ok", 0x0002, 6, "Phase Sequence OK"),
    # Output Symbol 1 (0x0004)
    _bin_sensor("compressor_running", 0x0004, 0, "Compressor"),
    _bin_sensor("fan_running", 0x0004, 5, "Fan"),
    _bin_sensor("valve_4way", 0x0004, 6, "4-Way Valve"),
    _bin_sensor("fan_high_speed", 0x0004, 7, "Fan High Speed"),
    # Output Symbol 2 (0x0005)
    _bin_sensor("chassis_heater", 0x0005, 0, "Chassis Heater"),
    _bin_sensor("heating_heater", 0x0005, 5, "Heating Heater"),
    _bin_sensor("valve_3way", 0x0005, 6, "3-Way Valve"),
    _bin_sensor("hotwater_heater", 0x0005, 7, "Hot Water Heater"),
    # Output Symbol 3 (0x0006)
    _bin_sensor("ac_pump", 0x0006, 0, "A/C Pump"),
    _bin_sensor("crank_heater", 0x0006, 1, "Crank Heater"),
    _bin_sensor("assistant_solenoid", 0x0006, 5, "Assistant Solenoid Valve"),
    _bin_sensor("pump_running", 0x0006, 6, "Circulation Pump"),
    # Failure Symbol 1 (0x0007)
    _bin_sensor("error_hotwater_sensor", 0x0007, 0, "Hot Water Temp Sensor Error"),
    _bin_sensor("error_ambient_sensor", 0x0007, 1, "Ambient Temp Sensor Error"),
    _bin_sensor("error_coil_sensor", 0x0007, 2, "Coil Temp Sensor Error"),
    _bin_sensor("error_outlet_sensor", 0x0007, 4, "Outlet Temp Sensor Error"),
    _bin_sensor("error_high_pressure_sensor", 0x0007, 5, "High Pressure Sensor Error"),
    _bin_sensor("error_phase_sequence", 0x0007, 7, "Phase Sequence Error"),
    # Failure Symbol 2 (0x0008)
    _bin_sensor("error_water_flow", 0x0008, 0, "Water Flow Error"),
    _bin_sensor("error_high_temp_heating", 0x0008, 2, "High Temp Protection (Heating Outlet)"),
    # Failure Symbol 3 (0x0009)
    _bin_sensor("error_outlet_gas_temp", 0x0009, 6, "Outlet Gas Temp Error"),
    # Failure Symbol 4 (0x000A)
    _bin_sensor("error_inlet_sensor", 0x000A, 0, "Water Inlet Temp Sensor Error"),
    _bin_sensor("error_exhaust_high", 0x000A, 1, "Exhaust Temperature Too High"),
    _bin_sensor("error_low_temp_cooling", 0x000A, 5, "Low Temp Protection (Cooling Outlet)"),
    _bin_sensor("error_inlet_gas_sensor", 0x000A, 6, "Inlet Gas Temp Sensor Error"),
    # Failure Symbol 5 (0x000B)
    _bin_sensor("error_low_pressure", 0x000B, 0, "Low Pressure Protection"),
    _bin_sensor("error_high_pressure", 0x000B, 1, "High Pressure Protection"),
    _bin_sensor("error_coil_temp_high", 0x000B, 2, "Coil Temperature Too High"),
    _bin_sensor("error_high_pressure_sensor2", 0x000B, 6, "High Pressure Sensor Failure"),
    _bin_sensor("error_low_pressure_sensor", 0x000B, 7, "Low Pressure Sensor Failure"),
    # Failure Symbol 6 (0x000C)
    _bin_sensor("error_antifreeze_secondary", 0x000C, 4, "Secondary Antifreeze Protection"),
    _bin_sensor("error_antifreeze_primary", 0x000C, 5, "Primary Antifreeze Protection"),
    # Failure Symbol 7 (0x000D)
    _bin_sensor("error_ambient_temp_low", 0x000D, 1, "Ambient Temperature Too Low"),
    _bin_sensor("error_inverter_module", 0x000D, 4, "Frequency Conversion Module Fault"),
    _bin_sensor("error_dc_fan2", 0x000D, 5, "DC Fan 2 Failure"),
    _bin_sensor("error_dc_fan1", 0x000D, 6, "DC Fan 1 Failure"),
)


def _expert_bit(
    key: str,
    address: int,
    bit: int,
    name: str,
    *,
    inverted: bool = False,
    enabled_default: bool = False,
    writable: bool = True,
) -> BinarySensorSpec:
    """Create a read-only CHICO control/schedule bitfield BinarySensorSpec (hidden by default in HA)."""
    return BinarySensorSpec(
        key=key,
        name=name,
        address=address,
        bit=bit,
        source_key=CHICO_CONTROL_REGISTER_KEYS[address],
        space=RegisterSpace.HOLDING_REGISTER,
        inverted=inverted,
        diagnostic=True,
        coil_address=(address << 4) + bit,
        writable=writable,
        enabled_default=enabled_default,
    )


CHICO_EXPERT_BINARY_SENSORS: tuple[BinarySensorSpec, ...] = (
    # Parameter Marker Definition (0x0032; bit 0 is writable Power switch)
    _expert_bit("a45_mv_mode_manual", 0x0032, 1, "A45 MV Manual Mode"),
    _expert_bit("manual_freq_selection", 0x0032, 2, "Manual Frequency Selection"),
    _expert_bit("b01_av_mode_manual", 0x0032, 5, "B01 AV Manual Mode"),
    _expert_bit("b93_av_init_outlet_adjustable", 0x0032, 6, "B93 AV Init Outlet Stp Adjustable"),
    # Control Mark 1 (0x0033; bit 7 is Failure Reset button)
    _expert_bit("r29_constant_freq_adj", 0x0033, 0, "R29 Constant Frequency Adjustment"),
    _expert_bit("f01_pressure_switch_enable", 0x0033, 1, "F01 Pressure Switch Enable"),
    # Bit 2 is active-low in V1.2 PDF ("0-use, 1-Unuse"), inverted=True exposes ON = enabled
    _expert_bit("b74_av_cool_enable", 0x0033, 2, "B74 AV Cool Enable", inverted=True),
    _expert_bit("b92_av_control_exhaust", 0x0033, 3, "B92 AV Exhaust Control Mode"),
    _expert_bit("d01_dcfan1_enable", 0x0033, 4, "D01 DC Fan 1 Enable"),
    _expert_bit("d02_dcfan2_enable", 0x0033, 5, "D02 DC Fan 2 Enable"),
    _expert_bit("parameters_reset_flag", 0x0033, 6, "Parameters Reset Flag", writable=False),
    # Control Mark 2 deduced bits (0x0034; bits 0-1 are switches; bits 2-4 Invalid in V1.2 PDF)
    _expert_bit("night_clock_mode", 0x0034, 2, "Night Clock Mode (Unconfirmed)", writable=False),
    _expert_bit("load_fast_check", 0x0034, 3, "Load Fast Check (Unconfirmed)", writable=False),
    _expert_bit("forced_defrost", 0x0034, 4, "Forced Defrost Flag (Unconfirmed)", writable=False),
    # Timeband Enable Flags (0x0035)
    _expert_bit("timeband_1_enable", 0x0035, 0, "Timeband 1 Enable"),
    _expert_bit("timeband_2_enable", 0x0035, 1, "Timeband 2 Enable"),
    _expert_bit("timeband_3_enable", 0x0035, 2, "Timeband 3 Enable"),
)

CHICO_BINARY_SENSORS: tuple[BinarySensorSpec, ...] = (
    CHICO_CORE_BINARY_SENSORS + CHICO_EXPERT_BINARY_SENSORS
)

CHICO_SWITCHES: tuple[SwitchSpec, ...] = (
    SwitchSpec(
        key="power_switch",
        name="Power",
        address=0x0032,
        bit=0,
        space=RegisterSpace.HOLDING_REGISTER,
        coil_address=0x0320,
        cache_key="_control_0032",
        is_config=False,
    ),
    SwitchSpec(
        key="antilegionella_enable",
        name="Antilegionella Enable",
        address=0x0034,
        bit=0,
        space=RegisterSpace.HOLDING_REGISTER,
        cache_key="_control_0034",
        is_config=True,
    ),
    SwitchSpec(
        key="two_three_function",
        name="Two/Three Function",
        address=0x0034,
        bit=1,
        space=RegisterSpace.HOLDING_REGISTER,
        cache_key="_control_0034",
        is_config=True,
    ),
)

CHICO_BUTTONS: tuple[ButtonSpec, ...] = (
    ButtonSpec(
        key="failure_reset",
        name="Failure Reset",
        address=0x0033,
        bit=7,
        space=RegisterSpace.HOLDING_REGISTER,
        description="Reset all failures after fixing the cause",
        write_value=True,
        diagnostic=True,
    ),
)

CHICO_SELECTS: tuple[SelectSpec, ...] = (
    SelectSpec(
        key="unit_mode",
        name="Unit Mode",
        address=0x0036,
        options={
            0: "Hot Water Only",
            1: "Heating Only",
            2: "Cooling Only",
            3: "Heating + Hot Water",
            4: "Cooling + Hot Water",
        },
        is_config=False,
    ),
    SelectSpec(
        key="fan_mode",
        name="Fan Mode",
        address=0x0190,
        options={
            0: "Normal",
            1: "Economic",
            2: "Night",
            3: "Test",
        },
        is_config=True,
    ),
    SelectSpec(
        key="pump_mode",
        name="Pump Work Mode",
        address=0x019E,
        options={
            0: "Interval",
            1: "Normal",
            2: "Demand",
        },
        is_config=True,
    ),
)


def _num(
    address: int,
    key: str,
    name: str,
    scale: float | int,
    unit: str | None,
    min_value: float,
    max_value: float,
    step: float,
    device_class: str | None = None,
    data_type: DataType = DataType.UINT16,
    is_primary: bool = False,
    bit_mask: int | None = None,
) -> NumberSpec:
    """Create a CHICO NumberSpec with consistent metadata."""
    return NumberSpec(
        key=key,
        name=name,
        address=address,
        space=RegisterSpace.HOLDING_REGISTER,
        data_type=data_type,
        scale=scale,
        unit=unit,
        min_value=min_value,
        max_value=max_value,
        step=step,
        device_class=device_class,
        supports_temp_step_override=(device_class == "temperature" and step == 0.5),
        is_primary=is_primary,
        bit_mask=bit_mask,
    )


CHICO_NUMBERS: tuple[NumberSpec, ...] = (
    # Basic Configuration - P parameters (0x00CA-0x00CC store setpoint in lower 8 bits)
    _num(0x00CC, "heating_setpoint", "Heating Setpoint", 0.5, "°C", 10, 55, 0.5, "temperature", is_primary=True, bit_mask=0xFF),
    _num(0x00CB, "cooling_setpoint", "Cooling Setpoint", 0.5, "°C", 12, 30, 0.5, "temperature", is_primary=True, bit_mask=0xFF),
    _num(0x00CA, "hotwater_setpoint", "Hot Water Setpoint", 0.5, "°C", 10, 55, 0.5, "temperature", is_primary=True, bit_mask=0xFF),
    _num(0x00C6, "temp_diff_heating_cooling", "Heating/Cooling Temp Diff", 1, "°C", 2, 18, 1, "temperature"),
    _num(0x00C8, "temp_diff_hotwater", "Hot Water Temp Diff", 1, "°C", 2, 18, 1, "temperature"),
    # Economic Mode - Heating (E01-E04 signed, E13-E16)
    _num(0x0169, "econ_heat_ambi_1", "Economic Heat Ambient 1", 1, "°C", -30, 50, 1, "temperature", DataType.INT16),
    _num(0x016A, "econ_heat_ambi_2", "Economic Heat Ambient 2", 1, "°C", -30, 50, 1, "temperature", DataType.INT16),
    _num(0x016B, "econ_heat_ambi_3", "Economic Heat Ambient 3", 1, "°C", -30, 50, 1, "temperature", DataType.INT16),
    _num(0x016C, "econ_heat_ambi_4", "Economic Heat Ambient 4", 1, "°C", -30, 50, 1, "temperature", DataType.INT16),
    _num(0x0175, "econ_heat_temp_1", "Economic Heat Temp 1", 0.5, "°C", 10, 55, 0.5, "temperature"),
    _num(0x0176, "econ_heat_temp_2", "Economic Heat Temp 2", 0.5, "°C", 10, 55, 0.5, "temperature"),
    _num(0x0177, "econ_heat_temp_3", "Economic Heat Temp 3", 0.5, "°C", 10, 55, 0.5, "temperature"),
    _num(0x0178, "econ_heat_temp_4", "Economic Heat Temp 4", 0.5, "°C", 10, 55, 0.5, "temperature"),
    # Economic Mode - Hot Water (E05-E08 signed, E17-E20)
    _num(0x016D, "econ_water_ambi_1", "Economic Water Ambient 1", 1, "°C", -30, 50, 1, "temperature", DataType.INT16),
    _num(0x016E, "econ_water_ambi_2", "Economic Water Ambient 2", 1, "°C", -30, 50, 1, "temperature", DataType.INT16),
    _num(0x016F, "econ_water_ambi_3", "Economic Water Ambient 3", 1, "°C", -30, 50, 1, "temperature", DataType.INT16),
    _num(0x0170, "econ_water_ambi_4", "Economic Water Ambient 4", 1, "°C", -30, 50, 1, "temperature", DataType.INT16),
    _num(0x0179, "econ_water_temp_1", "Economic Water Temp 1", 0.5, "°C", 10, 55, 0.5, "temperature"),
    _num(0x017A, "econ_water_temp_2", "Economic Water Temp 2", 0.5, "°C", 10, 55, 0.5, "temperature"),
    _num(0x017B, "econ_water_temp_3", "Economic Water Temp 3", 0.5, "°C", 10, 55, 0.5, "temperature"),
    _num(0x017C, "econ_water_temp_4", "Economic Water Temp 4", 0.5, "°C", 10, 55, 0.5, "temperature"),
    # Economic Mode - Cooling (E09-E12 signed, E21-E24)
    _num(0x0171, "econ_cool_ambi_1", "Economic Cool Ambient 1", 1, "°C", -30, 50, 1, "temperature", DataType.INT16),
    _num(0x0172, "econ_cool_ambi_2", "Economic Cool Ambient 2", 1, "°C", -30, 50, 1, "temperature", DataType.INT16),
    _num(0x0173, "econ_cool_ambi_3", "Economic Cool Ambient 3", 1, "°C", -30, 50, 1, "temperature", DataType.INT16),
    _num(0x0174, "econ_cool_ambi_4", "Economic Cool Ambient 4", 1, "°C", -30, 50, 1, "temperature", DataType.INT16),
    _num(0x017D, "econ_cool_temp_1", "Economic Cool Temp 1", 0.5, "°C", 12, 30, 0.5, "temperature"),
    _num(0x017E, "econ_cool_temp_2", "Economic Cool Temp 2", 0.5, "°C", 12, 30, 0.5, "temperature"),
    _num(0x017F, "econ_cool_temp_3", "Economic Cool Temp 3", 0.5, "°C", 12, 30, 0.5, "temperature"),
    _num(0x0180, "econ_cool_temp_4", "Economic Cool Temp 4", 0.5, "°C", 12, 30, 0.5, "temperature"),
    # General Configuration - G parameters
    _num(0x0181, "comp_delay_hotwater", "Hot Water Heater Delay", 1, "min", 1, 60, 1),
    _num(0x0182, "comp_delay_heating", "Heating Heater Delay", 1, "min", 1, 60, 1),
    _num(0x0183, "hotwater_heater_ext_temp", "Hot Water Heater Ambient Temp", 1, "°C", -30, 30, 1, "temperature", DataType.INT16),
    _num(0x0184, "heating_heater_ext_temp", "Heating Heater Ambient Temp", 1, "°C", -30, 30, 1, "temperature", DataType.INT16),
    _num(0x0185, "pump_cycle", "Pump Thermostatic Cycle", 1, "min", 1, 120, 1),
    _num(0x018D, "dc_pump_temp_diff", "DC Pump Temp Differential", 1, "°C", 5, 30, 1),
    _num(0x0191, "mode_control_enable", "Mode Control Enable", 1, None, 0, 1, 1),
    _num(0x0192, "ambient_switch_setpoint", "Ambient Temp Switch Setpoint", 1, "°C", -20, 30, 1, "temperature", DataType.INT16),
    _num(0x0193, "ambient_switch_diff", "Ambient Temp Switch Diff", 1, "°C", 1, 10, 1, "temperature"),
    # Antilegionella Configuration
    _num(0x019A, "antilegionella_temp", "Antilegionella Temperature", 1, "°C", 30, 70, 1, "temperature"),
    _num(0x019B, "antilegionella_weekday", "Antilegionella Weekday", 1, None, 0, 6, 1),
    _num(0x019C, "antilegionella_start_hour", "Antilegionella Start Hour", 1, "h", 0, 23, 1),
    _num(0x019D, "antilegionella_end_hour", "Antilegionella End Hour", 1, "h", 0, 23, 1),
)

# Opt-in writable promotions of confirmed CHICO expert parameters (excluded: unconfirmed Invalid gaps
# B21-B26/B29-B34, unconfirmed 0x0034 bits 2-4, and dangerous factory parameters_reset_flag bit 0x0033.6).
CHICO_EXPERT_NUMBERS: tuple[NumberSpec, ...] = tuple(
    spec.as_number_spec(is_expert=True)
    for spec in CHICO_EXPERT_SENSORS
    if spec.writable
    and not spec.options
    and spec.min_value is not None
    and spec.max_value is not None
)

CHICO_EXPERT_SELECTS: tuple[SelectSpec, ...] = tuple(
    spec.as_select_spec(is_config=True, is_expert=True)
    for spec in CHICO_EXPERT_SENSORS
    if spec.writable and spec.options
)

CHICO_EXPERT_SWITCHES: tuple[SwitchSpec, ...] = tuple(
    spec.as_switch_spec(is_config=True, is_expert=True)
    for spec in CHICO_EXPERT_BINARY_SENSORS
    if spec.writable and spec.key != "parameters_reset_flag"
)
