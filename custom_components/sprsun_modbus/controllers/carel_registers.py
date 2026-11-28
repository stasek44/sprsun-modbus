"""Declarative Modbus register, discrete input, coil, and alarm map for CAREL controllers.

Verified against SPRSUN CAREL OEM documentation:
- ``Modbus for DC inverter heat pump v3.xlsx`` (CGK0x0V2)
- ``220224 ModBus Adresy Carel CGK.docx`` (CGK025-060V3L)
- Live hardware logs & community drivers (wmertens/sprsun-carel-modbus, Sateetje/SPRSUN-Modbus)

Safety locks (NEVER exposed as writable):
- Coil 57 (00058): Factory parameter reset (Reset parametrów)
- Holding 332 (40333): Insert BLDC default
"""
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

# ---------------------------------------------------------------------------
# Enum / Option mappings
# ---------------------------------------------------------------------------

CAREL_UNIT_MODE_OPTIONS: dict[int, str] = {
    0: "Cooling",
    1: "Heating",
    2: "Hot Water",
    3: "Cooling + Hot Water",
    4: "Heating + Hot Water",
}

CAREL_RUN_MODE_OPTIONS: dict[int, str] = {
    0: "Cooling",
    1: "Heating",
    2: "Hot Water",
}

CAREL_STATUS_OPTIONS: dict[int, str] = {
    0: "Unit not Ready",
    1: "Unit ON",
    2: "OFF by Alarm",
    3: "OFF by Timezone",
    4: "OFF by SuperV",
    5: "OFF by Linkage",
    6: "OFF by Keyboard",
    7: "Manual Mode",
    8: "Anti Freeze",
    9: "OFF by AC Linkage",
    10: "OFF by Change",
}

CAREL_PUMP_MODE_OPTIONS: dict[int, str] = {
    0: "Normal",
    1: "Demand",
    2: "Interval",
}

CAREL_FAN_MODE_OPTIONS: dict[int, str] = {
    0: "Daytime",
    1: "Night",
    2: "Eco",
    3: "Pressure",
}

CAREL_BLDC_STATUS_OPTIONS: dict[int, str] = {
    0: "OK",
    1: "Controlled",
    2: "Limited",
}

CAREL_EEV_PROT_OPTIONS: dict[int, str] = {
    0: "None",
    1: "None (Idle)",
    2: "Low Superheat",
    3: "LOP",
    4: "MOP",
    5: "High Condensing Temp",
}

CAREL_HEATER_TYPE_OPTIONS: dict[int, str] = {
    0: "Disabled",
    1: "Hot Water",
    2: "Heating",
    3: "All",
    4: "Independent",
}

# ---------------------------------------------------------------------------
# Discrete Input alarm map (0-based DI addresses 13..177 -> AL001..AL174)
# ---------------------------------------------------------------------------

CAREL_ALARM_START_DI = 13
CAREL_ALARM_COUNT = 165  # DI 13..177 inclusive

CAREL_ALARM_MAP: dict[int, tuple[str, str]] = {
    13: ("AL001", "Too many memory writings"),
    14: ("AL002", "Retain memory write error"),
    15: ("AL003", "Inlet probe error"),
    16: ("AL004", "Outlet probe error"),
    17: ("AL005", "Ambient probe error"),
    18: ("AL006", "Condenser coil temp probe error"),
    19: ("AL007", "Water flow switch"),
    20: ("AL008", "Phase sequence protection alarm"),
    21: ("AL009", "Unit work hour warning"),
    22: ("AL010", "Pump work hour warning"),
    23: ("AL011", "Compressor work hour warning"),
    24: ("AL012", "Condenser fan work hour warning"),
    25: ("AL013", "Low superheat - Valve A"),
    26: ("AL014", "Low superheat - Valve B"),
    27: ("AL015", "LOP - Valve A"),
    28: ("AL016", "LOP - Valve B"),
    29: ("AL017", "MOP - Valve A"),
    30: ("AL018", "MOP - Valve B"),
    31: ("AL019", "Motor error - Valve A"),
    32: ("AL020", "Motor error - Valve B"),
    33: ("AL021", "Low suction temp - Valve A"),
    34: ("AL022", "Low suction temp - Valve B"),
    35: ("AL023", "High condensing temp EVD"),
    36: ("AL024", "Probe S1 error EVD"),
    37: ("AL025", "Probe S2 error EVD"),
    38: ("AL026", "Probe S3 error EVD"),
    39: ("AL027", "Probe S4 error EVD"),
    40: ("AL028", "Battery discharge EVD"),
    41: ("AL029", "EEPROM alarm EVD"),
    42: ("AL030", "Incomplete closing EVD"),
    43: ("AL031", "Emergency closing EVD"),
    44: ("AL032", "FW not compatible EVD"),
    45: ("AL033", "Config error EVD"),
    46: ("AL034", "EVD Driver offline"),
    47: ("AL035", "BLDC: High startup DeltaP"),
    48: ("AL036", "BLDC: Compressor shut off"),
    49: ("AL037", "BLDC: Out of envelope"),
    50: ("AL038", "BLDC: Starting fail wait"),
    51: ("AL039", "BLDC: Starting fail exceeded"),
    52: ("AL040", "BLDC: Low delta pressure"),
    53: ("AL041", "BLDC: High discharge gas temp"),
    54: ("AL042", "Envelope: High compressor ratio"),
    55: ("AL043", "Envelope: High discharge pressure"),
    56: ("AL044", "Envelope: High current"),
    57: ("AL045", "Envelope: High suction pressure"),
    58: ("AL046", "Envelope: Low compressor ratio"),
    59: ("AL047", "Envelope: Low pressure diff"),
    60: ("AL048", "Envelope: Low discharge pressure"),
    61: ("AL049", "Envelope: Low suction pressure"),
    62: ("AL050", "Envelope: High discharge temp"),
    63: ("AL051", "Power+: 01 Overcurrent"),
    64: ("AL052", "Power+: 02 Motor overload"),
    65: ("AL053", "Power+: 03 DCbus overvoltage"),
    66: ("AL054", "Power+: 04 DCbus undervoltage"),
    67: ("AL055", "Power+: 05 Drive overtemp"),
    68: ("AL056", "Power+: 06 Drive undertemp"),
    69: ("AL057", "Power+: 07 Overcurrent HW"),
    70: ("AL058", "Power+: 08 Motor overtemp"),
    71: ("AL059", "Power+: 09 IGBT module error"),
    72: ("AL060", "Power+: 10 CPU error"),
    73: ("AL061", "Power+: 11 Parameter default"),
    74: ("AL062", "Power+: 12 DCbus ripple"),
    75: ("AL063", "Power+: 13 Data comm fault"),
    76: ("AL064", "Power+: 14 Thermistor fault"),
    77: ("AL065", "Power+: 15 Autotuning fault"),
    78: ("AL066", "Power+: 16 Drive disabled"),
    79: ("AL067", "Power+: 17 Motor phase fault"),
    80: ("AL068", "Power+: 18 Internal fan fault"),
    81: ("AL069", "Power+: 19 Speed fault"),
    82: ("AL070", "Power+: 20 PFC module error"),
    83: ("AL071", "Power+: 21 PFC overvoltage"),
    84: ("AL072", "Power+: 22 PFC undervoltage"),
    85: ("AL073", "Power+: 23 STO detection error"),
    86: ("AL074", "Power+: 24 STO detection error"),
    87: ("AL075", "Power+: 25 Ground fault"),
    88: ("AL076", "Power+: 26 Internal error 1"),
    89: ("AL077", "Power+: 27 Internal error 2"),
    90: ("AL078", "Power+: 28 Drive overload"),
    91: ("AL079", "Power+: 29 uC safety fault"),
    92: ("AL080", "Power+: 98 Unexpected restart"),
    93: ("AL081", "Power+: 99 Unexpected stop"),
    94: ("AL082", "Power+ safety: 01 Current meas fault"),
    95: ("AL083", "Power+ safety: 02 Current unbalanced"),
    96: ("AL084", "Power+ safety: 03 Over current"),
    97: ("AL085", "Power+ safety: 04 STO alarm"),
    98: ("AL086", "Power+ safety: 05 STO hardware alarm"),
    99: ("AL087", "Power+ safety: 06 Power supply missing"),
    100: ("AL088", "Power+ safety: 07 HW fault cmd buffer"),
    101: ("AL089", "Power+ safety: 08 HW fault heater"),
    102: ("AL090", "Power+ safety: 09 Data comm fault"),
    103: ("AL091", "Power+ safety: 10 Compressor stall"),
    104: ("AL092", "Power+ safety: 11 DCbus overcurrent"),
    105: ("AL093", "Power+ safety: 12 HWF DCbus current"),
    106: ("AL094", "Power+ safety: 13 DCbus voltage"),
    107: ("AL095", "Power+ safety: 14 HWF DCbus voltage"),
    108: ("AL096", "Power+ safety: 15 Input voltage"),
    109: ("AL097", "Power+ safety: 16 HWF input voltage"),
    110: ("AL098", "Power+ safety: 17 DCbus power alarm"),
    111: ("AL099", "Power+ safety: 18 HWF power mismatch"),
    112: ("AL100", "Power+ safety: 19 NTC overtemp"),
    113: ("AL101", "Power+ safety: 20 NTC undertemp"),
    114: ("AL102", "Power+ safety: 21 NTC fault"),
    115: ("AL103", "Power+ safety: 22 HWF sync fault"),
    116: ("AL104", "Power+ safety: 23 Invalid parameter"),
    117: ("AL105", "Power+ safety: 24 FW fault"),
    118: ("AL106", "Power+ safety: 25 HW fault"),
    126: ("AL114", "Power+ offline"),
    127: ("AL115", "EEV: Low superheat"),
    128: ("AL116", "EEV: LOP"),
    129: ("AL117", "EEV: MOP"),
    130: ("AL118", "EEV: High condensing temp"),
    131: ("AL119", "EEV: Low suction temp"),
    132: ("AL120", "EEV: Motor error"),
    133: ("AL121", "EEV: Self tuning"),
    134: ("AL122", "EEV: Emergency closing"),
    135: ("AL123", "EEV: Temperature delta"),
    136: ("AL124", "EEV: Pressure delta"),
    137: ("AL125", "EEV: Param range error"),
    138: ("AL126", "EEV: Service position error"),
    139: ("AL127", "EEV: ValveID pin error"),
    140: ("AL128", "Low pressure alarm"),
    141: ("AL129", "High pressure alarm"),
    142: ("AL130", "Discharge temp probe error"),
    143: ("AL131", "Suction temp probe error"),
    144: ("AL132", "Discharge pressure probe error"),
    145: ("AL133", "Suction pressure probe error"),
    146: ("AL134", "Tank temp probe error"),
    147: ("AL135", "EVI suction temp probe error"),
    148: ("AL136", "EVI suction pressure probe error"),
    149: ("AL137", "Flow switch alarm"),
    150: ("AL138", "High temp alarm"),
    151: ("AL139", "Low temp alarm"),
    152: ("AL140", "Temp delta alarm"),
    153: ("AL141", "EVI: Param range error"),
    154: ("AL142", "EVI: Low superheat"),
    155: ("AL143", "EVI: LOP"),
    156: ("AL144", "EVI: MOP"),
    157: ("AL145", "EVI: High condensing temp"),
    158: ("AL146", "EVI: Low suction temp"),
    159: ("AL147", "EVI: Motor error"),
    160: ("AL148", "EVI: Self tuning"),
    161: ("AL149", "EVI: Emergency closing"),
    162: ("AL150", "EVI: Service position error"),
    163: ("AL151", "EVI: ValveID pin error"),
    164: ("AL152", "Supply power error"),
    165: ("AL153", "Fan 1 fault"),
    166: ("AL154", "Fan 2 fault"),
    167: ("AL155", "Fans offline"),
    168: ("AL165", "Slave 1 offline"),
    169: ("AL166", "Master offline"),
    170: ("AL167", "Slave 2 offline"),
    171: ("AL168", "Slave 3 offline"),
    172: ("AL169", "Slave 4 offline"),
    173: ("AL170", "Slave 5 offline"),
    174: ("AL171", "Slave 6 offline"),
    175: ("AL172", "Slave 7 offline"),
    176: ("AL173", "Slave 8 offline"),
    177: ("AL174", "Slave 9 offline"),
}

# ---------------------------------------------------------------------------
# Modbus polling batches (safe RS485/gateway chunk sizes)
# ---------------------------------------------------------------------------

CAREL_RO_BATCHES: tuple[ModbusBatchSpec, ...] = (
    ModbusBatchSpec(RegisterSpace.DISCRETE_INPUT, 0, 13, "CAREL DI status & outputs 0-12"),
    ModbusBatchSpec(RegisterSpace.HOLDING_REGISTER, 188, 30, "CAREL telemetry 188-217"),
)

CAREL_OPTIONAL_RO_BATCHES: tuple[ModbusBatchSpec, ...] = (
    ModbusBatchSpec(RegisterSpace.DISCRETE_INPUT, 178, 6, "CAREL DI component status 178-183"),
    ModbusBatchSpec(RegisterSpace.HOLDING_REGISTER, 333, 3, "CAREL BLDC power/voltage/current 333-335"),
    ModbusBatchSpec(RegisterSpace.COIL, 40, 1, "CAREL power coil 40"),
)

CAREL_ALARM_BATCH = ModbusBatchSpec(
    RegisterSpace.DISCRETE_INPUT,
    CAREL_ALARM_START_DI,
    CAREL_ALARM_COUNT,
    "CAREL alarms DI 13-177",
)

CAREL_RW_BATCHES: tuple[ModbusBatchSpec, ...] = (
    ModbusBatchSpec(RegisterSpace.HOLDING_REGISTER, 0, 16, "CAREL core RW setpoints & modes 0-15"),
    ModbusBatchSpec(RegisterSpace.COIL, 0, 43, "CAREL control coils 0-42"),
)

CAREL_OPTIONAL_RW_BATCHES: tuple[ModbusBatchSpec, ...] = (
    ModbusBatchSpec(RegisterSpace.HOLDING_REGISTER, 323, 7, "CAREL heater type & version 323-329"),
    ModbusBatchSpec(RegisterSpace.HOLDING_REGISTER, 263, 2, "CAREL night mode limits 263-264"),
    ModbusBatchSpec(RegisterSpace.HOLDING_REGISTER, 276, 21, "CAREL ECO curves 276-296"),
    ModbusBatchSpec(RegisterSpace.HOLDING_REGISTER, 336, 3, "CAREL ECO curve endpoints 336-338"),
    ModbusBatchSpec(RegisterSpace.HOLDING_REGISTER, 77, 15, "CAREL defrost parameters 77-91"),
)

# ---------------------------------------------------------------------------
# Core read-only sensors
# ---------------------------------------------------------------------------


def _ro_sensor(
    address: int,
    key: str,
    name: str,
    scale: float | int = 0.1,
    unit: str | None = None,
    device_class: str | None = None,
    data_type: DataType = DataType.INT16,
    *,
    diagnostic: bool = False,
    options: dict[int, str] | None = None,
    clamp_min: float | None = None,
) -> SensorSpec:
    return SensorSpec(
        key=key,
        name=name,
        address=address,
        space=RegisterSpace.HOLDING_REGISTER,
        data_type=data_type,
        scale=scale,
        unit=unit,
        device_class=device_class,
        diagnostic=diagnostic,
        options=options,
        clamp_min=clamp_min,
    )


CAREL_CORE_SENSORS: tuple[SensorSpec, ...] = (
    # Temperatures (Holding 188-196)
    _ro_sensor(188, "inlet_temp", "Inlet Water Temperature", 0.1, "°C", "temperature"),
    _ro_sensor(189, "outlet_temp", "Outlet Water Temperature", 0.1, "°C", "temperature"),
    _ro_sensor(190, "ambient_temp", "Ambient Temperature", 0.1, "°C", "temperature"),
    _ro_sensor(191, "discharge_temp", "Discharge Gas Temperature", 0.1, "°C", "temperature"),
    _ro_sensor(192, "suction_temp", "Suction Gas Temperature", 0.1, "°C", "temperature"),
    _ro_sensor(193, "discharge_pressure", "Discharge Pressure", 0.1, "bar", "pressure", clamp_min=0.0),
    _ro_sensor(194, "suction_pressure", "Suction Pressure", 0.1, "bar", "pressure", clamp_min=0.0),
    _ro_sensor(195, "hotwater_temp", "Hot Water Temperature", 0.1, "°C", "temperature"),
    _ro_sensor(196, "coil_temp", "Coil Temperature", 0.1, "°C", "temperature"),
    # Fan / Pump / Compressor / EEV telemetry (Holding 197-217)
    _ro_sensor(197, "fan_output", "Fan Output", 0.1, "%", None, clamp_min=0.0),
    _ro_sensor(198, "pump_output", "Pump Output", 0.1, "%", None, clamp_min=0.0),
    _ro_sensor(199, "fan1_rpm_out", "Fan 1 Target Speed", 1, "rpm", None, DataType.UINT16, diagnostic=True),
    _ro_sensor(200, "fan1_rpm_feedback", "Fan 1 Speed", 1, "rpm", None, DataType.UINT16),
    _ro_sensor(201, "fan2_rpm_out", "Fan 2 Target Speed", 1, "rpm", None, DataType.UINT16, diagnostic=True),
    _ro_sensor(202, "fan2_rpm_feedback", "Fan 2 Speed", 1, "rpm", None, DataType.UINT16, diagnostic=True),
    _ro_sensor(203, "compressor_request", "Compressor Required Capacity", 0.1, "%", None, diagnostic=True),
    _ro_sensor(204, "compressor_actual_cap", "Compressor Actual Capacity", 0.1, "%", None),
    _ro_sensor(205, "compressor_speed", "Compressor Speed", 0.1, "rps", None, clamp_min=0.0),
    _ro_sensor(206, "evap_temp", "Evaporation Temperature", 0.1, "°C", "temperature", diagnostic=True),
    _ro_sensor(207, "eev_opening", "EEV Opening", 1, "steps", None, DataType.INT16, diagnostic=True),
    _ro_sensor(208, "discharge_superheat", "Discharge Superheat", 0.1, "°C", "temperature", diagnostic=True),
    _ro_sensor(
        209,
        "bldc_status",
        "BLDC Compressor Status",
        1,
        None,
        None,
        DataType.UINT16,
        diagnostic=True,
        options=CAREL_BLDC_STATUS_OPTIONS,
    ),
    _ro_sensor(
        210,
        "eev_protection",
        "EEV Protection Status",
        1,
        None,
        None,
        DataType.UINT16,
        diagnostic=True,
        options=CAREL_EEV_PROT_OPTIONS,
    ),
    _ro_sensor(211, "suction_superheat", "Suction Superheat", 0.1, "°C", "temperature", diagnostic=True),
    _ro_sensor(
        215,
        "unit_run_mode",
        "Active Run Mode",
        1,
        None,
        None,
        DataType.UINT16,
        options=CAREL_RUN_MODE_OPTIONS,
    ),
    _ro_sensor(216, "target_temp", "Active Target Temperature", 0.1, "°C", "temperature"),
    _ro_sensor(
        217,
        "unit_status",
        "Unit Status",
        1,
        None,
        None,
        DataType.UINT16,
        options=CAREL_STATUS_OPTIONS,
    ),
    # BLDC Inverter Electrical Telemetry (Holding 333-335, optional batch)
    _ro_sensor(333, "bldc_power", "BLDC Motor Power", 100, "W", "power", DataType.INT16, clamp_min=0.0),
    _ro_sensor(334, "bldc_voltage", "BLDC Motor Voltage", 1, "V", "voltage", DataType.UINT16),
    _ro_sensor(335, "bldc_current", "BLDC Motor Current", 0.1, "A", "current", DataType.INT16, clamp_min=0.0),
    # Firmware version & model identification (Holding 325-329, optional RW batch)
    _ro_sensor(325, "fw_version_x", "Firmware Version Major", 1, None, None, DataType.UINT16, diagnostic=True),
    _ro_sensor(326, "fw_version_y", "Firmware Version Minor", 1, None, None, DataType.UINT16, diagnostic=True),
    _ro_sensor(327, "fw_version_z", "Firmware Version Patch", 1, None, None, DataType.UINT16, diagnostic=True),
    # Aggregated active alarms text sensor (populated from DI 13..177 in CarelController)
    SensorSpec(
        key="active_alarms",
        name="Active Alarms",
        address=-1,
        space=RegisterSpace.DISCRETE_INPUT,
        data_type=DataType.UINT16,
        diagnostic=True,
    ),
)

# ---------------------------------------------------------------------------
# Core binary sensors (Discrete Inputs 0..12 & 178..183 + aggregated alarm)
# ---------------------------------------------------------------------------


def _di_sensor(
    address: int,
    key: str,
    name: str,
    *,
    diagnostic: bool = False,
    device_class: str | None = None,
) -> BinarySensorSpec:
    return BinarySensorSpec(
        key=key,
        name=name,
        address=address,
        bit=None,
        space=RegisterSpace.DISCRETE_INPUT,
        diagnostic=diagnostic,
        device_class=device_class,
    )


CAREL_CORE_BINARY_SENSORS: tuple[BinarySensorSpec, ...] = (
    _di_sensor(0, "unit_on", "Unit Running", device_class="running"),
    _di_sensor(1, "flow_switch", "Flow Switch", diagnostic=True),
    _di_sensor(2, "linkage_switch", "Remote Linkage Switch", diagnostic=True),
    _di_sensor(3, "ac_linkage_switch", "A/C Linkage Switch", diagnostic=True),
    _di_sensor(4, "phase_switch", "Phase Protection Input", diagnostic=True),
    _di_sensor(5, "fan_high_speed", "Fan High Speed Relay", diagnostic=True),
    _di_sensor(6, "fan_low_speed", "Fan Low Speed Relay", diagnostic=True),
    _di_sensor(7, "four_way_valve", "4-Way Valve", diagnostic=True),
    _di_sensor(8, "pump_output_relay", "Circulation Pump Relay", diagnostic=True),
    _di_sensor(9, "chassis_heater", "Chassis Heater", device_class="heat"),
    _di_sensor(10, "crank_heater", "Crankcase Heater", device_class="heat"),
    _di_sensor(11, "three_way_valve", "3-Way Valve (DHW)", diagnostic=True),
    _di_sensor(12, "electric_heater", "Backup Electric Heater", device_class="heat"),
    _di_sensor(178, "pump_running", "Circulation Pump Status", device_class="running"),
    _di_sensor(179, "compressor_running", "Compressor Status", device_class="running"),
    _di_sensor(180, "fan_running", "Fan Status", device_class="running"),
    _di_sensor(181, "cooling_linkage", "Cooling Linkage Input", diagnostic=True),
    _di_sensor(182, "heating_linkage", "Heating Linkage Input", diagnostic=True),
    _di_sensor(183, "terminal_pump", "Terminal Pump Relay", diagnostic=True),
    BinarySensorSpec(
        key="alarm_active",
        name="Alarm Active",
        address=-1,
        bit=None,
        space=RegisterSpace.DISCRETE_INPUT,
        diagnostic=True,
        device_class="problem",
    ),
)

# ---------------------------------------------------------------------------
# Core writable numbers, selects, switches, and buttons
# ---------------------------------------------------------------------------

CAREL_NUMBERS: tuple[NumberSpec, ...] = (
    NumberSpec(
        key="heating_setpoint",
        name="Heating Setpoint",
        address=1,
        data_type=DataType.INT16,
        scale=0.1,
        unit="°C",
        min_value=10.0,
        max_value=55.0,
        step=0.5,
        device_class="temperature",
        supports_temp_step_override=True,
        is_primary=True,
    ),
    NumberSpec(
        key="cooling_setpoint",
        name="Cooling Setpoint",
        address=2,
        data_type=DataType.INT16,
        scale=0.1,
        unit="°C",
        min_value=12.0,
        max_value=40.0,
        step=0.5,
        device_class="temperature",
        supports_temp_step_override=True,
        is_primary=True,
    ),
    NumberSpec(
        key="hotwater_setpoint",
        name="Hot Water Setpoint",
        address=3,
        data_type=DataType.INT16,
        scale=0.1,
        unit="°C",
        min_value=10.0,
        max_value=60.0,
        step=0.5,
        device_class="temperature",
        supports_temp_step_override=True,
        is_primary=True,
    ),
    NumberSpec(
        key="hotwater_start_diff",
        name="Hot Water Start Differential",
        address=4,
        data_type=DataType.INT16,
        scale=0.1,
        unit="°C",
        min_value=1.0,
        max_value=15.0,
        step=0.5,
        device_class="temperature",
    ),
    NumberSpec(
        key="hotwater_stop_diff",
        name="Hot Water Stop Differential",
        address=5,
        data_type=DataType.INT16,
        scale=0.1,
        unit="°C",
        min_value=0.0,
        max_value=5.0,
        step=0.5,
        device_class="temperature",
    ),
    NumberSpec(
        key="temp_diff_start",
        name="Heating/Cooling Start Differential",
        address=6,
        data_type=DataType.INT16,
        scale=0.1,
        unit="°C",
        min_value=1.0,
        max_value=15.0,
        step=0.5,
        device_class="temperature",
    ),
    NumberSpec(
        key="temp_diff_stop",
        name="Heating/Cooling Stop Differential",
        address=7,
        data_type=DataType.INT16,
        scale=0.1,
        unit="°C",
        min_value=0.0,
        max_value=5.0,
        step=0.5,
        device_class="temperature",
    ),
    NumberSpec(
        key="aux_heat_ambient_setpoint",
        name="Auxiliary Heater Ambient Threshold",
        address=14,
        data_type=DataType.INT16,
        scale=0.1,
        unit="°C",
        min_value=-30.0,
        max_value=20.0,
        step=0.5,
        device_class="temperature",
    ),
    NumberSpec(
        key="pump_delta_t_setpoint",
        name="Pump Target Delta T",
        address=15,
        data_type=DataType.INT16,
        scale=0.1,
        unit="°C",
        min_value=1.0,
        max_value=15.0,
        step=0.5,
        device_class="temperature",
    ),
)

CAREL_SELECTS: tuple[SelectSpec, ...] = (
    SelectSpec(
        key="unit_mode",
        name="Unit Mode",
        address=0,
        options=CAREL_UNIT_MODE_OPTIONS,
        is_config=False,
    ),
    SelectSpec(
        key="pump_mode",
        name="Pump Mode",
        address=11,
        options=CAREL_PUMP_MODE_OPTIONS,
        is_config=True,
    ),
    SelectSpec(
        key="fan_mode",
        name="Fan Mode",
        address=12,
        options=CAREL_FAN_MODE_OPTIONS,
        is_config=True,
    ),
)

CAREL_SWITCHES: tuple[SwitchSpec, ...] = (
    SwitchSpec(
        key="power",
        name="Power",
        address=40,
        bit=None,
        space=RegisterSpace.COIL,
        is_config=False,
    ),
    # Coil 42 (00043) in OEM docs: 0 = Hot water ON, 1 = Hot water OFF (active-low)
    SwitchSpec(
        key="dhw_enable",
        name="Hot Water Function Enable",
        address=42,
        bit=None,
        space=RegisterSpace.COIL,
        is_config=True,
        inverted=True,
    ),
    SwitchSpec(
        key="aux_heat_enable",
        name="Auxiliary Heater Enable",
        address=0,
        bit=None,
        space=RegisterSpace.COIL,
        is_config=True,
    ),
    SwitchSpec(
        key="auto_restart",
        name="Auto Restart After Power Loss",
        address=2,
        bit=None,
        space=RegisterSpace.COIL,
        is_config=True,
    ),
    SwitchSpec(
        key="schedule_onoff_enable",
        name="Schedule ON/OFF Enable",
        address=38,
        bit=None,
        space=RegisterSpace.COIL,
        is_config=True,
    ),
    SwitchSpec(
        key="schedule_setpoint_enable",
        name="Schedule Setpoint Enable",
        address=39,
        bit=None,
        space=RegisterSpace.COIL,
        is_config=True,
    ),
)

CAREL_BUTTONS: tuple[ButtonSpec, ...] = (
    ButtonSpec(
        key="reset_alarm",
        name="Reset Alarm",
        address=41,
        bit=None,
        space=RegisterSpace.COIL,
        description="Reset active CAREL alarms (Coil 41 / 00042)",
        write_value=True,
        diagnostic=True,
    ),
)

# ---------------------------------------------------------------------------
# Opt-in expert controls (gated behind enable_expert_writes=True)
# ---------------------------------------------------------------------------


def _expert_num(
    address: int,
    key: str,
    name: str,
    min_value: float,
    max_value: float,
    *,
    scale: float | int = 0.1,
    step: float = 0.5,
    unit: str | None = "°C",
    device_class: str | None = "temperature",
    data_type: DataType = DataType.INT16,
) -> NumberSpec:
    return NumberSpec(
        key=key,
        name=name,
        address=address,
        data_type=data_type,
        scale=scale,
        unit=unit,
        min_value=min_value,
        max_value=max_value,
        step=step,
        device_class=device_class,
        is_expert=True,
    )


CAREL_EXPERT_NUMBERS: tuple[NumberSpec, ...] = (
    # PID & auxiliary delay (Holding 8..10, 13)
    _expert_num(8, "pid_kp", "PID Proportional Gain (Kp)", 0.0, 99.9, scale=0.1, step=0.1, unit=None, device_class=None),
    _expert_num(9, "pid_ti", "PID Integral Time (Ti)", 0.0, 9999.0, scale=1, step=1.0, unit="s", device_class=None, data_type=DataType.UINT16),
    _expert_num(10, "pid_td", "PID Derivative Time (Td)", 0.0, 9999.0, scale=1, step=1.0, unit="s", device_class=None, data_type=DataType.UINT16),
    _expert_num(13, "aux_comp_delay", "Auxiliary Heater Delay", 0.0, 999.0, scale=1, step=1.0, unit="min", device_class=None, data_type=DataType.UINT16),
    # Night mode limits (Holding 263..264)
    _expert_num(263, "night_mode_comp_max_speed", "Night Mode Compressor Max Speed", 0.0, 120.0, scale=0.1, step=1.0, unit="rps", device_class=None),
    _expert_num(264, "night_mode_fan_max_speed", "Night Mode Fan Max Speed", 0.0, 1000.0, scale=0.1, step=10.0, unit="rpm", device_class=None),
    # ECO curves — Cooling (X1..X4 = 276..279, Y1 = 336, Y2..Y4 = 288..290)
    _expert_num(276, "eco_cool_x1", "ECO Cooling Ambient X1", -50.0, 70.0),
    _expert_num(277, "eco_cool_x2", "ECO Cooling Ambient X2", -50.0, 70.0),
    _expert_num(278, "eco_cool_x3", "ECO Cooling Ambient X3", -50.0, 70.0),
    _expert_num(279, "eco_cool_x4", "ECO Cooling Ambient X4", -50.0, 70.0),
    _expert_num(336, "eco_cool_y1", "ECO Cooling Water Y1", 5.0, 40.0),
    _expert_num(288, "eco_cool_y2", "ECO Cooling Water Y2", 5.0, 40.0),
    _expert_num(289, "eco_cool_y3", "ECO Cooling Water Y3", 5.0, 40.0),
    _expert_num(290, "eco_cool_y4", "ECO Cooling Water Y4", 5.0, 40.0),
    # ECO curves — Heating (X1..X4 = 280..283, Y1..Y3 = 291..293, Y4 = 337)
    _expert_num(280, "eco_heat_x1", "ECO Heating Ambient X1", -50.0, 70.0),
    _expert_num(281, "eco_heat_x2", "ECO Heating Ambient X2", -50.0, 70.0),
    _expert_num(282, "eco_heat_x3", "ECO Heating Ambient X3", -50.0, 70.0),
    _expert_num(283, "eco_heat_x4", "ECO Heating Ambient X4", -50.0, 70.0),
    _expert_num(291, "eco_heat_y1", "ECO Heating Water Y1", 10.0, 65.0),
    _expert_num(292, "eco_heat_y2", "ECO Heating Water Y2", 10.0, 65.0),
    _expert_num(293, "eco_heat_y3", "ECO Heating Water Y3", 10.0, 65.0),
    _expert_num(337, "eco_heat_y4", "ECO Heating Water Y4", 10.0, 65.0),
    # ECO curves — Hot Water (X1..X4 = 284..287, Y1..Y3 = 294..296, Y4 = 338)
    _expert_num(284, "eco_hw_x1", "ECO Hot Water Ambient X1", -50.0, 70.0),
    _expert_num(285, "eco_hw_x2", "ECO Hot Water Ambient X2", -50.0, 70.0),
    _expert_num(286, "eco_hw_x3", "ECO Hot Water Ambient X3", -50.0, 70.0),
    _expert_num(287, "eco_hw_x4", "ECO Hot Water Ambient X4", -50.0, 70.0),
    _expert_num(294, "eco_hw_y1", "ECO Hot Water Y1", 10.0, 65.0),
    _expert_num(295, "eco_hw_y2", "ECO Hot Water Y2", 10.0, 65.0),
    _expert_num(296, "eco_hw_y3", "ECO Hot Water Y3", 10.0, 65.0),
    _expert_num(338, "eco_hw_y4", "ECO Hot Water Y4", 10.0, 65.0),
    # Defrost tuning parameters (Holding 77..91)
    _expert_num(77, "defrost_min_speed_change", "Defrost Min Speed When Change", 30.0, 90.0, scale=0.1, step=1.0, unit="rps", device_class=None),
    _expert_num(78, "defrost_eev_opening", "Defrost EEV Opening", 0.0, 480.0, scale=1, step=1.0, unit="steps", device_class=None, data_type=DataType.UINT16),
    _expert_num(79, "defrost_quit_eev_opening", "Defrost Quit EEV Opening", 0.0, 480.0, scale=1, step=1.0, unit="steps", device_class=None, data_type=DataType.UINT16),
    _expert_num(81, "defrost_comp_speed", "Defrost Compressor Speed", 30.0, 120.0, scale=0.1, step=1.0, unit="rps", device_class=None),
    _expert_num(82, "defrost_pump_speed", "Defrost Pump Speed", 0.0, 100.0, scale=0.1, step=1.0, unit="%", device_class=None),
    _expert_num(83, "defrost_start_setpoint", "Defrost Start Coil Temp", -20.0, 30.0),
    _expert_num(84, "defrost_end_setpoint", "Defrost End Coil Temp", 0.0, 30.0),
    _expert_num(85, "defrost_ambient_setpoint", "Defrost Max Ambient Temp", -30.0, 30.0),
    _expert_num(86, "defrost_ambient_coil_diff", "Defrost Ambient-Coil Temp Diff", 1.0, 30.0),
    _expert_num(87, "defrost_delay", "Defrost Start Delay", 0.0, 90.0, scale=1, step=1.0, unit="min", device_class=None, data_type=DataType.UINT16),
    _expert_num(88, "defrost_min_time", "Defrost Min Duration", 1.0, 99.0, scale=1, step=1.0, unit="min", device_class=None, data_type=DataType.UINT16),
    _expert_num(89, "defrost_max_time", "Defrost Max Duration", 1.0, 99.0, scale=1, step=1.0, unit="min", device_class=None, data_type=DataType.UINT16),
    _expert_num(90, "defrost_interval_time", "Defrost Interval Time", 0.0, 480.0, scale=1, step=1.0, unit="min", device_class=None, data_type=DataType.UINT16),
    _expert_num(91, "defrost_auto_every", "Automatic Defrost Every", 1.0, 999.0, scale=1, step=1.0, unit="min", device_class=None, data_type=DataType.UINT16),
)

CAREL_EXPERT_SELECTS: tuple[SelectSpec, ...] = (
    SelectSpec(
        key="heater_type",
        name="Electric Heater Type",
        address=323,
        options=CAREL_HEATER_TYPE_OPTIONS,
        is_config=True,
        is_expert=True,
    ),
)

CAREL_EXPERT_SWITCHES: tuple[SwitchSpec, ...] = (
    SwitchSpec(
        key="ac_linkage_normally_open",
        name="A/C Linkage Normally Open",
        address=18,
        bit=None,
        space=RegisterSpace.COIL,
        is_config=True,
        is_expert=True,
    ),
    SwitchSpec(
        key="defrost_enable",
        name="Defrost Function Enable",
        address=36,
        bit=None,
        space=RegisterSpace.COIL,
        is_config=True,
        is_expert=True,
    ),
)
