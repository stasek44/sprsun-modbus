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
PLATFORMS = ["sensor", "binary_sensor", "number"]

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
    0x0011: ("ambient_temp", "Ambient Temperature", 0.5, "°C", "temperature"),
    0x0012: ("outlet_temp", "Outlet Water Temperature", 0.1, "°C", "temperature"),
    0x0015: ("suction_gas_temp", "Suction Gas Temperature", 0.5, "°C", "temperature"),
    0x0016: ("coil_temp", "Coil Temperature", 0.5, "°C", "temperature"),
    0x001B: ("exhaust_temp", "Exhaust Temperature", 1, "°C", "temperature"),
    0x0022: ("driving_temp", "Driving Temperature", 0.5, "°C", "temperature"),
    0x0028: ("evap_temp", "Evaporation Temperature", 0.1, "°C", "temperature"),
    0x0029: ("cond_temp", "Condensation Temperature", 0.1, "°C", "temperature"),
    
    # System Measurements
    0x0017: ("ac_voltage", "AC Voltage", 1, "W", "power"),
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
    0x002F: ("suction_pressure", "Suction Pressure", 0.1, "bar", "pressure"),
    0x0030: ("discharge_pressure", "Discharge Pressure", 0.1, "bar", "pressure"),
    0x0031: ("dc_fan_target", "DC Fan Target", 1, "rpm", None),
    
    # Inverter Status
    0x001F: ("freq_conversion_failure_1", "Frequency Conversion Failure 1", 1, None, None),
    0x0020: ("freq_conversion_failure_2", "Frequency Conversion Failure 2", 1, None, None),
    0x0025: ("smart_grid_status", "Smart Grid Status", 1, None, None),
    0x002A: ("freq_conversion_fault_high", "Freq. Conversion Fault High", 1, None, None),
    0x002B: ("freq_conversion_fault_low", "Freq. Conversion Fault Low", 1, None, None),
}

# Binary Sensors - extracted from working status mark bits (R 0x0003)
# These are READ-ONLY status indicators  
BINARY_SENSOR_BITS = {
    "hotwater_demand": (0x0003, 0, "Hot Water Demand"),
    "heating_demand": (0x0003, 1, "Heating Demand"),
    "cooling_demand": (0x0003, 5, "Cooling Demand"),
    "antilegionella_active": (0x0003, 4, "Antilegionella Active"),
    "defrost_active": (0x0003, 7, "Defrost Active"),
    "alarm_stop": (0x0003, 6, "Alarm Stop"),
}

# Note: Control switches (RW 0x0032-0x0034) require bitfield manipulation
# These can be added as advanced feature later

# Numbers - Read-Write registers (according to modbus_reference.md)
# Format: address: (key, name, scale, unit, min, max, step, device_class)
REGISTERS_NUMBER = {
    # Basic Configuration - P parameters
    0x0036: ("unit_mode", "Unit Mode", 1, None, 0, 4, 1, None),  # P06
    0x00CC: ("heating_setpoint", "Heating Setpoint", 0.5, "°C", 10, 55, 0.5, "temperature"),  # P01
    0x00CB: ("cooling_setpoint", "Cooling Setpoint", 0.5, "°C", 12, 30, 0.5, "temperature"),  # P02
    0x00CA: ("hotwater_setpoint", "Hot Water Setpoint", 0.5, "°C", 10, 55, 0.5, "temperature"),  # P04
    0x00C6: ("temp_diff_heating_cooling", "Heating/Cooling Temp Diff", 1, "°C", 2, 18, 1, None),  # P03
    0x00C8: ("temp_diff_hotwater", "Hot Water Temp Diff", 1, "°C", 2, 18, 1, None),  # P05
    0x0190: ("fan_mode", "Fan Mode", 1, None, 0, 3, 1, None),  # P07: 0=NOR, 1=ECO, 2=Night, 3=Test
    
    # Economic Mode - Heating (E01-E04, E13-E16)
    0x0169: ("econ_heat_ambi_1", "Economic Heat Ambient 1", 1, "°C", -30, 50, 1, "temperature"),  # E01
    0x016A: ("econ_heat_ambi_2", "Economic Heat Ambient 2", 1, "°C", -30, 50, 1, "temperature"),  # E02
    0x016B: ("econ_heat_ambi_3", "Economic Heat Ambient 3", 1, "°C", -30, 50, 1, "temperature"),  # E03
    0x016C: ("econ_heat_ambi_4", "Economic Heat Ambient 4", 1, "°C", -30, 50, 1, "temperature"),  # E04
    0x0175: ("econ_heat_temp_1", "Economic Heat Temp 1", 0.5, "°C", 10, 55, 0.5, "temperature"),  # E13
    0x0176: ("econ_heat_temp_2", "Economic Heat Temp 2", 0.5, "°C", 10, 55, 0.5, "temperature"),  # E14
    0x0177: ("econ_heat_temp_3", "Economic Heat Temp 3", 0.5, "°C", 10, 55, 0.5, "temperature"),  # E15
    0x0178: ("econ_heat_temp_4", "Economic Heat Temp 4", 0.5, "°C", 10, 55, 0.5, "temperature"),  # E16
    
    # Economic Mode - Hot Water (E05-E08, E17-E20)
    0x016D: ("econ_water_ambi_1", "Economic Water Ambient 1", 1, "°C", -30, 50, 1, "temperature"),  # E05
    0x016E: ("econ_water_ambi_2", "Economic Water Ambient 2", 1, "°C", -30, 50, 1, "temperature"),  # E06
    0x016F: ("econ_water_ambi_3", "Economic Water Ambient 3", 1, "°C", -30, 50, 1, "temperature"),  # E07
    0x0170: ("econ_water_ambi_4", "Economic Water Ambient 4", 1, "°C", -30, 50, 1, "temperature"),  # E08
    0x0179: ("econ_water_temp_1", "Economic Water Temp 1", 0.5, "°C", 10, 55, 0.5, "temperature"),  # E17
    0x017A: ("econ_water_temp_2", "Economic Water Temp 2", 0.5, "°C", 10, 55, 0.5, "temperature"),  # E18
    0x017B: ("econ_water_temp_3", "Economic Water Temp 3", 0.5, "°C", 10, 55, 0.5, "temperature"),  # E19
    0x017C: ("econ_water_temp_4", "Economic Water Temp 4", 0.5, "°C", 10, 55, 0.5, "temperature"),  # E20
    
    # Economic Mode - Cooling (E09-E12, E21-E24)
    0x0171: ("econ_cool_ambi_1", "Economic Cool Ambient 1", 1, "°C", -30, 50, 1, "temperature"),  # E09
    0x0172: ("econ_cool_ambi_2", "Economic Cool Ambient 2", 1, "°C", -30, 50, 1, "temperature"),  # E10
    0x0173: ("econ_cool_ambi_3", "Economic Cool Ambient 3", 1, "°C", -30, 50, 1, "temperature"),  # E11
    0x0174: ("econ_cool_ambi_4", "Economic Cool Ambient 4", 1, "°C", -30, 50, 1, "temperature"),  # E12
    0x017D: ("econ_cool_temp_1", "Economic Cool Temp 1", 0.5, "°C", 12, 30, 0.5, "temperature"),  # E21
    0x017E: ("econ_cool_temp_2", "Economic Cool Temp 2", 0.5, "°C", 12, 30, 0.5, "temperature"),  # E22
    0x017F: ("econ_cool_temp_3", "Economic Cool Temp 3", 0.5, "°C", 12, 30, 0.5, "temperature"),  # E23
    0x0180: ("econ_cool_temp_4", "Economic Cool Temp 4", 0.5, "°C", 12, 30, 0.5, "temperature"),  # E24
    
    # General Configuration - G parameters
    0x0181: ("comp_delay_hotwater", "Hot Water Heater Delay", 1, "min", 1, 60, 1, None),  # G08
    0x0182: ("comp_delay_heating", "Heating Heater Delay", 1, "min", 1, 60, 1, None),  # G06
    0x0183: ("hotwater_heater_ext_temp", "Hot Water Heater Ambient Temp", 1, "°C", -30, 30, 1, "temperature"),  # G07
    0x0184: ("heating_heater_ext_temp", "Heating Heater Ambient Temp", 1, "°C", -30, 30, 1, "temperature"),  # G05
    0x0185: ("pump_cycle", "Pump Thermostatic Cycle", 1, "min", 1, 120, 1, None),  # G03
    0x018D: ("dc_pump_temp_diff", "DC Pump Temp Differential", 1, "°C", 5, 30, 1, None),  # G04
    0x0191: ("mode_control_enable", "Mode Control Enable", 1, None, 0, 1, 1, None),  # G09
    0x0192: ("ambient_switch_setpoint", "Ambient Temp Switch Setpoint", 1, "°C", -20, 30, 1, "temperature"),  # G10
    0x0193: ("ambient_switch_diff", "Ambient Temp Switch Diff", 1, "°C", 1, 10, 1, None),  # G11
    0x019E: ("pump_work_mode", "Pump Work Mode", 1, None, 0, 2, 1, None),  # G02: 0=Interval, 1=Normal, 2=Demand
    
    # Antilegionella Configuration
    0x019A: ("antilegionella_temp", "Antilegionella Temperature", 1, "°C", 30, 70, 1, "temperature"),
    0x019B: ("antilegionella_weekday", "Antilegionella Weekday", 1, None, 0, 6, 1, None),  # 0=Sun, 6=Sat
    0x019C: ("antilegionella_start_hour", "Antilegionella Start Hour", 1, "h", 0, 23, 1, None),
    0x019D: ("antilegionella_end_hour", "Antilegionella End Hour", 1, "h", 0, 23, 1, None),
}

# Unit mode descriptions
UNIT_MODE_MAP = {
    0: "Hot Water Only",
    1: "Heating Only",
    2: "Cooling Only",
    3: "Heating + Hot Water",
    4: "Cooling + Hot Water",
}

# Fan mode descriptions
FAN_MODE_MAP = {
    0: "Auto",
    1: "Low",
    2: "High",
}

# Pump mode descriptions
PUMP_MODE_MAP = {
    0: "Auto",
    1: "Continuous",
    2: "Intermittent",
}
