"""CHICO controller register map and declarative entity specifications."""
from __future__ import annotations

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

CHICO_RW_BATCHES: tuple[ModbusBatchSpec, ...] = (
    ModbusBatchSpec(
        space=RegisterSpace.HOLDING_REGISTER,
        start_address=0x0032,
        count=5,
        description="Control Marks + Unit Mode (0x0032-0x0036)",
    ),
    ModbusBatchSpec(
        space=RegisterSpace.HOLDING_REGISTER,
        start_address=0x00C6,
        count=7,
        description="P Parameters Setpoints (0x00C6-0x00CC)",
    ),
    ModbusBatchSpec(
        space=RegisterSpace.HOLDING_REGISTER,
        start_address=0x0169,
        count=29,
        description="Economic Curves E01-E24 + General Settings (0x0169-0x0185)",
    ),
    ModbusBatchSpec(
        space=RegisterSpace.HOLDING_REGISTER,
        start_address=0x018D,
        count=7,
        description="G04 DC Pump + P07 Fan + Mode Control (0x018D-0x0193)",
    ),
    ModbusBatchSpec(
        space=RegisterSpace.HOLDING_REGISTER,
        start_address=0x019A,
        count=5,
        description="Antilegionella + G02 Pump Mode (0x019A-0x019E)",
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


CHICO_SENSORS: tuple[SensorSpec, ...] = (
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
    _ro_sensor(0x0029, "cond_temp", "Condensation Temperature", 0.1, "°C", "temperature"),
    # System Measurements
    _ro_sensor(0x0017, "ac_voltage", "AC Voltage", 1, "V", "voltage"),
    _ro_sensor(0x0018, "pump_flow", "Pump Flow", 1, "m³/h"),
    _ro_sensor(0x0019, "heating_cooling_capacity", "Heating/Cooling Capacity", 1, "W", "power"),
    _ro_sensor(0x001A, "ac_current", "AC Current", 1, "A", "current", DataType.INT16, clamp_min=0),
    _ro_sensor(0x001C, "eev1_step", "EEV1 Step", 1, "steps"),
    _ro_sensor(0x001D, "eev2_step", "EEV2 Step", 1, "steps"),
    _ro_sensor(0x001E, "compressor_frequency", "Compressor Frequency", 1, "Hz", "frequency"),
    _ro_sensor(0x0021, "dc_bus_voltage", "DC Bus Voltage", 1, "V", "voltage"),
    _ro_sensor(0x0023, "compressor_current", "Compressor Current", 1, "A", "current", DataType.INT16, clamp_min=0),
    _ro_sensor(0x0024, "target_frequency", "Target Frequency", 1, "Hz", "frequency"),
    _ro_sensor(0x0026, "dc_fan1_speed", "DC Fan 1 Speed", 1, "rpm"),
    _ro_sensor(0x0027, "dc_fan2_speed", "DC Fan 2 Speed", 1, "rpm"),
    _ro_sensor(0x002E, "dc_pump_speed", "DC Pump Speed", 1, "rpm"),
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


CHICO_BINARY_SENSORS: tuple[BinarySensorSpec, ...] = (
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
    )


CHICO_NUMBERS: tuple[NumberSpec, ...] = (
    # Basic Configuration - P parameters
    _num(0x00CC, "heating_setpoint", "Heating Setpoint", 0.5, "°C", 10, 55, 0.5, "temperature", is_primary=True),
    _num(0x00CB, "cooling_setpoint", "Cooling Setpoint", 0.5, "°C", 12, 30, 0.5, "temperature", is_primary=True),
    _num(0x00CA, "hotwater_setpoint", "Hot Water Setpoint", 0.5, "°C", 10, 55, 0.5, "temperature", is_primary=True),
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
