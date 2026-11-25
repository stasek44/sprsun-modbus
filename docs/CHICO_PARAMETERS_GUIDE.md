# 📖 SPRSUN Heat Pump Parameters & Settings Guide

## Table of Contents
- [1. Basic Parameters (P)](#1-basic-parameters-p)
- [2. Economic Curve Parameters (E)](#2-economic-curve-parameters-e)
- [3. General / Engineering Parameters (G)](#3-general--engineering-parameters-g)
- [4. Temperature Readings](#4-temperature-readings)
- [5. System Operation Readings](#5-system-operation-readings)
- [6. Input and Output Statuses](#6-input-and-output-statuses)
- [7. Alarms and Faults](#7-alarms-and-faults)
- [8. Advanced Parameters](#8-advanced-parameters)
- [9. Controls](#9-controls)
- [10. Practical Tips & Troubleshooting](#10-practical-tips--troubleshooting)
- [11. Additional Information](#11-additional-information)

---

## 1. Basic Parameters (P)

### P01 - Heating Setpoint (0x00CC)
**Range:** 10–55°C | **Default:** ~45°C  
**Target water temperature in space heating mode.**

- Sets the desired heating flow water temperature (for radiators / underfloor heating).
- Higher value = warmer rooms, but higher electrical consumption.
- For underfloor heating: typically 30–40°C.
- For traditional radiators: typically 45–55°C.

### P02 - Cooling Setpoint (0x00CB)
**Range:** 12–30°C | **Default:** ~18°C  
**Target water temperature in cooling mode.**

- Sets the desired chilled water temperature (fan-coils, surface/underfloor cooling).
- Lower value = cooler indoor temperature.
- Typically: 15–18°C for active cooling.

### P03 - Temp Diff (Heating/Cooling) (0x00C6)
**Range:** 2–18°C | **Default:** 5°C  
**Temperature hysteresis for heating and cooling.**

- The temperature delta at which the heat pump starts and stops.
- Example: Setpoint 45°C, diff 5°C → pump stops at 45°C and restarts when water drops to 40°C.
- Higher value = fewer on/off compressor cycles (longer lifespan, energy savings, slightly wider temperature swings).
- Lower value = tighter temperature control, but more frequent compressor starts.

### P04 - Hot Water Setpoint (0x00CA)
**Range:** 10–55°C | **Default:** ~50°C  
**Target domestic hot water (DHW) temperature.**

- Sets the target water temperature in the DHW cylinder/tank.
- Typically: 45–55°C.
- **Note:** For setpoints below 55°C, enabling the antilegionella disinfection function is strongly recommended.

### P05 - Hot Water Temp Diff (0x00C8)
**Range:** 2–18°C | **Default:** 5°C  
**Temperature hysteresis for domestic hot water (DHW).**

- The temperature drop before the heat pump starts heating the DHW tank.
- Example: Setpoint 50°C, diff 5°C → pump triggers DHW heating when tank drops to 45°C.

### P06 - Unit Mode (0x0036)
**Operating mode of the heat pump.**

- **0 - DHW (Hot Water Only):** DHW water heating only.
- **1 - Heating Only:** Space heating only.
- **2 - Cooling Only:** Space cooling only.
- **3 - Heating + DHW:** Space heating combined with DHW (typical winter mode).
- **4 - Cooling + DHW:** Space cooling combined with DHW (typical summer mode).

**Usage recommendations:**
- Winter: Mode 3 (Heating + DHW).
- Summer: Mode 4 (Cooling + DHW) or Mode 0 (DHW only).
- Temporary rapid DHW reheat: Mode 0.

### P07 - Fan Mode (0x0190)
**Outdoor fan speed profile.**

- **0 - Normal:** Standard fan speed, optimal performance.
- **1 - Economic:** Lower fan RPM = quieter operation, lower power draw, slightly reduced thermal capacity.
- **2 - Night:** Night mode — lowest fan RPM for whisper-quiet operation.
- **3 - Test:** Test mode — full speed fan operation for diagnostics.

**When to use:**
- Normal: Standard daily operation.
- Economic: When energy efficiency or reduced noise is prioritized.
- Night: Scheduled during sleep hours to prevent disturbing neighbors.
- Test: Diagnostic and performance verification.

---

## 2. Economic Curve Parameters (E)

**Concept:** Automatic adjustment of the target water setpoint based on the outdoor ambient temperature (weather compensation heating/cooling curve).

### E01–E04 - Economic Heat Ambient (0x0169–0x016C)
**Range:** -30 to 50°C | **Outdoor ambient temperature reference points for heating curve**

Defines 4 outdoor ambient temperature inflection points:
- **E01:** Lowest outdoor design temperature (e.g., -20°C).
- **E02:** Cold outdoor temperature (e.g., -10°C).
- **E03:** Moderate outdoor temperature (e.g., 0°C).
- **E04:** Mild outdoor temperature (e.g., +10°C).

### E13–E16 - Economic Heat Temp (0x0175–0x0178)
**Range:** 10–55°C | **Target water temperatures corresponding to E01–E04**

Water setpoints mapped to the ambient temperatures:
- **E13:** Water temp when outdoor is E01 (e.g., 55°C at -20°C).
- **E14:** Water temp when outdoor is E02 (e.g., 50°C at -10°C).
- **E15:** Water temp when outdoor is E03 (e.g., 45°C at 0°C).
- **E16:** Water temp when outdoor is E04 (e.g., 35°C at +10°C).

**Example Behavior:**
```
Outdoor temperature = -15°C
The controller interpolates linearly between E01 (-20°C / 55°C) and E02 (-10°C / 50°C).
Resulting water setpoint: ~52.5°C.
```

### E05–E08 - Economic Water Ambient (0x016D–0x0170)
**Range:** -30 to 50°C | **Outdoor temperature reference points for DHW**

Analogous to E01–E04, applied to domestic hot water generation.

### E17–E20 - Economic Water Temp (0x0179–0x017C)
**Range:** 10–55°C | **Target DHW temperatures corresponding to E05–E08**

Corresponding target DHW temperatures.

### E09–E12 - Economic Cool Ambient (0x0171–0x0174)
**Range:** -30 to 50°C | **Outdoor temperature reference points for cooling**

Analogous to E01–E04, applied to space cooling.

### E21–E24 - Economic Cool Temp (0x017D–0x0180)
**Range:** 12–30°C | **Target chilled water temperatures corresponding to E09–E12**

Corresponding target chilled water temperatures for cooling.

**Benefits of Economic Mode Curves:**
- Automatic seasonal adaptation without manual setpoint changes.
- Significant electricity savings by avoiding unnecessary water overheating or subcooling.
- Maximum seasonal coefficient of performance (SCOP).

---

## 3. General / Engineering Parameters (G)

### G02 - Pump Work Mode (0x019E)
**Circulation water pump operating profile.**

- **0 - Interval:** Pump runs periodically (e.g. 3 minutes every 30 minutes) — prevents water stagnation and pipe freezing during extended idle periods.
- **1 - Normal:** Pump runs continuously whenever space heating or cooling is active (Always On).
- **2 - Demand:** Pump runs only when there is an active heating/cooling demand — most economical, but may cause more frequent compressor cycling.

**Mode recommendations:**
- **Interval:** Recommended during summer or when heating is turned off for long periods (protects against freezing and lime buildup).
- **Normal:** Standard heating season setting — continuous flow provides uniform heat distribution and accurate return temperature sensing.
- **Demand:** Best for energy conservation where room thermostats regulate flow.

**DC / Inverter Circulation Pump Control:**
If your installation uses a variable-speed DC pump connected to the controller:
- In Normal or Demand mode, pump speed is automatically modulated to maintain the target delta T set in G04.
- Higher delta T = lower pump speed = reduced electricity consumption.

### G03 - Start Interval (0x0185)
**Range:** 1–120 minutes | **Minimum compressor restart protection delay**

- Protects the compressor against short-cycling and rapid pressure equalization stress.
- Typical setting: 5–10 minutes.

### G04 - DC Pump Temp Differential (0x018D)
**Range:** 5–30°C | **Target temperature differential (Delta T) for DC pump**

- Active only when a variable-speed inverter DC circulation pump is installed.
- Controls pump speed to maintain the specified temperature difference between heating flow and return.
- Higher value (e.g. 10–15°C) = slower pump flow = larger Delta T.
- Lower value (e.g. 5–8°C) = faster pump flow = smaller Delta T = better mixing.

### G05 - Heating Heater External Temp (0x0184)
**Range:** -30 to 30°C | **Bivalent auxiliary electric heater threshold for heating (OUT4)**

- Outdoor temperature below which the auxiliary electric heating element is allowed to engage.
- Typically: -10°C to -5°C.
- Delay before turning on is governed by G06.

### G06 - Heating Heater Delay (0x0182)
**Range:** 1–60 minutes | **Delay before activating heating auxiliary heater**

- Waiting time before energizing the electric auxiliary element, giving the heat pump compressor time to reach the setpoint alone.
- Typically: 15–30 minutes.

### G07 - Hot Water Heater External Temp (0x0183)
**Range:** -30 to 30°C | **Auxiliary electric heater threshold for DHW (OUT12)**

- Outdoor temperature below which the DHW tank booster heater is allowed to engage.
- Delay before turning on is governed by G08.

### G08 - Hot Water Heater Delay (0x0181)
**Range:** 1–60 minutes | **Delay before activating DHW auxiliary heater**

- Waiting time before energizing the DHW electric element.
- Typically: 15–30 minutes.

### G09 - Mode Control Enable (0x0191)
**Automatic heating / cooling changeover based on ambient temperature.**

- **0 - NO linkage (Manual):** Operating mode is set manually via P06.
- **1 - YES amb (Automatic):** Automatic switching between heating and cooling based on outdoor ambient temperature thresholds (G10 / G11).

**Automatic changeover logic:**
1. Configure G10 (setpoint, e.g., 20°C).
2. Configure G11 (hysteresis, e.g., 3°C).
3. When outdoor temperature > G10 + G11 (e.g. >23°C) → switches automatically to cooling (or cooling + DHW).
4. When outdoor temperature < G10 - G11 (e.g. <17°C) → switches automatically to heating (or heating + DHW).
5. Between 17°C and 23°C → maintains the current operating mode without hunting.

### G10 - Ambient Switch Setpoint (0x0192)
**Range:** -20 to 30°C | **Changeover ambient temperature setpoint**

- Baseline outdoor temperature threshold for automatic heating/cooling changeover.
- Typically: 18–22°C.

### G11 - Ambient Switch Diff (0x0193)
**Range:** 1–10°C | **Changeover ambient hysteresis**

- Deadband around G10 to prevent rapid cycling between heating and cooling during spring and autumn.

---

## 4. Temperature Readings

### Water Circuit Sensors

- **Inlet Water Temperature (0x000E):** Water temperature returning from the heating system into the heat pump.
- **Outlet Water Temperature (0x0012):** Water temperature leaving the heat pump towards the heating system (flow).
- **Hot Water Temperature (0x000F):** Water temperature inside the DHW storage cylinder.

### Refrigerant Circuit Sensors (R32 / R410A)

- **Ambient Temperature (0x0011):** Outdoor ambient air temperature.  
  ⚠️ **SIGNED VALUE** (can be negative). Essential for weather curves and automatic defrost.
- **Suction Gas Temperature (0x0015):** Refrigerant vapor temperature prior to entering the compressor suction port.  
  ⚠️ **SIGNED VALUE** (can be negative).
- **Discharge / Exhaust Temperature (0x001B):** Superheated refrigerant vapor temperature leaving the compressor.  
  Normal: 60–85°C. Critical threshold: >100°C indicates overheating or refrigerant shortage.
- **Driving Temperature (0x0022):** Power inverter module / drive heatsink temperature.  
  ⚠️ **SIGNED VALUE** (can be negative).
- **Coil Temperature (0x0016):** Outdoor finned heat exchanger coil temperature.  
  ⚠️ **SIGNED VALUE** (can be negative). In heating mode, this drops below 0°C; triggers defrost cycles.
- **Evaporator Temperature (0x0028):** Refrigerant evaporating temperature.  
  ⚠️ **SIGNED VALUE** (can be negative).
- **Condenser Temperature (0x0029):** Refrigerant condensing temperature. Typically 35–50°C.

### Pressure Sensors

- **Discharge Pressure (0x002F) & Suction Pressure (0x0030):**  
  ⚠️ **MODBUS MAPPING NOTE:** In the CHICO register specification, registers 0x002F and 0x0030 are swapped compared to standard vendor docs. In this integration:
  - `0x002F` = High pressure / discharge (~15–30 bar).
  - `0x0030` = Low pressure / suction (~4–7 bar).
  - Both converted to `bar` (0.1 PSI to bar multiplier 0.0069).

---

## 5. System Operation Readings

### Performance & Energy

- **COP (0x0001):** Coefficient of Performance (Real-time Thermal Output / Electrical Power Input). Typical: 3.0–5.0 depending on ambient conditions.
- **Heating/Cooling Capacity (0x0019):** Estimated real-time thermal output delivered to the water circuit [W].
- **EEV1 / EEV2 Step (0x001C / 0x001D):** Electronic expansion valve opening position (0–500 steps).

### Electrical Measurements

- **AC Voltage (0x0017):** Incoming mains voltage [V].
- **AC Current (0x001A):** Total active line current drawn by the unit [A].
- **DC Bus Voltage (0x0021):** Inverter DC bus internal voltage [V] (typically 300–380V).
- **Compressor Current (0x0023):** Current drawn by the inverter compressor [A].

### Speeds & Frequencies

- **Compressor Frequency (0x001E):** Current operating frequency of the compressor inverter [Hz].
- **Target Frequency (0x0024):** Commanded compressor frequency target [Hz].
- **DC Fan 1 & 2 Speed (0x0026 / 0x0027):** Actual fan rotational speeds [RPM].
- **DC Fan Target (0x0031):** Commanded target speed for the outdoor fans [RPM].
- **DC Pump Speed (0x002E):** Modulation percentage of the DC circulation pump [%].

### Operational Metrics & Diagnostics

- **Compressor Runtime (0x0000):** Cumulative operating hours of the compressor [h].
- **Pump Flow (0x0018):** Primary water loop flow rate [m³/h].
- **Firmware Versions (0x0013 / 0x0014 / 0x002C / 0x002D):** Software, controller, and display firmware version registers.

---

## 6. Input and Output Statuses

### Switching Input Symbol (0x0002) - Digital Inputs

- **Bit 0 - A/C Linkage Switch:** External A/C demand signal.
- **Bit 1 - Linkage Switch:** Master external thermostat contact.
- **Bit 2 - Heating Linkage:** External heating demand contact.
- **Bit 3 - Cooling Linkage:** External cooling demand contact.
- **Bit 4 - Flow Switch:** Safety water flow paddle switch (1 = flow OK).
- **Bit 5 - High Pressure Switch:** Safety high pressure mechanical switch.
- **Bit 6 - Phase Sequence OK:** Correct 3-phase power supply sequencing (3-phase models).

### Working Status Mark (0x0003) - Operational State Flags

- **Bit 0 - Hot Water Demand:** DHW heating demand is active.
- **Bit 1 - Heating Demand:** Space heating demand is active.
- **Bit 4 - Antilegionella Active:** High-temperature DHW pasteurization cycle running.
- **Bit 5 - Cooling Demand:** Space cooling demand is active.
- **Bit 6 - Alarm Stop:** Unit halted due to an active protection fault or alarm.
- **Bit 7 - Defrost Active:** Reverse-cycle evaporator coil defrosting in progress.

### Output Symbols (Relay Outputs)

#### Output Symbol 1 (0x0004)
- **Bit 0 - Compressor:** Compressor contactor / inverter active.
- **Bit 5 - Fan:** Outdoor evaporator fan active.
- **Bit 6 - 4-Way Valve:** Reversing valve energized (0 = Heating, 1 = Cooling/Defrost).
- **Bit 7 - Fan High Speed:** Fan high-speed winding/setting engaged.

#### Output Symbol 2 (0x0005)
- **Bit 0 - Chassis Heater:** Base pan defrost drainage trace heater.
- **Bit 5 - Heating Heater:** Space heating auxiliary electric heater contactor (OUT4).
- **Bit 6 - 3-Way Valve:** Diverting valve position (0 = Space Heating/Cooling, 1 = DHW Cylinder).
- **Bit 7 - Hot Water Heater:** DHW cylinder auxiliary electric immersion heater contactor (OUT12).

#### Output Symbol 3 (0x0006)
- **Bit 0 - A/C Pump:** Auxiliary cooling loop pump.
- **Bit 1 - Crank Heater:** Compressor crankcase oil warming belt.
- **Bit 5 - Assistant Solenoid Valve:** Bypass / liquid injection solenoid valve.
- **Bit 6 - Circulation Pump:** Primary heating system water circulation pump.

---

## 7. Alarms and Faults

### Failure Symbol 1 (0x0007) - Sensor Open / Short Faults
- **Bit 0:** Hot Water Temperature Sensor Error.
- **Bit 1:** Ambient Temperature Sensor Error.
- **Bit 2:** Coil Temperature Sensor Error.
- **Bit 4:** Outlet Water Temperature Sensor Error.
- **Bit 5:** High Pressure Sensor Error.
- **Bit 7:** Phase Sequence Error (3-phase supplies).

### Failure Symbol 2 (0x0008) - Flow & Protection
- **Bit 0 - Water Flow Error:** No water flow detected through the heat pump (check circulator, valves, air locks, dirt strainer).
- **Bit 2 - High Temp Protection:** Outlet flow water temperature exceeded safety limits during heating.

### Failure Symbol 3 (0x0009) & Symbol 4 (0x000A)
- **Symbol 3, Bit 6:** Outlet Gas Temperature Sensor Error.
- **Symbol 4, Bit 0:** Inlet Water Temperature Sensor Error.
- **Symbol 4, Bit 1:** Exhaust Temperature Too High (>105°C — critical compressor protection shutdown).
- **Symbol 4, Bit 5:** Low Temperature Protection (Outlet water below freezing in cooling mode).
- **Symbol 4, Bit 6:** Suction Gas Temperature Sensor Error.

### Failure Symbol 5 (0x000B) - Pressure Protections (High Priority)
- **Bit 0 - Low Pressure Protection:** Refrigerant suction pressure dropped below minimum safety limit (leakage, blocked filter drier, EEV failure).
- **Bit 1 - High Pressure Protection:** Refrigerant discharge pressure exceeded high limit (fouled condenser, fan motor failure, air in refrigerant circuit).
- **Bit 2:** Coil Temperature Too High.
- **Bit 6 / 7:** High / Low Pressure Transducer Signal Failure.

### Failure Symbol 6 (0x000C) & Symbol 7 (0x000D) - System & Inverter
- **Symbol 6, Bit 4 / 5:** Secondary / Primary Antifreeze Protection active.
- **Symbol 7, Bit 1:** Ambient Temperature Below Operating Limits (e.g. below -25°C).
- **Symbol 7, Bit 4 - Inverter Module Fault:** Compressor frequency drive fault (overcurrent, overvoltage, IPM module failure).
- **Symbol 7, Bit 5 / 6:** DC Fan Motor 1 or 2 Failure.

---

## 8. Advanced Parameters

### Antilegionella Disinfection
- **Disinfection Temperature (0x019A):** 30–70°C (recommended: 60°C).
- **Weekday (0x019B):** 0 = Sunday, 1 = Monday, ..., 6 = Saturday.
- **Start Hour (0x019C):** 0–23 (e.g., 2 for 02:00 AM).
- **End Hour (0x019D):** 0–23 (e.g., 4 for 04:00 AM).

**Purpose:** Periodically elevates the DHW cylinder temperature above 60°C to eliminate Legionella pneumophila bacteria.

### Smart Grid Status (0x0025)
- Indicates demand-response status from utility contacts (peak shaving / PV surplus boost).

### Expert / Engineering Parameter Series (Hidden Read-Only Diagnostic by Default)

> ⚠️ **Safety & Visibility Notice:** Expert settings cover the newly mapped CHICO registers (`0x0032–0x01BB`, excluding core user/E/G/Antilegionella controls that were already present in `v5.1.x`). By default, all `353` read-only expert entities (`336` `sensor` + `17` `binary_sensor` under `Diagnostic`) are **disabled by default (`entity_registry_enabled_default = False`)** so they remain hidden in the Home Assistant UI until individually enabled. Writing to them requires explicitly enabling **Enable Expert Settings Writes** (`enable_expert_writes`) in the integration's **Configure** dialog, which adds `337` writable **Configuration** controls (`322` numbers in `box` mode, `2` selects, `13` switches) under the same `SPRSUN Heat Pump` device. Incorrect values can compromise defrosting, refrigerant superheat, or compressor envelope protection.

- **Defrost & Defrost Fan (`H01–H18`, `0x0037–0x0046`, `0x00D4–0x00DB`, `0x01B0–0x01B1`):** Entry/exit coil temperature thresholds (`H03`, `H04`), cycle intervals and durations (`H01`, `H02`, `H05–H16`), and defrost fan pressure/speed limits (`H17`, `H18`).
- **Main Electronic Expansion Valve (`A01–A51`, `0x0047–0x0056`, `0x008A–0x00A1`, `0x00DC–0x00E7`, `0x00BD–0x00BF`):** Target superheat steps, PI PID coefficients, heating/cooling curve ambient steps, and manual vs automatic EEV position (`A45`).
- **Auxiliary / EVI Expansion Valve (`B01–B93`, `0x0057–0x0081`, `0x00B6–0x00BC`, `0x00EC–0x00F3`, `0x01B5`):** Vapor-injection superheat targets, initial openings (`B21–B34`, with deduced unconfirmed pairs `0x006A–0x006F` and `0x0072–0x0077`), and outlet adjustment (`B93`).
- **Fan Curves (`D01–D22`, `0x00A2–0x00B5`, `0x00F4–0x00F5`):** DC fan enable bits (`0x0033` bits 4–5), speed-vs-ambient curves (`D03–D20`), and AC fan ambient switch points (`D21`, `D22`).
- **Factory Limits & Protections (`F01–F56`, `0x0082–0x0089`, `0x00C0–0x00D3`, `0x0186–0x0199`, `0x01A2–0x01A3`, `0x01B2–0x01B9`):**
  - High/low pressure protection and recovery limits (`F02` / `F03` use `+250` raw offset at `0.1 bar` scale, giving `25.0–50.0 bar`), discharge/exhaust limits, water temperature sensor calibrations (`F44–F46`), and heating/cooling temperature limits (`F54`, `F55`).
  - **Model & Pump Mode:** `F13` (`0x0186`: `Manual`/`Auto` DC pump mode) and `F56` (`0x01BA`: `A102508`–`A206008` unit model selection) are exposed as `select` controls when expert writes are enabled.
- **Compressor Frequency Curves (`R00–R94`, `0x00F9–0x0117`, `0x012D–0x0168`, `0x01BB`):** Ambient/water-delta frequency tables for Normal, Economic, Night, and Test fan modes, plus `R94` Oil Return Frequency (`0x01BB`).
- **Timeband Schedules 1–3 (`0x0119–0x0124`, `0x01A4–0x01AF`, `0x0035` bits 0–2):**
  - Start/stop hour & minute (`0x0119–0x0124`), DHW/Heating/Cooling setpoints (`0x01A4–0x01AC`, low-byte `0xFF` masked write), enable switches (`0x0035` bits 0–2), and weekday masks (`0x01AD–0x01AF`, verified on live hardware as 7-bit `0–127` weekday bitmasks rather than `0–6`).

---

## 9. Controls

### Power Switch (0x0032 bit 0)
- Master software On / Off switch for the heat pump.
- `0` = Standby / Off.
- `1` = Operating according to active setpoints and schedules.

### Failure Reset (0x0033 bit 7)
- Instantaneous alarm reset pulse.
- Writing `1` clears latching error codes after the underlying physical fault is corrected.
- Auto-resets back to `0`.

### Control Mark 2 (0x0034)
- **Bit 0 - Antilegionella Enable:** Master switch for weekly scheduled thermal pasteurization.
- **Bit 1 - Two / Three Function (G01):**
  - `0 = Two Function (Heating + Cooling only)`: For installations without a DHW tank or with separate hot water heating.
  - `1 = Three Function (Heating + Cooling + DHW)`: Standard installation with a 3-way diverting valve and DHW cylinder.

### Expert Control Bits (`0x0032`, `0x0033`, `0x0035`)
- **Read-Only Always (`17` binary sensors, hidden by default):** Created with `entity_registry_enabled_default = False` under Diagnostics (`0x0032` bits 1–6, `0x0033` bits 0–6 including inverted `B74 AV Cool Enable` on bit 2, `0x0034` unconfirmed bits 2–4, and `0x0035` bits 0–2) and can be enabled individually in HA if needed.
- **Opt-In Switches (`13` switches when `enable_expert_writes = true`):** Exposes confirmed working switches (`a45_mv_mode_manual`, `manual_freq_selection`, `b01_av_mode_manual`, `b93_av_init_outlet_adjustable`, `r29_constant_freq_adj`, `f01_pressure_switch_enable`, `b74_av_cool_enable`, `b92_av_control_exhaust`, `d01_dcfan1_enable`, `d02_dcfan2_enable`, `timeband_1..3_enable`).
- **Safety Exclusion:** `parameters_reset_flag` (`0x0033` bit 6) is intentionally **never** exposed as a writable switch to prevent accidental factory resets.

---

## 10. Practical Tips & Troubleshooting

### Energy Optimization
1. **Use Weather Compensation Curves (Economic Mode):** Prevents overheating flow water in mild outdoor conditions.
2. **Tune Hysteresis Carefully (P03 / P05):** A setting between 4°C and 6°C strikes an optimal balance between comfort and compressor runtimes.
3. **Set Fan Mode to Economic or Night:** Minimizes acoustic footprint during evening hours.
4. **Target 48–50°C for DHW:** Significant heat pump COP boost compared to heating water to 55°C, while utilizing weekly antilegionella cycles for sanitary safety.
5. **Keep Auxiliary Heater Thresholds Conservative:** Set G05/G07 to -10°C or below to avoid expensive resistive electric heating during normal winter weather.

### Common Issues & Remedies
- **Frequent Short-Cycling:** Increase hysteresis (P03) and check minimum start delay (G03).
- **Insufficient Domestic Hot Water:** Verify P06 is set to a mode including DHW (`0`, `3`, or `4`), ensure G01 (Three Function) is set to `1`, and inspect the 3-way valve actuator.
- **Low Pressure / Antifreeze Alarms in Winter:** Check water flow rate (strainer, pump), verify glycol concentration, and confirm outdoor coil defrost cycles are operating normally.

---

## 11. Additional Information

- Parameter write changes apply to Modbus Slave Address #1 (`device_address = 1`).
- Avoid modifying factory engineering parameters without referencing manufacturer documentation or consulting a certified technician.
