"""Constants for the SPRSUN Heat Pump Modbus integration."""

DOMAIN = "sprsun_modbus"

# Default values
DEFAULT_NAME = "SPRSUN Heat Pump"
DEFAULT_PORT = 502
DEFAULT_DEVICE_ADDRESS = 1
DEFAULT_SCAN_INTERVAL = 10  # seconds - balance between responsiveness and load
DEFAULT_TIMEOUT = 30  # seconds - Elfin W11 timeout (must be >= scan_interval + cycle_time)

# Configuration keys
CONF_DEVICE_ADDRESS = "device_address"
CONF_SCAN_INTERVAL = "scan_interval"

# Platforms
PLATFORMS = ["sensor", "binary_sensor", "number", "select", "switch", "button"]

# Read-Only Registers (50 parameters) - zgodnie z modbus_reference.md
REGISTERS_READ_ONLY = {
    # System Status
    0x0000: ("compressor_runtime", "Compressor Runtime", 1, "h", None),
    0x0001: ("cop", "COP", 1, None, None),
    0x0013: ("software_version_year", "Software Version (Year)", 1, None, None),
    0x0014: ("software_version_month_day", "Software Version (Month/Day)", 1, None, None),
    0x002C: ("controller_version", "Controller Version", 1, None, None),
    0x002D: ("display_version", "Display Version", 1, None, None),
    
    # Input/Output/Status Flags
    0x0002: ("switching_input_symbol", "Switching Input Symbol", 1, None, None),
    0x0003: ("working_status_mark", "Working Status Mark", 1, None, None),
    0x0004: ("output_symbol_1", "Output Symbol 1", 1, None, None),
    0x0005: ("output_symbol_2", "Output Symbol 2", 1, None, None),
    0x0006: ("output_symbol_3", "Output Symbol 3", 1, None, None),
    
    # Failure/Alarm Flags
    0x0007: ("failure_symbol_1", "Failure Symbol 1", 1, None, None),
    0x0008: ("failure_symbol_2", "Failure Symbol 2", 1, None, None),
    0x0009: ("failure_symbol_3", "Failure Symbol 3", 1, None, None),
    0x000A: ("failure_symbol_4", "Failure Symbol 4", 1, None, None),
    0x000B: ("failure_symbol_5", "Failure Symbol 5", 1, None, None),
    0x000C: ("failure_symbol_6", "Failure Symbol 6", 1, None, None),
    0x000D: ("failure_symbol_7", "Failure Symbol 7", 1, None, None),
    
    # Temperature Sensors
    0x000E: ("inlet_temp", "Inlet Water Temperature", 0.1, "°C", "temperature"),
    0x000F: ("hotwater_temp", "Hot Water Temperature", 0.1, "°C", "temperature"),
    0x0011: ("ambient_temp", "Ambient Temperature", 0.5, "°C", "temperature"),  # SIGNED
    0x0012: ("outlet_temp", "Outlet Water Temperature", 0.1, "°C", "temperature"),
    0x0015: ("suction_gas_temp", "Suction Gas Temperature", 0.5, "°C", "temperature"),  # SIGNED
    0x0016: ("coil_temp", "Coil Temperature", 0.5, "°C", "temperature"),  # SIGNED
    0x001B: ("exhaust_temp", "Exhaust Temperature", 1, "°C", "temperature"),
    0x0022: ("driving_temp", "Driving Temperature", 0.5, "°C", "temperature"),  # SIGNED
    0x0028: ("evap_temp", "Evaporation Temperature", 0.1, "°C", "temperature"),  # SIGNED
    0x0029: ("cond_temp", "Condensation Temperature", 0.1, "°C", "temperature"),
    
    # System Measurements
    0x0017: ("ac_voltage", "AC Voltage", 1, "V", "voltage"),
    0x0018: ("pump_flow", "Pump Flow", 1, "m³/h", None),
    0x0019: ("heating_cooling_capacity", "Heating/Cooling Capacity", 1, "W", "power"),
    0x001A: ("ac_current", "AC Current", 1, "A", "current"),
    0x001C: ("eev1_step", "EEV1 Step", 1, "steps", None),
    0x001D: ("eev2_step", "EEV2 Step", 1, "steps", None),
    0x001E: ("compressor_frequency", "Compressor Frequency", 1, "Hz", "frequency"),
    0x0021: ("dc_bus_voltage", "DC Bus Voltage", 1, "V", "voltage"),
    0x0023: ("compressor_current", "Compressor Current", 1, "A", "current"),
    0x0024: ("target_frequency", "Target Frequency", 1, "Hz", "frequency"),
    0x0026: ("dc_fan1_speed", "DC Fan 1 Speed", 1, "rpm", None),
    0x0027: ("dc_fan2_speed", "DC Fan 2 Speed", 1, "rpm", None),
    0x002E: ("dc_pump_speed", "DC Pump Speed", 1, "rpm", None),
    # Pressure sensors: Values in 0.1 PSI, converted to bar (0.1 PSI ÷ 14.5 = 0.0069)
    # REGISTERS ARE SWAPPED IN MANUFACTURER'S DOCUMENTATION!
    # 0x002F labeled "suction" actually shows discharge values (~31 bar)
    # 0x0030 labeled "discharge" actually shows suction values (~5 bar)
    0x002F: ("discharge_pressure", "Discharge Pressure", 0.0069, "bar", "pressure"),  # SWAPPED!
    0x0030: ("suction_pressure", "Suction Pressure", 0.0069, "bar", "pressure"),      # SWAPPED!
    0x0031: ("dc_fan_target", "DC Fan Target", 1, "rpm", None),
    
    # Inverter Status
    0x001F: ("freq_conversion_failure_1", "Frequency Conversion Failure 1", 1, None, None),
    0x0020: ("freq_conversion_failure_2", "Frequency Conversion Failure 2", 1, None, None),
    0x0025: ("smart_grid_status", "Smart Grid Status", 1, None, None),
    0x002A: ("freq_conversion_fault_high", "Freq. Conversion Fault High", 1, None, None),
    0x002B: ("freq_conversion_fault_low", "Freq. Conversion Fault Low", 1, None, None),
}

# Binary Sensors - extracted from bitfield registers
# These are READ-ONLY status indicators

# Working Status Mark (R 0x0003) - operational status
BINARY_SENSOR_BITS = {
    # Working Status Mark (0x0003)
    "hotwater_demand": (0x0003, 0, "Hot Water Demand"),
    "heating_demand": (0x0003, 1, "Heating Demand"),
    "cooling_demand": (0x0003, 5, "Cooling Demand"),
    "antilegionella_active": (0x0003, 4, "Antilegionella Active"),
    "defrost_active": (0x0003, 7, "Defrost Active"),
    "alarm_stop": (0x0003, 6, "Alarm Stop"),
    
    # Switching Input Symbol (0x0002) - physical input switches
    "ac_linkage_switch": (0x0002, 0, "A/C Linkage Switch"),
    "linkage_switch": (0x0002, 1, "Linkage Switch"),
    "heating_linkage": (0x0002, 2, "Heating Linkage"),
    "cooling_linkage": (0x0002, 3, "Cooling Linkage"),
    "flow_switch": (0x0002, 4, "Flow Switch"),
    "high_pressure_switch": (0x0002, 5, "High Pressure Switch"),
    "phase_sequence_ok": (0x0002, 6, "Phase Sequence OK"),
    
    # Output Symbol 1 (0x0004) - main outputs
    "compressor_running": (0x0004, 0, "Compressor"),
    "fan_running": (0x0004, 5, "Fan"),
    "valve_4way": (0x0004, 6, "4-Way Valve"),
    "fan_high_speed": (0x0004, 7, "Fan High Speed"),
    
    # Output Symbol 2 (0x0005) - auxiliary outputs
    "chassis_heater": (0x0005, 0, "Chassis Heater"),
    "heating_heater": (0x0005, 5, "Heating Heater"),
    "valve_3way": (0x0005, 6, "3-Way Valve"),
    "hotwater_heater": (0x0005, 7, "Hot Water Heater"),
    
    # Output Symbol 3 (0x0006) - pump outputs
    "ac_pump": (0x0006, 0, "A/C Pump"),
    "crank_heater": (0x0006, 1, "Crank Heater"),
    "assistant_solenoid": (0x0006, 5, "Assistant Solenoid Valve"),
    "pump_running": (0x0006, 6, "Circulation Pump"),
    
    # Failure Symbol 1 (0x0007) - sensor failures
    "error_hotwater_sensor": (0x0007, 0, "Hot Water Temp Sensor Error"),
    "error_ambient_sensor": (0x0007, 1, "Ambient Temp Sensor Error"),
    "error_coil_sensor": (0x0007, 2, "Coil Temp Sensor Error"),
    "error_outlet_sensor": (0x0007, 4, "Outlet Temp Sensor Error"),
    "error_high_pressure_sensor": (0x0007, 5, "High Pressure Sensor Error"),
    "error_phase_sequence": (0x0007, 7, "Phase Sequence Error"),
    
    # Failure Symbol 2 (0x0008) - protection errors
    "error_water_flow": (0x0008, 0, "Water Flow Error"),
    "error_high_temp_heating": (0x0008, 2, "High Temp Protection (Heating Outlet)"),
    
    # Failure Symbol 3 (0x0009)
    "error_outlet_gas_temp": (0x0009, 6, "Outlet Gas Temp Error"),
    
    # Failure Symbol 4 (0x000A)
    "error_inlet_sensor": (0x000A, 0, "Water Inlet Temp Sensor Error"),
    "error_exhaust_high": (0x000A, 1, "Exhaust Temperature Too High"),
    "error_low_temp_cooling": (0x000A, 5, "Low Temp Protection (Cooling Outlet)"),
    "error_inlet_gas_sensor": (0x000A, 6, "Inlet Gas Temp Sensor Error"),
    
    # Failure Symbol 5 (0x000B) - pressure errors
    "error_low_pressure": (0x000B, 0, "Low Pressure Protection"),
    "error_high_pressure": (0x000B, 1, "High Pressure Protection"),
    "error_coil_temp_high": (0x000B, 2, "Coil Temperature Too High"),
    "error_high_pressure_sensor2": (0x000B, 6, "High Pressure Sensor Failure"),
    "error_low_pressure_sensor": (0x000B, 7, "Low Pressure Sensor Failure"),
    
    # Failure Symbol 6 (0x000C) - antifreeze
    "error_antifreeze_secondary": (0x000C, 4, "Secondary Antifreeze Protection"),
    "error_antifreeze_primary": (0x000C, 5, "Primary Antifreeze Protection"),
    
    # Failure Symbol 7 (0x000D) - system errors
    "error_ambient_temp_low": (0x000D, 1, "Ambient Temperature Too Low"),
    "error_inverter_module": (0x000D, 4, "Frequency Conversion Module Fault"),
    "error_dc_fan2": (0x000D, 5, "DC Fan 2 Failure"),
    "error_dc_fan1": (0x000D, 6, "DC Fan 1 Failure"),
}

# Switch entities - Read-Write bitfield controls (persistent state)
# Format: key: (address, bit, name, coil_address_if_available)
REGISTERS_SWITCH = {
    "power_switch": (0x0032, 0, "Power", 0x0320),  # Parameter marker bit 0: ON/OFF (coil 0x0320)
    "antilegionella_enable": (0x0034, 0, "Antilegionella Enable", None),  # Control mark 2 bit 0
    "two_three_function": (0x0034, 1, "Two/Three Function", None),  # Control mark 2 bit 1 (0=Two, 1=Three)
}

# Button entities - Read-Write bitfield momentary actions
# Format: key: (address, bit, name, description)
REGISTERS_BUTTON = {
    "failure_reset": (0x0033, 7, "Failure Reset", "Reset all failures after fixing the cause"),  # Control mark 1 bit 7
}

# Select entities - Read-Write mode controls
# Format: address: (key, name, options_dict)
REGISTERS_SELECT = {
    0x0036: ("unit_mode", "Unit Mode", {  # P06
        0: "Hot Water Only",
        1: "Heating Only",
        2: "Cooling Only",
        3: "Heating + Hot Water",
        4: "Cooling + Hot Water",
    }),
    0x0190: ("fan_mode", "Fan Mode", {  # P07
        0: "Normal",
        1: "Economic",
        2: "Night",
        3: "Test",
    }),
    0x019E: ("pump_mode", "Pump Work Mode", {  # G02
        0: "Interval",
        1: "Normal",
        2: "Demand",
    }),
}

# Numbers - Read-Write registers (according to modbus_reference.md)
# Format: address: (key, name, scale, unit, min, max, step, device_class)
REGISTERS_NUMBER = {
    # Basic Configuration - P parameters
    0x00CC: ("heating_setpoint", "Heating Setpoint", 0.5, "°C", 10, 55, 0.5, "temperature"),  # P01
    0x00CB: ("cooling_setpoint", "Cooling Setpoint", 0.5, "°C", 12, 30, 0.5, "temperature"),  # P02
    0x00CA: ("hotwater_setpoint", "Hot Water Setpoint", 0.5, "°C", 10, 55, 0.5, "temperature"),  # P04
    0x00C6: ("temp_diff_heating_cooling", "Heating/Cooling Temp Diff", 1, "°C", 2, 18, 1, "temperature"),  # P03
    0x00C8: ("temp_diff_hotwater", "Hot Water Temp Diff", 1, "°C", 2, 18, 1, "temperature"),  # P05
    
    # Economic Mode - Heating (E01-E04, E13-E16)
    # NOTE: E01-E04 are SIGNED (can be negative for winter ambient temps)
    0x0169: ("econ_heat_ambi_1", "Economic Heat Ambient 1", 1, "°C", -30, 50, 1, "temperature"),  # E01 SIGNED
    0x016A: ("econ_heat_ambi_2", "Economic Heat Ambient 2", 1, "°C", -30, 50, 1, "temperature"),  # E02 SIGNED
    0x016B: ("econ_heat_ambi_3", "Economic Heat Ambient 3", 1, "°C", -30, 50, 1, "temperature"),  # E03 SIGNED
    0x016C: ("econ_heat_ambi_4", "Economic Heat Ambient 4", 1, "°C", -30, 50, 1, "temperature"),  # E04 SIGNED
    0x0175: ("econ_heat_temp_1", "Economic Heat Temp 1", 0.5, "°C", 10, 55, 0.5, "temperature"),  # E13
    0x0176: ("econ_heat_temp_2", "Economic Heat Temp 2", 0.5, "°C", 10, 55, 0.5, "temperature"),  # E14
    0x0177: ("econ_heat_temp_3", "Economic Heat Temp 3", 0.5, "°C", 10, 55, 0.5, "temperature"),  # E15
    0x0178: ("econ_heat_temp_4", "Economic Heat Temp 4", 0.5, "°C", 10, 55, 0.5, "temperature"),  # E16
    
    # Economic Mode - Hot Water (E05-E08, E17-E20)
    # NOTE: E05-E08 are SIGNED (can be negative for winter ambient temps)
    0x016D: ("econ_water_ambi_1", "Economic Water Ambient 1", 1, "°C", -30, 50, 1, "temperature"),  # E05 SIGNED
    0x016E: ("econ_water_ambi_2", "Economic Water Ambient 2", 1, "°C", -30, 50, 1, "temperature"),  # E06 SIGNED
    0x016F: ("econ_water_ambi_3", "Economic Water Ambient 3", 1, "°C", -30, 50, 1, "temperature"),  # E07 SIGNED
    0x0170: ("econ_water_ambi_4", "Economic Water Ambient 4", 1, "°C", -30, 50, 1, "temperature"),  # E08 SIGNED
    0x0179: ("econ_water_temp_1", "Economic Water Temp 1", 0.5, "°C", 10, 55, 0.5, "temperature"),  # E17
    0x017A: ("econ_water_temp_2", "Economic Water Temp 2", 0.5, "°C", 10, 55, 0.5, "temperature"),  # E18
    0x017B: ("econ_water_temp_3", "Economic Water Temp 3", 0.5, "°C", 10, 55, 0.5, "temperature"),  # E19
    0x017C: ("econ_water_temp_4", "Economic Water Temp 4", 0.5, "°C", 10, 55, 0.5, "temperature"),  # E20
    
    # Economic Mode - Cooling (E09-E12, E21-E24)
    # NOTE: E09-E12 are SIGNED (can be negative for winter ambient temps)
    0x0171: ("econ_cool_ambi_1", "Economic Cool Ambient 1", 1, "°C", -30, 50, 1, "temperature"),  # E09 SIGNED
    0x0172: ("econ_cool_ambi_2", "Economic Cool Ambient 2", 1, "°C", -30, 50, 1, "temperature"),  # E10 SIGNED
    0x0173: ("econ_cool_ambi_3", "Economic Cool Ambient 3", 1, "°C", -30, 50, 1, "temperature"),  # E11 SIGNED
    0x0174: ("econ_cool_ambi_4", "Economic Cool Ambient 4", 1, "°C", -30, 50, 1, "temperature"),  # E12 SIGNED
    0x017D: ("econ_cool_temp_1", "Economic Cool Temp 1", 0.5, "°C", 12, 30, 0.5, "temperature"),  # E21
    0x017E: ("econ_cool_temp_2", "Economic Cool Temp 2", 0.5, "°C", 12, 30, 0.5, "temperature"),  # E22
    0x017F: ("econ_cool_temp_3", "Economic Cool Temp 3", 0.5, "°C", 12, 30, 0.5, "temperature"),  # E23
    0x0180: ("econ_cool_temp_4", "Economic Cool Temp 4", 0.5, "°C", 12, 30, 0.5, "temperature"),  # E24
    
    # General Configuration - G parameters
    0x0181: ("comp_delay_hotwater", "Hot Water Heater Delay", 1, "min", 1, 60, 1, None),  # G08
    0x0182: ("comp_delay_heating", "Heating Heater Delay", 1, "min", 1, 60, 1, None),  # G06
    0x0183: ("hotwater_heater_ext_temp", "Hot Water Heater Ambient Temp", 1, "°C", -30, 30, 1, "temperature"),  # G07 SIGNED
    0x0184: ("heating_heater_ext_temp", "Heating Heater Ambient Temp", 1, "°C", -30, 30, 1, "temperature"),  # G05 SIGNED
    0x0185: ("pump_cycle", "Pump Thermostatic Cycle", 1, "min", 1, 120, 1, None),  # G03
    0x018D: ("dc_pump_temp_diff", "DC Pump Temp Differential", 1, "°C", 5, 30, 1, None),  # G04
    0x0191: ("mode_control_enable", "Mode Control Enable", 1, None, 0, 1, 1, None),  # G09
    0x0192: ("ambient_switch_setpoint", "Ambient Temp Switch Setpoint", 1, "°C", -20, 30, 1, "temperature"),  # G10 SIGNED
    0x0193: ("ambient_switch_diff", "Ambient Temp Switch Diff", 1, "°C", 1, 10, 1, "temperature"),  # G11
    
    # Antilegionella Configuration
    0x019A: ("antilegionella_temp", "Antilegionella Temperature", 1, "°C", 30, 70, 1, "temperature"),
    0x019B: ("antilegionella_weekday", "Antilegionella Weekday", 1, None, 0, 6, 1, None),  # 0=Sun, 6=Sat
    0x019C: ("antilegionella_start_hour", "Antilegionella Start Hour", 1, "h", 0, 23, 1, None),
    0x019D: ("antilegionella_end_hour", "Antilegionella End Hour", 1, "h", 0, 23, 1, None),
}

# Weekday mapping for antilegionella
WEEKDAY_MAP = {
    0: "Sunday",
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
}
