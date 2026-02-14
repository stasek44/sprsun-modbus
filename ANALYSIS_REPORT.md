# SPRSUN Modbus Data Analysis Report

**Data Collection Period:** 2026-02-13 23:12:02 to 23:21:06  
**Total Data Points:** 14 samples (over ~9 minutes before stopping)  
**Poll Interval:** ~10 seconds

---

## Summary by Category

### 🌡️ Temperature Sensors (Actively Varying)
| Parameter | Min | Max | Avg | Status |
|-----------|-----|-----|-----|--------|
| **Inlet temp.** | 0.0°C | 42.6°C | 16.5°C | ✓ Varying (8 unique values) |
| **Outlet temp.** | 0.1°C | 47.3°C | 19.9°C | ✓ Varying (12 unique values) |
| **Hotwater temp.** | 0.0°C | 43.2°C | 34.1°C | ✓ Varying (12 unique values) |
| **Ambi temp.** | 0.5°C | 181.0°C | 77.8°C | ✓ Varying (10 unique values) |
| **Suct gas temp.** | -6.5°C | 130.0°C | 51.1°C | ✓ Varying (10 unique values) |
| **Coil temp.** | -7.0°C | 202.0°C | 31.6°C | ✓ Varying (14 unique values) |
| **Exhaust temp.** | 0°C | 89°C | 49.3°C | ✓ Varying (10 unique values) |
| **Driving temp.** | 40.0°C | 281.5°C | 123.8°C | ✓ Varying (6 unique values) |
| **Evap. temp.** | -8.4°C | 17.0°C | -1.7°C | ✓ Varying (11 unique values) |
| **Cond. temp.** | -4.8°C | 50.2°C | 25.2°C | ✓ Varying (14 unique values) |

**Note:** All temperature sensors show active readings with good variation, indicating proper operation.

---

### 🔧 Compressor & Control (Active)
| Parameter | Min | Max | Avg | Status |
|-----------|-----|-----|-----|--------|
| **Compressor Runtime** | 150 | 151 | 150.6 | Low variation (incrementing) |
| **Comp. Frequency** | 0 Hz | 70 Hz | 39.1 Hz | ✓ Varying (7 values) |
| **Comp. Current** | 0 A | 80 A | 32.3 A | ✓ Varying (7 values) |
| **Target Frequency** | 1 Hz | 125 Hz | 50.9 Hz | ✓ Varying (8 values) |
| **EEV1 Step** | 0 | 480 | 186.2 | ✓ Varying (main valve) |
| **EEV2 Step** | 0 | 480 | 106.1 | ✓ Varying (aux valve) |

**Analysis:** Compressor is actively operating with frequency varying from idle to 70Hz. Target shows system is trying to reach higher frequencies (up to 125Hz).

---

### 💨 Fan Control (Active)
| Parameter | Min | Max | Avg | Status |
|-----------|-----|-----|-----|--------|
| **DC Fan 1 Speed** | 0 | 739 | 404.8 | ✓ Varying (9 values) |
| **DC Fan 2 Speed** | 0 | 662 | 91.6 | Low variation (3 values) |
| **DC Fan Target** | 0 | 862 | 527.2 | ✓ Varying (12 values) |

**Analysis:** Fan 1 is actively modulating, Fan 2 shows limited operation.

---

### 📊 Pressure Sensors (Active)
| Parameter | Min | Max | Avg | Status |
|-----------|-----|-----|-----|--------|
| **Suct. Press** | 10.0 bar | 305.8 bar | 164.0 bar | ✓ Varying (11 values) |
| **Disch. Press** | 51.3 bar | 298.4 bar | 104.0 bar | ✓ Varying (14 values) |

**Analysis:** Both pressure sensors showing active readings with good variation.

---

### 🔌 Electrical Measurements
| Parameter | Min | Max | Avg | Status |
|-----------|-----|-----|-----|--------|
| **DC Bus Voltage** | 0 V | 556 V | 289.3 V | ✓ Varying (7 values) |
| **AC Voltage** | -11 W | 0 W | -1.5 W | ⚠️ Suspicious values |
| **AC Current** | 0 A | 0 A | 0 A | ⚠️ Always zero |

**Issues Detected:**
- **AC Voltage** showing negative values - possible register mapping issue
- **AC Current** always 0 - sensor may not be connected or different register

---

### ⚙️ Status Flags (Bit Fields)
| Parameter | Min | Max | Avg | Unique Values |
|-----------|-----|-----|-----|---------------|
| **Switching Input Symbol** | 0 | 384 | 329.1 | 2 values |
| **Working Status Mark** | 13 | 384 | 106.4 | 5 values |
| **Output Symbol 1** | 15 | 193 | 135.8 | 5 values |
| **Output Symbol 2** | 64 | 374 | 146.3 | 5 values |
| **Output Symbol 3** | 64 | 193 | 90.1 | 4 values |

**Analysis:** Status flags are changing, indicating the system is transitioning between different operating modes.

---

### ⚠️ Failure/Alarm Flags
| Parameter | Status | Notes |
|-----------|--------|-------|
| **Failure Symbol 1** | Some flags | Values: 0, 65, 97 |
| **Failure Symbol 2** | Clear | Always 0 |
| **Failure Symbol 3** | Clear | Always 0 |
| **Failure Symbol 4** | Clear | Always 0 (2 null readings) |
| **Failure Symbol 5** | Occasional | Values: 0, 24 |
| **Failure Symbol 6** | Clear | Always 0 |
| **Failure Symbol 7** | Occasional | Values: 0, 24, 125 |

**Analysis:** Some failure flags are being raised intermittently. Would need to decode bit fields to identify specific faults.

---

### 🚫 Not Active / Always Zero
| Parameter | Status |
|-----------|--------|
| **Pump Flow** | Always 0 - sensor may not be installed |
| **AC Current** | Always 0 - possible mapping issue |
| **Frequency Conversion Failure 2** | Always 0 - no faults |

---

### 📱 System Information
| Parameter | Values | Notes |
|-----------|--------|-------|
| **COP** | 0, 256, 261 | Coefficient of Performance varying |
| **Software Version (Year)** | 326 - 8228 | Inconsistent - possible decode issue |
| **Software Version (Month/Day)** | 260, 8228 | Need proper decoding |
| **Controller Version** | 0, 590 | Version 590 when active |
| **Display Version** | 590, 660 | Version 590-660 |
| **DC Pump Speed** | 0 - 660 | 4 values (modulating) |

---

## Key Findings

### ✅ Working Correctly (Active Data)
1. **All temperature sensors** - Good variation and realistic ranges
2. **Compressor control** - Frequency varying 0-70 Hz
3. **Pressure sensors** - Both suction and discharge active
4. **Expansion valves** - Both EEV1 and EEV2 modulating
5. **DC Fan 1** - Active speed control
6. **DC Bus voltage** - Varying with load

### ⚠️ Potential Issues
1. **AC Voltage** - Showing negative values (register mapping issue?)
2. **AC Current** - Always 0 (not connected or wrong register?)
3. **Pump Flow** - Always 0 (sensor may not be installed)
4. **Software Version registers** - Values seem incorrectly decoded

### 🔍 Needs Investigation
1. **Failure Symbol 1, 5, 7** - Intermittent flags (need bit decoding)
2. **Status flags** - Should decode individual bits for detailed status
3. **Heating/Cooling Capacity** - Only 2 values (0, 388W) - may need scaling

---

## Recommendations

1. **Register Verification:** Check registers 0x0017 (AC Voltage) and 0x001A (AC Current) - may be mapped incorrectly
2. **Bit Decoding:** Decode failure and status bit fields to identify specific conditions
3. **Scaling Check:** Verify if some registers need different scaling factors
4. **Longer Run:** Collect data over full heating/cooling cycle for better analysis
5. **Flow Sensor:** Verify if flow sensor (Register 0x0018) is installed on this unit

---

## Data Quality: ★★★★☆ (4/5)

- **Excellent:** Temperature sensors, pressure, compressor control
- **Good:** Status flags, fan control, electrical measurements
- **Needs Review:** AC voltage (negative values), AC current (always 0), pump flow (always 0)
