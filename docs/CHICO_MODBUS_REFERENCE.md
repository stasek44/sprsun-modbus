# SPRSUN Heat Pump Modbus Protocol Reference (CHICO)

## Original OEM Document & Hardware Verification Profile

- **Original Protocol Specification:** `RS485-CG248075-MODBUS-V1.2-EN-2022.07.05` (preserved intact in columns 1–5 below)
- **Verified Live Hardware Profile (2026-11-25):**
  - **Model Selection (`F56` / `0x01BA`):** `2` (`A202508`, tested on `CGK-025V3L-B`)
  - **Controller Version (`0x002C`):** `590` | **Display Version (`0x002D`):** `660`
  - **Firmware Date (`0x0013` / `0x0014`):** `8228` (`0x2024`) / `260` (`0x0104`) → `2024-01-04`

## Communication Protocol

**Physical Layer:** RS485 Modbus RTU, `19200 bps`, `8N2` (8 data bits, no parity, 2 stop bits — or `8N1` on some units), half-duplex, Slave `#1`–`#8` (parameter writes restricted to device `#1`).

**Supported Modbus Functions:** `0x03` Read Holding Registers, `0x06` Write Single Register, `0x10` Write Multiple Registers, `0x01` Read Coils, `0x05` Write Single Coil (`[FF][00]` = ON, `[00][00]` = OFF).

## Hardware Verification Highlights vs OEM PDF

1. **Pressure Sensors Swap (`0x002F` / `0x0030`):** OEM PDF swaps Suction vs Discharge labels. Live values (`13.87 bar` vs `4.15 bar`) confirm `0x002F` = Discharge, `0x0030` = Suction (`raw × 0.0069 bar`).
2. **Fan Pressure Diff Units (`D05–D07`, `D11–D13`):** OEM PDF writes `n*10bar` (`20–100 bar`!), whereas live unit holds `23, 4, 3, 9, 4, 2` — raw values are directly in **bar**.
3. **Fan Step Gains (`D16–D20`):** Live values `20, 15, 10, 5, 2` confirm step size is in **rpm**.
4. **Timeband Weekday (`0x01AD–0x01AF`):** OEM PDF says `0~6`, whereas live `timeband_1_weekday = 126` (`0b01111110`) proves this is a **7-bit Mon–Sat bitmask (`0–127`)**.
5. **Observed Parameter Values Outside OEM PDF Min (`0x005C` `A44`, `0x00C9` `F40`):** Live unit holds `A44 = 46 steps` (`raw 23`, PDF min `50`) and `F40 = 0 °C` (PDF min `1`).
6. **OEM Label Typos:** `0x0053–0x005A` all print `A34` in the PDF (logically `A34–A41` heat lower limits, live `46 steps`); `0x00DB` repeats `H04 Defrost ambi stp` (live `10 °C`, upper defrost ambient threshold alongside `H09=-2 °C`, `H12=-10 °C`).
7. **Reserved Gaps Marked `Invalid` in OEM PDF:** `0x006A–0x006F` (`B21–B26` deduced) responded with raw `[0, 0, 2, 2, 0, 0]` (`0,0,4,4,0,0 steps`); `0x0072–0x0077` (`B29–B34` deduced) responded with `[65, 5, 5, 5, 1, 2]` (`130,10,10,10,2,4 steps`). Exposed disabled-by-default via optional batches so unsupported firmware skips cleanly.
8. **Signed `INT16` Registers:** All registers with negative ranges (`0x0011`, `0x0015`, `0x0016`, `0x0022`, `0x0028`, `0x00CD–0x00CF`, `0x00D4`, `0x00D9–0x00E7`, `0x00EC–0x00F5`, `0x0169–0x0174`, `0x0183–0x0184`, `0x0192`, `0x01A3`, `0x01B2–0x01B3`) verified live without unsigned `65xxx` wraparound (e.g. `h03 = -4 °C`, `f41 = -30 °C`, `evap_temp = -4.5 °C`).

## Complete CHICO Register Map (`0x0000–0x01BB`)

| Address | Type | OEM Name (PDF V1.2) | OEM Range / Scale / Raw Note (PDF V1.2) | Observed Live (`Ctrl v590 / Disp v660 / A202508`) | Integration Key |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `0x0000` | `R` | Compressor Runtime | Core CHICO telemetry (not in CG248075 V1.2 table header) | `2138 h` | `compressor_runtime` |
| `0x0001` | `R` | COP | Core CHICO telemetry (not in CG248075 V1.2 table header) | Observed raw `0` (PDF lists `0.01`, varies by firmware) | `cop` |
| `0x0002` | `R` | Switching Input Symbol | Bitfield: bit 0: A/C Linkage switch, bit 1: Linkage switch, bit 2: Heating linkage, bit 3: Cooling linkage, bit 4: Flow Switch, bit 5: High pressure switch, bit 6: Phase sequence detection | Raw `384` | `switching_input_symbol` |
| `0x0003` | `R` | Working Status Mark | Bitfield: bit 0: hotwater demand, bit 1: Heating demand, bit 2: With or without heating, bit 3: With or without cooling, bit 4: Antilegionella on, bit 5: cooling demand, bit 6: Alarm downtime, bit 7: defrost | Raw `14` | `working_status_mark` |
| `0x0004` | `R` | Output Symbol 1 | Bitfield: bit 0: Compressor, bit 5: Fan, bit 6: 4-way valve, bit 7: High or low fan speed:0-low 1-high | Raw `161` | `output_symbol_1` |
| `0x0005` | `R` | Output Symbol 2 | Bitfield: bit 0: Chassis heater, bit 5: Heating heater, bit 6: Three-way valve, bit 7: Hotwater heater | Raw `1` | `output_symbol_2` |
| `0x0006` | `R` | Output Symbol 3 | Bitfield: bit 0: A/C PUMP, bit 1: Crank heater, bit 5: Assistant solenoid valve, bit 6: Pump | Raw `97` | `output_symbol_3` |
| `0x0007` | `R` | Failure Symbol 1 | Bitfield: bit 0: Hotwater temp, bit 1: Ambi temp, bit 2: coil temp, bit 4: Outlet temp, bit 5: High pressure sensor failure, bit 7: Phase sequence | Raw `0` | `failure_symbol_1` |
| `0x0008` | `R` | Failure Symbol 2 | Bitfield: bit 0: Water flow failure, bit 2: High protection of heating water outlet | Raw `0` | `failure_symbol_2` |
| `0x0009` | `R` | Failure Symbol 3 | Bitfield: bit 6: Outlet gas temp. failure | Raw `0` | `failure_symbol_3` |
| `0x000A` | `R` | Failure Symbol 4 | Bitfield: bit 0: Water inlet temp. failure, bit 1: Exhaust temperature is too high, bit 5: Low protection of cooling water outlet, bit 6: Inlet gas temp. failure | Raw `0` | `failure_symbol_4` |
| `0x000B` | `R` | Failure Symbol 5 | Bitfield: bit 0: Low pressure protection, bit 1: High pressure protection, bit 2: Coil temperature is too high, bit 6: High pressure sensor failure, bit 7: Low pressure sensor failure | Raw `0` | `failure_symbol_5` |
| `0x000C` | `R` | Failure Symbol 6 | Bitfield: bit 4: sec antifreeze, bit 5: one antifreeze | Raw `0` | `failure_symbol_6` |
| `0x000D` | `R` | Failure Symbol 7 | Bitfield: bit 1: Ambient temperature is too low, bit 4: frequency conversion module is faulty, bit 5: 2# Dc fan failure, bit 6: 1# Dc fan failure | Raw `0` | `failure_symbol_7` |
| `0x000E` | `R` | Inlet Temp | n*0.1℃ | `29.4 °C` | `inlet_temp` |
| `0x000F` | `R` | Hotwater Temp | n*0.1℃ | `44.7 °C` | `hotwater_temp` |
| `0x0010` | `R` | *Invalid (PDF V1.2)* | Reserved | Ignored in RO batch | — |
| `0x0011` | `R` | Ambi Temp | n*0.5℃ | `1.0 °C` | `ambient_temp` |
| `0x0012` | `R` | Outlet Temp | n*0.1℃ | `31.7 °C` | `outlet_temp` |
| `0x0013` | `R` | Software Version (Year) | Core CHICO telemetry (not in CG248075 V1.2 table header) | Observed `8228` (`0x2024` = year 2024) | `software_version_year` |
| `0x0014` | `R` | Software Version (Month/Day) | Core CHICO telemetry (not in CG248075 V1.2 table header) | Observed `260` (`0x0104` = Jan 04) | `software_version_month_day` |
| `0x0015` | `R` | Suct Gas Temp | n*0.5℃ | `-3.0 °C` | `suction_gas_temp` |
| `0x0016` | `R` | Coil Temp | n*0.5℃ | `-4.0 °C` | `coil_temp` |
| `0x0017` | `R` | AC Voltage | Core CHICO telemetry (not in CG248075 V1.2 table header) | `0 V` | `ac_voltage` |
| `0x0018` | `R` | Pump Flow | Core CHICO telemetry (not in CG248075 V1.2 table header) | `0 m³/h` | `pump_flow` |
| `0x0019` | `R` | Heating/Cooling Capacity | Core CHICO telemetry (not in CG248075 V1.2 table header) | `0 W` | `heating_cooling_capacity` |
| `0x001A` | `R` | AC Current | Core CHICO telemetry (not in CG248075 V1.2 table header) | `0 A` | `ac_current` |
| `0x001B` | `R` | Exhaust Temp | n*1℃ | `62 °C` | `exhaust_temp` |
| `0x001C` | `R` | EEV1 Step | EEV1 step. | `86 steps` | `eev1_step` |
| `0x001D` | `R` | EEV2 Step | EEV2 step. | `0 steps` | `eev2_step` |
| `0x001E` | `R` | Comp Frequency | Comp.frequency | `30 Hz` | `compressor_frequency` |
| `0x001F` | `R` | Frequency Conversion Failure 1 | Frequency conversion failure 1 | `0` | `freq_conversion_failure_1` |
| `0x0020` | `R` | Frequency Conversion Failure 2 | Frequency conversion failure 2 | `0` | `freq_conversion_failure_2` |
| `0x0021` | `R` | DC Bus Voltage | DC bus voltage | `556 V` | `dc_bus_voltage` |
| `0x0022` | `R` | Driving Temp | n*0.5℃ | `40.0 °C` | `driving_temp` |
| `0x0023` | `R` | Comp Current | Comp.current | `5 A` | `compressor_current` |
| `0x0024` | `R` | Target Frequency | Target frequency | `30 Hz` | `target_frequency` |
| `0x0025` | `R` | Smart Grid Status | Core CHICO telemetry (not in CG248075 V1.2 table header) | `0` | `smart_grid_status` |
| `0x0026` | `R` | DC Fan 1 Speed | DC fan 1 speed | `662 rpm` | `dc_fan1_speed` |
| `0x0027` | `R` | DC Fan 2 Speed | DC fan 2 speed | `0 rpm` | `dc_fan2_speed` |
| `0x0028` | `R` | Evap.temp | n*0.1℃ | `-4.5 °C` | `evap_temp` |
| `0x0029` | `R` | Cond.temp | n*0.1℃ | `33.5 °C` | `cond_temp` |
| `0x002A` | `R` | Frequency Conversion Fault 8 | bits higher · If the values are 0xFF, corresponding faults are reported | `0` | `freq_conversion_fault_high` |
| `0x002B` | `R` | Frequency Conversion Failure 8 | bits lower | `0` | `freq_conversion_fault_low` |
| `0x002C` | `R` | Controller Version | Controller Version | Observed `590` (Controller v590) | `controller_version` |
| `0x002D` | `R` | Display Version | Display Version | Observed `660` (Display v660) | `display_version` |
| `0x002E` | `R` | DC Pump Speed | DC pump speed | `80 rpm` | `dc_pump_speed` |
| `0x002F` | `R` | Suct.press | n*0.1bar | Observed `13.869 bar` — **Swapped in OEM PDF**: actually Discharge Pressure (`n × 0.0069 bar`) | `discharge_pressure` |
| `0x0030` | `R` | Disch.press | n*0.1bar | Observed `4.1469 bar` — **Swapped in OEM PDF**: actually Suction Pressure (`n × 0.0069 bar`) | `suction_pressure` |
| `0x0031` | `R` | DC Fan Target | DC fan target | `659 rpm` | `dc_fan_target` |
| `0x0032` | `RW` | Parameter Marker Definition | Bitfield: bit 0: 0-OFF，1-ON, bit 1: MV mode：0-Auto，1- manu, bit 2: Manual frequency selection, bit 5: AV MODE：0-Auto，1- manu, bit 6: AV init outlet stp | Observed raw `65` (`0b01000001`: Power ON, B93 Adjustable ON) | bitfield (`_control_0032`) |
| `0x0033` | `RW` | Control Mark 1 | Bitfield: bit 0: Constant freq adj：0-NO，1-YES, bit 1: Pressure switch enable：1-use，0-Unuse, bit 2: AV cool enable：0-use,1-Unuse, bit 3: AV control mode: 0-Enhance, 1-Exhaust, bit 4: DCfan 1 enable：0-Unuse，1-use, bit 5: DCfan 2 enable：0-Unuse，1-use, bit 6: Parameters reset 0-Unuse ，1-use, bit 7: Failure reset 0-Unuse，1-use | Observed raw `31` (`0b00011111`: R29=1, F01=1, B74=1[unused], B92=1[Exhaust], D01=1) | bitfield (`_control_0033`) |
| `0x0034` | `RW` | Control Mark 2 | Bitfield: bit 0: antilegionella Enable 0-Unuse，1-use, bit 1: Two/Three function 0-Unuse，1-use | Observed raw `2` (`0b00000010`: G01 Two/Three ON; Antilegionella OFF; bits 2-4 unconfirmed `0`) | bitfield (`_control_0034`) |
| `0x0035` | `RW` | Timeband | Bitfield: bit 0: Timeband 1 Enable, bit 1: Timeband 2 Enable, bit 2: Timeband 3 Enable | Observed raw `0` (Timeband 1-3 all disabled) | bitfield (`_control_0035`) |
| `0x0036` | `RW` | P06 Unit Mode | 0 DHW · 1 Heating · 2 Cooling · 3 Heating+DHW · 4 Cooling+DHW | `3` | `unit_mode` |
| `0x0037` | `RW` | H01 Defrost Freq | 30-120HZ | `70 Hz` | `h01_defrost_freq` |
| `0x0038` | `RW` | H08 Defrost Period 1 | 10MIN~120MIN | `45 min` | `h08_defrost_period_1` |
| `0x0039` | `RW` | H11 Defrost Period 2 | 10MIN~120MIN | `45 min` | `h11_defrost_period_2` |
| `0x003A` | `RW` | H14 Defrost Period 3 | 10MIN~120MIN | `45 min` | `h14_defrost_period_3` |
| `0x003B` | `RW` | H15 Comp Total Run | 1-60 · n*5min | `240 min` | `h15_comp_total_run` |
| `0x003C` | `RW` | H16 Comp Continuous Run | 5MIN -90MIN | `10 min` | `h16_comp_continuous_run` |
| `0x003D` | `RW` | H05 Defrost Time | 5-20MIN | `8 min` | `h05_defrost_time` |
| `0x003E` | `RW` | A01 MV Period | 20S~90S | `30 s` | `a01_mv_period` |
| `0x003F` | `RW` | A14 MV Heat Initial 0 | 0~240 · n*2P | `330 steps` | `a14_mv_heat_initial_0` |
| `0x0040` | `RW` | A15 MV Heat Initial 1 | 0~240 · n*2P | `200 steps` | `a15_mv_heat_initial_1` |
| `0x0041` | `RW` | A16 MV Heat Initial 2 | 0~240 · n*2P | `150 steps` | `a16_mv_heat_initial_2` |
| `0x0042` | `RW` | A17 MV Heat Initial 3 | 0~240 · n*2P | `140 steps` | `a17_mv_heat_initial_3` |
| `0x0043` | `RW` | A18 MV Heat Initial 4 | 0~240 · n*2P | `100 steps` | `a18_mv_heat_initial_4` |
| `0x0044` | `RW` | A19 MV Heat Initial 5 | 0~240 · n*2P | `80 steps` | `a19_mv_heat_initial_5` |
| `0x0045` | `RW` | A20 MV Heat Initial 6 | 0~240 · n*2P | `70 steps` | `a20_mv_heat_initial_6` |
| `0x0046` | `RW` | A21 MV Heat Initial 7 | 0~240 · n*2P | `60 steps` | `a21_mv_heat_initial_7` |
| `0x0047` | `RW` | A22 MV Cool Initial 0 | 0~240 · n*2P | `200 steps` | `a22_mv_cool_initial_0` |
| `0x0048` | `RW` | A23 MV Cool Initial 1 | 0~240 · n*2P | `150 steps` | `a23_mv_cool_initial_1` |
| `0x0049` | `RW` | A24 MV Cool Initial 2 | 0~240 · n*2P | `150 steps` | `a24_mv_cool_initial_2` |
| `0x004A` | `RW` | A25 MV Cool Initial 3 | 0~240 · n*2P | `150 steps` | `a25_mv_cool_initial_3` |
| `0x004B` | `RW` | A26 MV Water Init 0 | 0~240 · n*2P | `380 steps` | `a26_mv_water_init_0` |
| `0x004C` | `RW` | A27 MV Water Init 1 | 0~240 · n*2P | `200 steps` | `a27_mv_water_init_1` |
| `0x004D` | `RW` | A28 MV Water Init 2 | 0~240 · n*2P | `150 steps` | `a28_mv_water_init_2` |
| `0x004E` | `RW` | A29 MV Water Init 3 | 0~240 · n*2P | `140 steps` | `a29_mv_water_init_3` |
| `0x004F` | `RW` | A30 MV Water Init 4 | 0~240 · n*2P | `100 steps` | `a30_mv_water_init_4` |
| `0x0050` | `RW` | A31 MV Water Init 5 | 0~240 · n*2P | `80 steps` | `a31_mv_water_init_5` |
| `0x0051` | `RW` | A32 MV Water Init 6 | 0~240 · n*2P | `70 steps` | `a32_mv_water_init_6` |
| `0x0052` | `RW` | A33 MV Water Init 7 | 0~240 · n*2P | `60 steps` | `a33_mv_water_init_7` |
| `0x0053` | `RW` | A34 MV Heat Lower 0 | 0~240 · n*2P | `46 steps` (PDF repeats `A34`; sequential `A34`) | `a34_mv_heat_lower_0` |
| `0x0054` | `RW` | A34 MV Heat Lower 1 | 0~240 · n*2P | `46 steps` (PDF repeats `A34`; sequential `A35`) | `a35_mv_heat_lower_1` |
| `0x0055` | `RW` | A34 MV Heat Lower 2 | 0~240 · n*2P | `46 steps` (PDF repeats `A34`; sequential `A36`) | `a36_mv_heat_lower_2` |
| `0x0056` | `RW` | A34 MV Heat Lower 3 | 0~240 · n*2P | `46 steps` (PDF repeats `A34`; sequential `A37`) | `a37_mv_heat_lower_3` |
| `0x0057` | `RW` | A34 MV Heat Lower 4 | 0~240 · n*2P | `46 steps` (PDF repeats `A34`; sequential `A38`) | `a38_mv_heat_lower_4` |
| `0x0058` | `RW` | A34 MV Heat Lower 5 | 0~240 · n*2P | `46 steps` (PDF repeats `A34`; sequential `A39`) | `a39_mv_heat_lower_5` |
| `0x0059` | `RW` | A34 MV Heat Lower 6 | 0~240 · n*2P | `46 steps` (PDF repeats `A34`; sequential `A40`) | `a40_mv_heat_lower_6` |
| `0x005A` | `RW` | A34 MV Heat Lower 7 | 0~240 · n*2P | `46 steps` (PDF repeats `A34`; sequential `A41`) | `a41_mv_heat_lower_7` |
| `0x005B` | `RW` | A43 MV Defrost Open | 0~240 · n*2P | `480 steps` | `a43_mv_defrost_open` |
| `0x005C` | `RW` | A44 MV Water Lower | 25~75 · n*2P | Observed `46 steps` (raw `23 × 2P`) — lower than PDF min `25` (`50 steps`) | `a44_mv_water_lower` |
| `0x005D` | `RW` | A46 MV Manual Open | 10~225 · n*2P | `40 steps` | `a46_mv_manual_open` |
| `0x005E` | `RW` | A47 MV SH Ratio | 1~6 | `5` | `a47_mv_sh_ratio` |
| `0x005F` | `RW` | A48 MV SH Diff | 1~180 | `1` | `a48_mv_sh_diff` |
| `0x0060` | `RW` | A50 MV Comp.keep Time | 0~250S · n*2S | `60 s` | `a50_mv_comp_keep_time` |
| `0x0061` | `RW` | A51 MV Def.keep Time | 0~250S · n*2S | `60 s` | `a51_mv_def_keep_time` |
| `0x0062` | `RW` | B02 AV Manual Open | 10~225 · n*2P | `350 steps` | `b02_av_manual_open` |
| `0x0063` | `RW` | B04 AV Exhaust Ratio | 1~6 | `5` | `b04_av_exhaust_ratio` |
| `0x0064` | `RW` | B05 AV Exhaust Diff | 0~180 | `1` | `b05_av_exhaust_diff` |
| `0x0065` | `RW` | B06 AV SH Ratio | 1~6 | `4` | `b06_av_sh_ratio` |
| `0x0066` | `RW` | B07 AV SH Diff | 0~180 | `1` | `b07_av_sh_diff` |
| `0x0067` | `RW` | B08 AV Period | 10~20S | `15 s` | `b08_av_period` |
| `0x0068` | `RW` | B19 AV Heat Initial 0 | 0~240 · Outlet temp.≤B93，n*2P | `64 steps` | `b19_av_heat_initial_0` |
| `0x0069` | `RW` | B20 AV Heat Initial 1 | 0~240 · n*2P | `164 steps` | `b20_av_heat_initial_1` |
| `0x006A` | `RW` | *Invalid (PDF V1.2)* — deduced `B21` | Contiguous gap in `B19–B26` table (`n*2P`) | `0 steps` (internal firmware value, disabled by default) | `b21_av_heat_initial_2` |
| `0x006B` | `RW` | *Invalid (PDF V1.2)* — deduced `B22` | Contiguous gap in `B19–B26` table (`n*2P`) | `0 steps` (internal firmware value, disabled by default) | `b22_av_heat_initial_3` |
| `0x006C` | `RW` | *Invalid (PDF V1.2)* — deduced `B23` | Contiguous gap in `B19–B26` table (`n*2P`) | `4 steps` (internal firmware value, disabled by default) | `b23_av_heat_initial_4` |
| `0x006D` | `RW` | *Invalid (PDF V1.2)* — deduced `B24` | Contiguous gap in `B19–B26` table (`n*2P`) | `4 steps` (internal firmware value, disabled by default) | `b24_av_heat_initial_5` |
| `0x006E` | `RW` | *Invalid (PDF V1.2)* — deduced `B25` | Contiguous gap in `B19–B26` table (`n*2P`) | `0 steps` (internal firmware value, disabled by default) | `b25_av_heat_initial_6` |
| `0x006F` | `RW` | *Invalid (PDF V1.2)* — deduced `B26` | Contiguous gap in `B19–B26` table (`n*2P`) | `0 steps` (internal firmware value, disabled by default) | `b26_av_heat_initial_7` |
| `0x0070` | `RW` | B27 AV Water Initial 0 | 0~240 · Outlet temp.≤B93，n*2P | `64 steps` | `b27_av_water_initial_0` |
| `0x0071` | `RW` | B28 AV Water Initial 1 | 0~240 · n*2P | `164 steps` | `b28_av_water_initial_1` |
| `0x0072` | `RW` | *Invalid (PDF V1.2)* — deduced `B29` | Contiguous gap in `B27–B34` table (`n*2P`) | `130 steps` (internal firmware value, disabled by default) | `b29_av_water_initial_2` |
| `0x0073` | `RW` | *Invalid (PDF V1.2)* — deduced `B30` | Contiguous gap in `B27–B34` table (`n*2P`) | `10 steps` (internal firmware value, disabled by default) | `b30_av_water_initial_3` |
| `0x0074` | `RW` | *Invalid (PDF V1.2)* — deduced `B31` | Contiguous gap in `B27–B34` table (`n*2P`) | `10 steps` (internal firmware value, disabled by default) | `b31_av_water_initial_4` |
| `0x0075` | `RW` | *Invalid (PDF V1.2)* — deduced `B32` | Contiguous gap in `B27–B34` table (`n*2P`) | `10 steps` (internal firmware value, disabled by default) | `b32_av_water_initial_5` |
| `0x0076` | `RW` | *Invalid (PDF V1.2)* — deduced `B33` | Contiguous gap in `B27–B34` table (`n*2P`) | `2 steps` (internal firmware value, disabled by default) | `b33_av_water_initial_6` |
| `0x0077` | `RW` | *Invalid (PDF V1.2)* — deduced `B34` | Contiguous gap in `B27–B34` table (`n*2P`) | `4 steps` (internal firmware value, disabled by default) | `b34_av_water_initial_7` |
| `0x0078` | `RW` | B35 AV Heat Lower 0 | 0~240 · n*2P | `20 steps` | `b35_av_heat_lower_0` |
| `0x0079` | `RW` | B36 AV Heat Lower 1 | 0~240 · n*2P | `20 steps` | `b36_av_heat_lower_1` |
| `0x007A` | `RW` | B37 AV Heat Lower 2 | 0~240 · n*2P | `20 steps` | `b37_av_heat_lower_2` |
| `0x007B` | `RW` | B38 AV Heat Lower 3 | 0~240 · n*2P | `20 steps` | `b38_av_heat_lower_3` |
| `0x007C` | `RW` | B39 AV Heat Lower 4 | 0~240 · n*2P | `20 steps` | `b39_av_heat_lower_4` |
| `0x007D` | `RW` | B40 AV Heat Lower 5 | 0~240 · n*2P | `20 steps` | `b40_av_heat_lower_5` |
| `0x007E` | `RW` | B41 AV Heat Lower 6 | 0~240 · n*2P | `20 steps` | `b41_av_heat_lower_6` |
| `0x007F` | `RW` | B42 AV Heat Lower 7 | 0~240 · n*2P | `20 steps` | `b42_av_heat_lower_7` |
| `0x0080` | `RW` | B43 AV Defrost Open | 0~240 · n*2P | `0 steps` | `b43_av_defrost_open` |
| `0x0081` | `RW` | B44 AV Cool Open | 0~240 · n*2P | `0 steps` | `b44_av_cool_open` |
| `0x0082` | `RW` | F02 HP Protect Value | 0-250 · (n+250)*0.1bar | `42.0 bar` | `f02_hp_protect_value` |
| `0x0083` | `RW` | F03 HP Recover Value | 0-250 · (n+250)*0.1bar | `36.0 bar` | `f03_hp_recover_value` |
| `0x0084` | `RW` | F04 LP Protect Value | 0-200 · n*0.1bar | `0.8 bar` | `f04_lp_protect_value` |
| `0x0085` | `RW` | F05 LP Recover Value | 0-200 · n*0.1bar | `1.5 bar` | `f05_lp_recover_value` |
| `0x0086` | `RW` | D03 Cool Dcfan Max Speed | 0~100 · n*10rpm | `750 rpm` | `d03_cool_dcfan_max_speed` |
| `0x0087` | `RW` | D04 Cool Dcfan Min Speed | 0~100 · n*10rpm | `200 rpm` | `d04_cool_dcfan_min_speed` |
| `0x0088` | `RW` | D05 Cool Dcfan High Press | 10-40 | Observed `23` — raw **bar** (`23 bar`), PDF unit column omitted | `d05_cool_dcfan_high_press` |
| `0x0089` | `RW` | D06 Cool Dcfan Open Diff | 2-10 · n*10bar | Observed `4` — raw **bar** (PDF `n*10bar` is a typo) | `d06_cool_dcfan_open_diff` |
| `0x008A` | `RW` | D07 Cool Dcfan Close Diff | 2-10 · n*10bar | Observed `3` — raw **bar** (PDF `n*10bar` is a typo) | `d07_cool_dcfan_close_diff` |
| `0x008B` | `RW` | D08 Cool Dcfan Init Speed | 0~100 · n*10rpm | `700 rpm` | `d08_cool_dcfan_init_speed` |
| `0x008C` | `RW` | D09 Heat Dcfan Max Speed | 0~100 · n*10rpm | `750 rpm` | `d09_heat_dcfan_max_speed` |
| `0x008D` | `RW` | D10 Heat Dcfan Min Speed | 0~100 · n*10rpm | `200 rpm` | `d10_heat_dcfan_min_speed` |
| `0x008E` | `RW` | D11 Heat Dcfan Low Press | 5-15 · n*10bar | Observed `9` — raw **bar** (PDF `n*10bar` is a typo) | `d11_heat_dcfan_low_press` |
| `0x008F` | `RW` | D12 Heat Dcfan Open Diff | 2-10 · n*10bar | Observed `4` — raw **bar** (PDF `n*10bar` is a typo) | `d12_heat_dcfan_open_diff` |
| `0x0090` | `RW` | D13 Heat Dcfan Close Diff | 2-10 · n*10bar | Observed `2` — raw **bar** (PDF `n*10bar` is a typo) | `d13_heat_dcfan_close_diff` |
| `0x0091` | `RW` | D14 Heat DCfan Init Speed | 0~100 · n*10rpm | `700 rpm` | `d14_heat_dcfan_init_speed` |
| `0x0092` | `RW` | D15 DCfan Adjust Period | 0-30 | `5 s` | `d15_dcfan_adjust_period` |
| `0x0093` | `RW` | D16 DCfan Adjust Speed 1 | 0~100 · Speed difference≥200 | `20 rpm` | `d16_dcfan_adjust_speed_1` |
| `0x0094` | `RW` | D17 DCfan Adjust Speed 2 | 0~100 · 200＞Speed difference≥100 | `15 rpm` | `d17_dcfan_adjust_speed_2` |
| `0x0095` | `RW` | D18 DCfan Adjust Speed 3 | 0~100 · 100＞Speed difference≥50 | `10 rpm` | `d18_dcfan_adjust_speed_3` |
| `0x0096` | `RW` | D19 DCfan Adjust Speed 4 | 0~100 · 50＞Speed difference≥20 | `5 rpm` | `d19_dcfan_adjust_speed_4` |
| `0x0097` | `RW` | D20 DCfan Adjust Speed 5 | 0~100 · 20＞Speed difference≥5 | `2 rpm` | `d20_dcfan_adjust_speed_5` |
| `0x0098` | `RW` | B45 AV Water Lower 0 | 0~240 · n*2P | `20 steps` | `b45_av_water_lower_0` |
| `0x0099` | `RW` | B46 AV Water Lower 1 | 0~240 · n*2P | `20 steps` | `b46_av_water_lower_1` |
| `0x009A` | `RW` | B47 AV Water Lower 2 | 0~240 · n*2P | `20 steps` | `b47_av_water_lower_2` |
| `0x009B` | `RW` | B48 AV Water Lower 3 | 0~240 · n*2P | `20 steps` | `b48_av_water_lower_3` |
| `0x009C` | `RW` | B49 AV Water Lower 4 | 0~240 · n*2P | `20 steps` | `b49_av_water_lower_4` |
| `0x009D` | `RW` | B50 AV Water Lower 5 | 0~240 · n*2P | `20 steps` | `b50_av_water_lower_5` |
| `0x009E` | `RW` | B51 AV Water Lower 6 | 0~240 · n*2P | `20 steps` | `b51_av_water_lower_6` |
| `0x009F` | `RW` | B52 AV Water Lower 7 | 0~240 · n*2P | `20 steps` | `b52_av_water_lower_7` |
| `0x00A0` | `RW` | B53 AV Heat Exhaust 0 | 50~125℃ · T≥14℃ | `60 °C` | `b53_av_heat_exhaust_0` |
| `0x00A1` | `RW` | B54 AV Heat Exhaust 1 | 50~125℃ · [9，14) | `60 °C` | `b54_av_heat_exhaust_1` |
| `0x00A2` | `RW` | B55 AV Heat Exhaust 2 | 50~125℃ · [4，9) | `60 °C` | `b55_av_heat_exhaust_2` |
| `0x00A3` | `RW` | B56 AV Heat Exhaust 3 | 50~125℃ · [-5，4) | `60 °C` | `b56_av_heat_exhaust_3` |
| `0x00A4` | `RW` | B57 AV Heat Exhaust 4 | 50~125℃ · [-10，-5) | `60 °C` | `b57_av_heat_exhaust_4` |
| `0x00A5` | `RW` | B58 AV Heat Exhaust 5 | 50~125℃ · [-16，-10) | `60 °C` | `b58_av_heat_exhaust_5` |
| `0x00A6` | `RW` | B59 AV Heat Exhaust 6 | 50~125℃ · [-23，-16) | `60 °C` | `b59_av_heat_exhaust_6` |
| `0x00A7` | `RW` | B60 AV Heat Exhaust 7 | 50~125℃ · T＜-23℃ | `60 °C` | `b60_av_heat_exhaust_7` |
| `0x00A8` | `RW` | B61 AV Water Exh0 | 50~125℃ · T≥14℃ | `60 °C` | `b61_av_water_exhaust_0` |
| `0x00A9` | `RW` | B62 AV Water Exh1 | 50~125℃ · [9，14) | `60 °C` | `b62_av_water_exhaust_1` |
| `0x00AA` | `RW` | B63 AV Water Exh2 | 50~125℃ · [4，9) | `60 °C` | `b63_av_water_exhaust_2` |
| `0x00AB` | `RW` | B64 AV Water Exh3 | 50~125℃ · [-5，4) | `60 °C` | `b64_av_water_exhaust_3` |
| `0x00AC` | `RW` | B65 AV Water Exh4 | 50~125℃ · [-10，-5) | `60 °C` | `b65_av_water_exhaust_4` |
| `0x00AD` | `RW` | B66 AV Water Exh5 | 50~125℃ · [-16，-10) | `60 °C` | `b66_av_water_exhaust_5` |
| `0x00AE` | `RW` | B67 AV Water Exh6 | 50~125℃ · [-23，-16) | `60 °C` | `b67_av_water_exhaust_6` |
| `0x00AF` | `RW` | B68 AV Water Exh7 | 50~125℃ · T＜-23℃ | `60 °C` | `b68_av_water_exhaust_7` |
| `0x00B0` | `RW` | B69 AV Cool Exhaust 0 | 50~125℃ · T≥38℃ | `60 °C` | `b69_av_cool_exhaust_0` |
| `0x00B1` | `RW` | B70 AV Cool Exhaust 1 | 50~125℃ · [30，38) | `60 °C` | `b70_av_cool_exhaust_1` |
| `0x00B2` | `RW` | B71 AV Cool Exhaust 2 | 50~125℃ · [25，30) | `60 °C` | `b71_av_cool_exhaust_2` |
| `0x00B3` | `RW` | B72 AV Cool Exhaust 3 | 50~125℃ · T＜25℃ | `60 °C` | `b72_av_cool_exhaust_3` |
| `0x00B4` | `RW` | B73 AV Open Delay | 0~180S | `10 s` | `b73_av_open_delay` |
| `0x00B5` | `RW` | B75 AV Off Exh Diff | 0~30 | `5 °C` | `b75_av_off_exh_diff` |
| `0x00B6` | `RW` | B76 AV Heat Exh Diff 0 | 0~125℃ · T≥14℃ | `40 °C` | `b76_av_heat_exh_diff_0` |
| `0x00B7` | `RW` | B77 AV Heat Exh Diff 1 | 0~125℃ · [9，14) | `35 °C` | `b77_av_heat_exh_diff_1` |
| `0x00B8` | `RW` | B78 AV Heat Exh Diff 2 | 0~125℃ · [4，9) | `35 °C` | `b78_av_heat_exh_diff_2` |
| `0x00B9` | `RW` | B79 AV Heat Exh Diff 3 | 0~125℃ · [-5，4) | `38 °C` | `b79_av_heat_exh_diff_3` |
| `0x00BA` | `RW` | B80 AV Heat Exh Diff 4 | 0~125℃ · [-10，-5) | `40 °C` | `b80_av_heat_exh_diff_4` |
| `0x00BB` | `RW` | B81 AV Heat Exh Diff 5 | 0~125℃ · [-16，-10) | `40 °C` | `b81_av_heat_exh_diff_5` |
| `0x00BC` | `RW` | B82 AV Heat Exh Diff 6 | 0~125℃ · [-23，-16) | `40 °C` | `b82_av_heat_exh_diff_6` |
| `0x00BD` | `RW` | B83 AV Heat Exh Diff 7 | 0~125℃ · T＜-23℃ | `35 °C` | `b83_av_heat_exh_diff_7` |
| `0x00BE` | `RW` | B84 AV Water Exh Diff 0 | 0~125℃ · T≥14℃ | `40 °C` | `b84_av_water_exh_diff_0` |
| `0x00BF` | `RW` | B85 AV Water Exh Diff 1 | 0~125℃ · [9，14) | `35 °C` | `b85_av_water_exh_diff_1` |
| `0x00C0` | `RW` | B86 AV Water Exh Diff 2 | 0~125℃ · [4，9) | `35 °C` | `b86_av_water_exh_diff_2` |
| `0x00C1` | `RW` | B87 AV Water Exh Diff 3 | 0~125℃ · [-5，4) | `38 °C` | `b87_av_water_exh_diff_3` |
| `0x00C2` | `RW` | B88 AV Water Exh Diff 4 | 0~125℃ · [-10，-5) | `40 °C` | `b88_av_water_exh_diff_4` |
| `0x00C3` | `RW` | B89 AV Water Exh Diff 5 | 0~125℃ · [-16，-10) | `40 °C` | `b89_av_water_exh_diff_5` |
| `0x00C4` | `RW` | B90 AV Water Exh Diff 6 | 0~125℃ · [-23，-16) | `40 °C` | `b90_av_water_exh_diff_6` |
| `0x00C5` | `RW` | B91 AV Water Exh Diff 7 | 0~125℃ · T＜-23℃ | `35 °C` | `b91_av_water_exh_diff_7` |
| `0x00C6` | `RW` | P03 Temp.diff | 2℃~18℃ | `2 °C` | `temp_diff_heating_cooling` |
| `0x00C7` | `RW` | F39 AC Constant Temp Diff | 1~10℃ | `2 °C` | `f39_ac_constant_temp_diff` |
| `0x00C8` | `RW` | P05 Temp.diff | 2℃~18℃ | `5 °C` | `temp_diff_hotwater` |
| `0x00C9` | `RW` | F40 WT Constant Temp Diff | 1~10℃ | Observed `0 °C` — lower than PDF min `1 °C` | `f40_wt_constant_temp_diff` |
| `0x00CA` | `RW` | P04 Hotwater Setp | 10~55 · n*0.5℃ · （Read only lower 8 bits） | `48.0 °C` | `hotwater_setpoint` |
| `0x00CB` | `RW` | P02 Cooling Setp | 12~30 · n*0.5℃（Read only lower 8 bits） | `18.0 °C` | `cooling_setpoint` |
| `0x00CC` | `RW` | P01 Heating Setp | 10~55 · n*0.5℃（Read only lower 8 bits） | `28.0 °C` | `heating_setpoint` |
| `0x00CD` | `RW` | F44 WT Temp Calibration | -30~30 | `2 °C` | `f44_wt_temp_calibration` |
| `0x00CE` | `RW` | F45 Inlet Temp Calibration | -30~30 | `0 °C` | `f45_inlet_temp_calibration` |
| `0x00CF` | `RW` | F46 Outlet Temp Calibration | -30~30 | `0 °C` | `f46_outlet_temp_calibration` |
| `0x00D0` | `RW` | F49 WT Temp Offset Stp | 30~55 | `48 °C` | `f49_wt_temp_offset_stp` |
| `0x00D1` | `RW` | F50 Inlet Temp Offset Stp | 30~55 | `48 °C` | `f50_inlet_temp_offset_stp` |
| `0x00D2` | `RW` | F42 Water Temp Offset | 0~50 | `7 °C` | `f42_water_temp_offset` |
| `0x00D3` | `RW` | F43 Inlet Temp Offset | 0~50 | `5 °C` | `f43_inlet_temp_offset` |
| `0x00D4` | `RW` | H03 Defrost In Stp | -15℃~-1℃ | `-4 °C` | `h03_defrost_in_stp` |
| `0x00D5` | `RW` | H04 Defrost Exit Stp | 1℃~40℃ | `15 °C` | `h04_defrost_exit_stp` |
| `0x00D6` | `RW` | H07 Def Ambi Coil 1 | 0℃~30℃ | `10 °C` | `h07_defrost_ambi_coil_1` |
| `0x00D7` | `RW` | H10 Def Ambi Coil 2 | 0℃~30℃ | `9 °C` | `h10_defrost_ambi_coil_2` |
| `0x00D8` | `RW` | H13 Def Ambi Coil 3 | 0℃~30℃ | `8 °C` | `h13_defrost_ambi_coil_3` |
| `0x00D9` | `RW` | H09 Defrost Ambi Stp.1 | -30℃~30℃ | `-2 °C` | `h09_defrost_ambi_stp_1` |
| `0x00DA` | `RW` | H12 Defrost Ambi Stp.2 | -30℃~30℃ | `-10 °C` | `h12_defrost_ambi_stp_2` |
| `0x00DB` | `RW` | H04 Defrost Ambi Stp | -30℃~30℃ | Observed `10 °C` — **PDF label typo** repeats `H04`; acts as upper defrost ambient setpoint | `defrost_ambi_stp_00db` |
| `0x00DC` | `RW` | A02 MV Heating SH 1 | -5℃~10℃ · T≥14℃ | `4 °C` | `a02_mv_heating_sh_1` |
| `0x00DD` | `RW` | A03 MV Heating SH 2 | -5℃~10℃ · [9，14) | `4 °C` | `a03_mv_heating_sh_2` |
| `0x00DE` | `RW` | A04 MV Heating SH 3 | -5℃~10℃ · [4，9) | `4 °C` | `a04_mv_heating_sh_3` |
| `0x00DF` | `RW` | A05 MV Heating SH 4 | -5℃~10℃ · [-5，4) | `4 °C` | `a05_mv_heating_sh_4` |
| `0x00E0` | `RW` | A06 MV Heating SH 5 | -5℃~10℃ · [-10，-5) | `4 °C` | `a06_mv_heating_sh_5` |
| `0x00E1` | `RW` | A07 MV Heating SH 6 | -5℃~10℃ · [-16，-10) | `4 °C` | `a07_mv_heating_sh_6` |
| `0x00E2` | `RW` | A08 MV Heating SH 7 | -5℃~10℃ · [-23，-16) | `4 °C` | `a08_mv_heating_sh_7` |
| `0x00E3` | `RW` | A09 MV Heating SH 8 | -5℃~10℃ · T＜-23℃ | `5 °C` | `a09_mv_heating_sh_8` |
| `0x00E4` | `RW` | A10 MV Cooling SH 1 | -5℃~10℃ · T≥38℃ | `5 °C` | `a10_mv_cooling_sh_1` |
| `0x00E5` | `RW` | A11 MV Cooling SH 2 | -5℃~10℃ · [30，38) | `5 °C` | `a11_mv_cooling_sh_2` |
| `0x00E6` | `RW` | A12 MV Cooling SH 3 | -5℃~10℃ · [25，30) | `5 °C` | `a12_mv_cooling_sh_3` |
| `0x00E7` | `RW` | A13 MV Cooling SH 4 | -5℃~10℃ · T＜25℃ | `5 °C` | `a13_mv_cooling_sh_4` |
| `0x00E8` | `RW` | A42 MV Exhaust Stp | 70℃~125℃ | `120 °C` | `a42_mv_exhaust_stp` |
| `0x00E9` | `RW` | B03 AV Start Ambi | 11℃~45℃ | `45 °C` | `b03_av_start_ambi` |
| `0x00EA` | `RW` | B09 AV Exhaust Stp | 70~120 | `120 °C` | `b09_av_exhaust_stp` |
| `0x00EB` | `RW` | B10 AV Off Exh Stp | 40~70 | `65 °C` | `b10_av_off_exh_stp` |
| `0x00EC` | `RW` | B11 AV Heating SH 1 | -10~10 · T≥14℃ | `4 °C` | `b11_av_heating_sh_1` |
| `0x00ED` | `RW` | B12 AV Heating SH 2 | -10~10 · [9，14) | `4 °C` | `b12_av_heating_sh_2` |
| `0x00EE` | `RW` | B13 AV Heating SH 3 | -10~10 · [4，9) | `4 °C` | `b13_av_heating_sh_3` |
| `0x00EF` | `RW` | B14 AV Heating SH 4 | -10~10 · [-5，4) | `4 °C` | `b14_av_heating_sh_4` |
| `0x00F0` | `RW` | B15 AV Heating SH 5 | -10~10 · [-10，-5) | `4 °C` | `b15_av_heating_sh_5` |
| `0x00F1` | `RW` | B16 AV Heating SH 6 | -10~10 · [-16，-10) | `4 °C` | `b16_av_heating_sh_6` |
| `0x00F2` | `RW` | B17 AV Heating SH 7 | -10~10 · [-23，-16) | `4 °C` | `b17_av_heating_sh_7` |
| `0x00F3` | `RW` | B18 AV Heating SH 8 | -10~10 · T＜-23℃ | `4 °C` | `b18_av_heating_sh_8` |
| `0x00F4` | `RW` | D21 AC Fan Switch Ambi.1 | -10~50℃ | `28 °C` | `d21_ac_fan_switch_ambi_1` |
| `0x00F5` | `RW` | D22 AC Fan Switch Ambi.2 | -10~50℃ | `26 °C` | `d22_ac_fan_switch_ambi_2` |
| `0x00F6` | `RW` | R16 Exhaust High TP0 | 50~125℃ | `105 °C` | `r16_exhaust_high_tp0` |
| `0x00F7` | `RW` | R17 Exhaust High TP1 | 50~125℃ | `107 °C` | `r17_exhaust_high_tp1` |
| `0x00F8` | `RW` | R18 Exhaust High TP2 | 50~125℃ | `109 °C` | `r18_exhaust_high_tp2` |
| `0x00F9` | `RW` | R19 Exhaust High TP3 | 50~125℃ | `112 °C` | `r19_exhaust_high_tp3` |
| `0x00FA` | `RW` | R20 Exhaust High TP4 | 50~125℃ | `115 °C` | `r20_exhaust_high_tp4` |
| `0x00FB` | `RW` | Manual Frequency Setting | Manual frequency setting | `50 Hz` | `manual_frequency_setting` |
| `0x00FC` | `RW` | Freq Of Water ROO | 30~120Hz · T≥14℃ | `30 Hz` | `r00_water_freq_0` |
| `0x00FD` | `RW` | Freq Of Water RO1 | 30~120Hz · [9，14) | `70 Hz` | `r01_water_freq_1` |
| `0x00FE` | `RW` | Freq Of Water RO2 | 30~120Hz · [4，9) | `70 Hz` | `r02_water_freq_2` |
| `0x00FF` | `RW` | Freq Of Water RO3 | 30~120Hz · [-5，4) | `70 Hz` | `r03_water_freq_3` |
| `0x0100` | `RW` | Freq Of Water R30 | 30~120Hz · [-10，-5) | `70 Hz` | `r30_water_freq_4` |
| `0x0101` | `RW` | Freq Of Water R31 | 30~120Hz · [-16，-10) | `70 Hz` | `r31_water_freq_5` |
| `0x0102` | `RW` | Freq Of Water R32 | 30~120Hz · [-23，-16) | `70 Hz` | `r32_water_freq_6` |
| `0x0103` | `RW` | Freq Of Water R33 | 30~120Hz · T＜-23℃ | `70 Hz` | `r33_water_freq_7` |
| `0x0104` | `RW` | Freq Of Heat RO4 | 30~120Hz · T≥14℃ | `33 Hz` | `r04_heat_freq_0` |
| `0x0105` | `RW` | Freq Of Heat RO5 | 30~120Hz · [9，14) | `36 Hz` | `r05_heat_freq_1` |
| `0x0106` | `RW` | Freq Of Heat RO6 | 30~120Hz · [4，9) | `45 Hz` | `r06_heat_freq_2` |
| `0x0107` | `RW` | Freq Of Heat RO7 | 30~120Hz · [-5，4) | `50 Hz` | `r07_heat_freq_3` |
| `0x0108` | `RW` | Freq Of Heat RO8 | 30~120Hz · [-10，-5) | `55 Hz` | `r08_heat_freq_4` |
| `0x0109` | `RW` | Freq Of Heat RO9 | 30~120Hz · [-16，-10) | `60 Hz` | `r09_heat_freq_5` |
| `0x010A` | `RW` | Freq Of Heat R10 | 30~120Hz · [-23，-16) | `65 Hz` | `r10_heat_freq_6` |
| `0x010B` | `RW` | Freq Of Heat R11 | 30~120Hz · T＜-23℃ | `70 Hz` | `r11_heat_freq_7` |
| `0x010C` | `RW` | Freq Of Cool R12 | 30~120Hz · T≥38℃ | `60 Hz` | `r12_cool_freq_0` |
| `0x010D` | `RW` | Freq Of Cool R13 | 30~120Hz · [30，38) | `70 Hz` | `r13_cool_freq_1` |
| `0x010E` | `RW` | Freq Of Cool R14 | 30~120Hz · [25，30) | `70 Hz` | `r14_cool_freq_2` |
| `0x010F` | `RW` | Freq Of Cool R15 | 30~120Hz · T＜25℃ | `65 Hz` | `r15_cool_freq_3` |
| `0x0110` | `RW` | Freq Adj Lower Limit R21 | 0~125Hz | `125 Hz` | `r21_freq_adj_lower_limit` |
| `0x0111` | `RW` | Freq Adj Lower Limit R22 | 0~125Hz | `125 Hz` | `r22_freq_adj_lower_limit` |
| `0x0112` | `RW` | Freq Adj Lower Limit R23 | 0~125Hz | `125 Hz` | `r23_freq_adj_lower_limit` |
| `0x0113` | `RW` | Freq Adj Lower Limit R24 | 0~125Hz | `125 Hz` | `r24_freq_adj_lower_limit` |
| `0x0114` | `RW` | Freq Adj Lower Upper R25 | 0~125Hz | `125 Hz` | `r25_freq_adj_upper_limit` |
| `0x0115` | `RW` | Freq Adj Lower Upper R26 | 0~125Hz | `125 Hz` | `r26_freq_adj_upper_limit` |
| `0x0116` | `RW` | Freq Adj Lower Upper R27 | 0~125Hz | `125 Hz` | `r27_freq_adj_upper_limit` |
| `0x0117` | `RW` | Freq Adj Lower Upper R28 | 0~125Hz | `125 Hz` | `r28_freq_adj_upper_limit` |
| `0x0118` | `RW` | *Invalid (PDF V1.2)* | Reserved gap | Not polled (skipped in batch split) | — |
| `0x0119` | `RW` | Timeband 1 ON Hour | 0-23 | `0 h` | `timeband_1_on_hour` |
| `0x011A` | `RW` | Timeband 1 ON Minutes | 0-59 | `0 min` | `timeband_1_on_minute` |
| `0x011B` | `RW` | Timeband 1 OFF Hour | 0-23 | `16 h` | `timeband_1_off_hour` |
| `0x011C` | `RW` | Timeband 1 OFF Minutes | 0-59 | `0 min` | `timeband_1_off_minute` |
| `0x011D` | `RW` | Timeband 2 ON Hour | 0-23 | `14 h` | `timeband_2_on_hour` |
| `0x011E` | `RW` | Timeband 2 ON Minutes | 0-59 | `0 min` | `timeband_2_on_minute` |
| `0x011F` | `RW` | Timeband 2 OFF Hour | 0-23 | `17 h` | `timeband_2_off_hour` |
| `0x0120` | `RW` | Timeband 2 OFF Minutes | 0-59 | `0 min` | `timeband_2_off_minute` |
| `0x0121` | `RW` | Timeband 3 ON Hour | 0-23 | `19 h` | `timeband_3_on_hour` |
| `0x0122` | `RW` | Timeband 3 ON Minutes | 0-59 | `0 min` | `timeband_3_on_minute` |
| `0x0123` | `RW` | Timeband 3 OFF Hour | 0-23 | `23 h` | `timeband_3_off_hour` |
| `0x0124` | `RW` | Timeband 3 OFF Minutes | 0-59 | `0 min` | `timeband_3_off_minute` |
| `0x0125` | `RW` | *Invalid (PDF V1.2)* | Reserved gap | Not polled (skipped in batch split) | — |
| `0x0126` | `RW` | *Invalid (PDF V1.2)* | Reserved gap | Not polled (skipped in batch split) | — |
| `0x0127` | `RW` | *Invalid (PDF V1.2)* | Reserved gap | Not polled (skipped in batch split) | — |
| `0x0128` | `RW` | *Invalid (PDF V1.2)* | Reserved gap | Not polled (skipped in batch split) | — |
| `0x0129` | `RW` | *Invalid (PDF V1.2)* | Reserved gap | Not polled (skipped in batch split) | — |
| `0x012A` | `RW` | *Invalid (PDF V1.2)* | Reserved gap | Not polled (skipped in batch split) | — |
| `0x012B` | `RW` | *Invalid (PDF V1.2)* | Reserved gap | Not polled (skipped in batch split) | — |
| `0x012C` | `RW` | *Invalid (PDF V1.2)* | Reserved gap | Not polled (skipped in batch split) | — |
| `0x012D` | `RW` | ECO Freq Of Water R34 | 30~120Hz | `50 Hz` | `r34_eco_water_freq_0` |
| `0x012E` | `RW` | ECO Freq Of Water R35 | 30~120Hz | `50 Hz` | `r35_eco_water_freq_1` |
| `0x012F` | `RW` | ECO Freq Of Water R36 | 30~120Hz | `55 Hz` | `r36_eco_water_freq_2` |
| `0x0130` | `RW` | ECO Freq Of Water R37 | 30~120Hz | `60 Hz` | `r37_eco_water_freq_3` |
| `0x0131` | `RW` | ECO Freq Of Water R38 | 30~120Hz | `65 Hz` | `r38_eco_water_freq_4` |
| `0x0132` | `RW` | ECO Freq Of Water R39 | 30~120Hz | `70 Hz` | `r39_eco_water_freq_5` |
| `0x0133` | `RW` | ECO Freq Of Water R40 | 30~120Hz | `70 Hz` | `r40_eco_water_freq_6` |
| `0x0134` | `RW` | ECO Freq Of Water R41 | 30~120Hz | `70 Hz` | `r41_eco_water_freq_7` |
| `0x0135` | `RW` | ECO Freq Of Heat R42 | 30~120Hz | `50 Hz` | `r42_eco_heat_freq_0` |
| `0x0136` | `RW` | ECO Freq Of Heat R43 | 30~120Hz | `50 Hz` | `r43_eco_heat_freq_1` |
| `0x0137` | `RW` | ECO Freq Of Heat R44 | 30~120Hz | `55 Hz` | `r44_eco_heat_freq_2` |
| `0x0138` | `RW` | ECO Freq Of Heat R45 | 30~120Hz | `60 Hz` | `r45_eco_heat_freq_3` |
| `0x0139` | `RW` | ECO Freq Of Heat R46 | 30~120Hz | `65 Hz` | `r46_eco_heat_freq_4` |
| `0x013A` | `RW` | ECO Freq Of Heat R47 | 30~120Hz | `70 Hz` | `r47_eco_heat_freq_5` |
| `0x013B` | `RW` | ECO Freq Of Heat R48 | 30~120Hz | `70 Hz` | `r48_eco_heat_freq_6` |
| `0x013C` | `RW` | ECO Freq Of Heat R49 | 30~120Hz | `70 Hz` | `r49_eco_heat_freq_7` |
| `0x013D` | `RW` | ECO Freq Of Cool R50 | 30~120Hz | `65 Hz` | `r50_eco_cool_freq_0` |
| `0x013E` | `RW` | ECO Freq Of Cool R51 | 30~120Hz | `65 Hz` | `r51_eco_cool_freq_1` |
| `0x013F` | `RW` | ECO Freq Of Cool R52 | 30~120Hz | `60 Hz` | `r52_eco_cool_freq_2` |
| `0x0140` | `RW` | ECO Freq Of Cool R53 | 30~120Hz | `55 Hz` | `r53_eco_cool_freq_3` |
| `0x0141` | `RW` | Night Freq Of Water R54 | 30~120Hz | `60 Hz` | `r54_night_water_freq_0` |
| `0x0142` | `RW` | Night Freq Of Water R55 | 30~120Hz | `60 Hz` | `r55_night_water_freq_1` |
| `0x0143` | `RW` | Night Freq Of Water R56 | 30~120Hz | `60 Hz` | `r56_night_water_freq_2` |
| `0x0144` | `RW` | Night Freq Of Water R57 | 30~120Hz | `60 Hz` | `r57_night_water_freq_3` |
| `0x0145` | `RW` | Night Freq Of Water R58 | 30~120Hz | `60 Hz` | `r58_night_water_freq_4` |
| `0x0146` | `RW` | Night Freq Of Water R59 | 30~120Hz | `60 Hz` | `r59_night_water_freq_5` |
| `0x0147` | `RW` | Night Freq Of Water R60 | 30~120Hz | `60 Hz` | `r60_night_water_freq_6` |
| `0x0148` | `RW` | Night Freq Of Water R61 | 30~120Hz | `60 Hz` | `r61_night_water_freq_7` |
| `0x0149` | `RW` | Night Freq Of Heat R62 | 30~120Hz | `60 Hz` | `r62_night_heat_freq_0` |
| `0x014A` | `RW` | Night Freq Of Heat R63 | 30~120Hz | `60 Hz` | `r63_night_heat_freq_1` |
| `0x014B` | `RW` | Night Freq Of Heat R64 | 30~120Hz | `60 Hz` | `r64_night_heat_freq_2` |
| `0x014C` | `RW` | Night Freq Of Heat R65 | 30~120Hz | `60 Hz` | `r65_night_heat_freq_3` |
| `0x014D` | `RW` | Night Freq Of Heat R66 | 30~120Hz | `60 Hz` | `r66_night_heat_freq_4` |
| `0x014E` | `RW` | Night Freq Of Heat R67 | 30~120Hz | `60 Hz` | `r67_night_heat_freq_5` |
| `0x014F` | `RW` | Night Freq Of Heat R68 | 30~120Hz | `60 Hz` | `r68_night_heat_freq_6` |
| `0x0150` | `RW` | Night Freq Of Heat R69 | 30~120Hz | `60 Hz` | `r69_night_heat_freq_7` |
| `0x0151` | `RW` | Night Freq Of Cool R70 | 30~120Hz | `60 Hz` | `r70_night_cool_freq_0` |
| `0x0152` | `RW` | Night Freq Of Cool R71 | 30~120Hz | `60 Hz` | `r71_night_cool_freq_1` |
| `0x0153` | `RW` | Night Freq Of Cool R72 | 30~120Hz | `60 Hz` | `r72_night_cool_freq_2` |
| `0x0154` | `RW` | Night Freq Of Cool R73 | 30~120Hz | `60 Hz` | `r73_night_cool_freq_3` |
| `0x0155` | `RW` | Test Freq Of Water R74 | 30~120Hz | `33 Hz` | `r74_test_water_freq_0` |
| `0x0156` | `RW` | Test Freq Of Water R75 | 30~120Hz | `33 Hz` | `r75_test_water_freq_1` |
| `0x0157` | `RW` | Test Freq Of Water R76 | 30~120Hz | `33 Hz` | `r76_test_water_freq_2` |
| `0x0158` | `RW` | Test Freq Of Water R77 | 30~120Hz | `33 Hz` | `r77_test_water_freq_3` |
| `0x0159` | `RW` | Test Freq Of Water R78 | 30~120Hz | `70 Hz` | `r78_test_water_freq_4` |
| `0x015A` | `RW` | Test Freq Of Water R79 | 30~120Hz | `70 Hz` | `r79_test_water_freq_5` |
| `0x015B` | `RW` | Test Freq Of Water R80 | 30~120Hz | `70 Hz` | `r80_test_water_freq_6` |
| `0x015C` | `RW` | Test Freq Of Water R81 | 30~120Hz | `70 Hz` | `r81_test_water_freq_7` |
| `0x015D` | `RW` | Test Freq Of Heat R82 | 30~120Hz | `33 Hz` | `r82_test_heat_freq_0` |
| `0x015E` | `RW` | Test Freq Of Heat R83 | 30~120Hz | `33 Hz` | `r83_test_heat_freq_1` |
| `0x015F` | `RW` | Test Freq Of Heat R84 | 30~120Hz | `33 Hz` | `r84_test_heat_freq_2` |
| `0x0160` | `RW` | Test Freq Of Heat R85 | 30~120Hz | `33 Hz` | `r85_test_heat_freq_3` |
| `0x0161` | `RW` | Test Freq Of Heat R86 | 30~120Hz | `70 Hz` | `r86_test_heat_freq_4` |
| `0x0162` | `RW` | Test Freq Of Heat R87 | 30~120Hz | `70 Hz` | `r87_test_heat_freq_5` |
| `0x0163` | `RW` | Test Freq Of Heat R88 | 30~120Hz | `70 Hz` | `r88_test_heat_freq_6` |
| `0x0164` | `RW` | Test Freq Of Heat R89 | 30~120Hz | `70 Hz` | `r89_test_heat_freq_7` |
| `0x0165` | `RW` | Test Freq Of Cool R90 | 30~120Hz | `60 Hz` | `r90_test_cool_freq_0` |
| `0x0166` | `RW` | Test Freq Of Cool R91 | 30~120Hz | `60 Hz` | `r91_test_cool_freq_1` |
| `0x0167` | `RW` | Test Freq Of Cool R92 | 30~120Hz | `60 Hz` | `r92_test_cool_freq_2` |
| `0x0168` | `RW` | Test Freq Of Cool R93 | 30~120Hz | `60 Hz` | `r93_test_cool_freq_3` |
| `0x0169` | `RW` | E01 Economic Heat Ambi 1 | -30~50℃ | `-15 °C` | `econ_heat_ambi_1` |
| `0x016A` | `RW` | E02 Economic Heat Ambi 2 | -30~50℃ | `50 °C` | `econ_heat_ambi_2` |
| `0x016B` | `RW` | E03 Economic Heat Ambi 3 | -30~50℃ | `7 °C` | `econ_heat_ambi_3` |
| `0x016C` | `RW` | E04 Economic Heat Ambi 4 | -30~50℃ | `18 °C` | `econ_heat_ambi_4` |
| `0x016D` | `RW` | E05 Economic Water Ambi 1 | -30~50℃ | `0 °C` | `econ_water_ambi_1` |
| `0x016E` | `RW` | E06 Economic Water Ambi 2 | -30~50℃ | `10 °C` | `econ_water_ambi_2` |
| `0x016F` | `RW` | E07 Economic Water Ambi 3 | -30~50℃ | `20 °C` | `econ_water_ambi_3` |
| `0x0170` | `RW` | E08 Economic Water Ambi 4 | -30~50℃ | `30 °C` | `econ_water_ambi_4` |
| `0x0171` | `RW` | E09 Economic Cool Ambi 1 | -30~50℃ | `20 °C` | `econ_cool_ambi_1` |
| `0x0172` | `RW` | E10 Economic Cool Ambi 2 | -30~50℃ | `25 °C` | `econ_cool_ambi_2` |
| `0x0173` | `RW` | E11 Economic Cool Ambi 3 | -30~50℃ | `30 °C` | `econ_cool_ambi_3` |
| `0x0174` | `RW` | E12 Economic Cool Ambi 4 | -30~50℃ | `35 °C` | `econ_cool_ambi_4` |
| `0x0175` | `RW` | E13 Economic Heat Temp 1 | 10~55 · n*0.5℃（Read only lower 8 bits） | `45.0 °C` | `econ_heat_temp_1` |
| `0x0176` | `RW` | E14 Economic Heat Temp 2 | 10~55 · n*0.5℃（Read only lower 8 bits） | `45.0 °C` | `econ_heat_temp_2` |
| `0x0177` | `RW` | E15 Economic Heat Temp 3 | 10~55 · n*0.5℃（Read only lower 8 bits） | `40.0 °C` | `econ_heat_temp_3` |
| `0x0178` | `RW` | E16 Economic Heat Temp 4 | 10~55 · n*0.5℃（Read only lower 8 bits） | `35.0 °C` | `econ_heat_temp_4` |
| `0x0179` | `RW` | E17 Economic Water Temp 1 | 10~55 · n*0.5℃（Read only lower 8 bits） | `50.0 °C` | `econ_water_temp_1` |
| `0x017A` | `RW` | E18 Economic Water Temp 2 | 10~55 · n*0.5℃（Read only lower 8 bits） | `50.0 °C` | `econ_water_temp_2` |
| `0x017B` | `RW` | E19 Economic Water Temp 3 | 10~55 · n*0.5℃（Read only lower 8 bits） | `48.0 °C` | `econ_water_temp_3` |
| `0x017C` | `RW` | E20 Economic Water Temp 4 | 10~55 · n*0.5℃（Read only lower 8 bits） | `45.0 °C` | `econ_water_temp_4` |
| `0x017D` | `RW` | E21 Economic Cool Temp 1 | 12~30 · n*0.5℃（Read only lower 8 bits） | `15.0 °C` | `econ_cool_temp_1` |
| `0x017E` | `RW` | E22 Economic Cool Temp 2 | 12~30 · n*0.5℃（Read only lower 8 bits） | `15.0 °C` | `econ_cool_temp_2` |
| `0x017F` | `RW` | E23 Economic Cool Temp 3 | 12~30 · n*0.5℃（Read only lower 8 bits） | `12.0 °C` | `econ_cool_temp_3` |
| `0x0180` | `RW` | E24 Economic Cool Temp 4 | 12~30 · n*0.5℃（Read only lower 8 bits） | `12.0 °C` | `econ_cool_temp_4` |
| `0x0181` | `RW` | G08 Comp Delay | 1~60min | `50 min` | `comp_delay_hotwater` |
| `0x0182` | `RW` | G06 Comp Delay | 1~60min | `50 min` | `comp_delay_heating` |
| `0x0183` | `RW` | G07 Hotwater Heater Ext | -30~30℃ | `-15 °C` | `hotwater_heater_ext_temp` |
| `0x0184` | `RW` | G05 Heating Heater Ext | -30~30℃ | `-15 °C` | `heating_heater_ext_temp` |
| `0x0185` | `RW` | G03 Start Internal | 1~120min | `5 min` | `pump_cycle` |
| `0x0186` | `RW` | F13 DC Pump Mode | 0 manual/1 auto | Observed `1` (`Auto`) | `f13_dc_pump_mode` |
| `0x0187` | `RW` | F14 DC Pump Cycle | 10~120s | `30 s` | `f14_dc_pump_cycle` |
| `0x0188` | `RW` | F15 DC Pump Freq Set | 10~100% | `80 %` | `f15_dc_pump_freq_set` |
| `0x0189` | `RW` | F16 DC Pump Max Freq | 10~100% | `100 %` | `f16_dc_pump_max_freq` |
| `0x018A` | `RW` | F17 DC Pump Min Freq | 10~100% | `80 %` | `f17_dc_pump_min_freq` |
| `0x018B` | `RW` | F18 DC Pump Scale Factor | 1~10 | `1` | `f18_dc_pump_scale_factor` |
| `0x018C` | `RW` | F19 DC Pump Diff | 0~100 | `0` | `f19_dc_pump_diff` |
| `0x018D` | `RW` | G04 Delta Tempset | 5~30℃ | `5 °C` | `dc_pump_temp_diff` |
| `0x018E` | `RW` | F21 Comp Freq Scale Factor | 1~10 | `10` | `f21_comp_freq_scale_factor` |
| `0x018F` | `RW` | F22 Comp Freq Diff | 0~100 | `0` | `f22_comp_freq_diff` |
| `0x0190` | `RW` | F23 Compressor Mode | 0 NOR，1 ECO， · 2 Night，3 Test | `0` | `fan_mode` |
| `0x0191` | `RW` | G09 Enable Switch | NO linkage · YES amb | `0` | `mode_control_enable` |
| `0x0192` | `RW` | G10 Ambtemp Switch Setp | -20~30℃ | `25 °C` | `ambient_switch_setpoint` |
| `0x0193` | `RW` | G11 Ambtemp Diff | 1~10℃ | `4 °C` | `ambient_switch_diff` |
| `0x0194` | `RW` | F27 Limit Freq Temp Diff | 5~20℃ | `10 °C` | `f27_limit_freq_temp_diff` |
| `0x0195` | `RW` | F28 Dec.freq Temp Diff | 5~20℃ | `11 °C` | `f28_dec_freq_temp_diff` |
| `0x0196` | `RW` | F29 Limit Freq Outlet Low | 0~20℃ | `7 °C` | `f29_limit_freq_outlet_low` |
| `0x0197` | `RW` | F30 Dec.freq Outlet Low | 0~20℃ | `6 °C` | `f30_dec_freq_outlet_low` |
| `0x0198` | `RW` | F31 Limit Freq Outlet High | 30~80℃ | `56 °C` | `f31_limit_freq_outlet_high` |
| `0x0199` | `RW` | F32 Dec Freq Outlet High | 30~80℃ | `57 °C` | `f32_dec_freq_outlet_high` |
| `0x019A` | `RW` | Temp.set Point Of Antilegionella | antilegionella · 30~70 | `70 °C` | `antilegionella_temp` |
| `0x019B` | `RW` | Weekday Of Antilegionella | 0(Sun)~6(Sat) | `1` | `antilegionella_weekday` |
| `0x019C` | `RW` | Start Timer Of Antilegionella | 0~23 | `8 h` | `antilegionella_start_hour` |
| `0x019D` | `RW` | End Timer Of Antilegionella | 0~23 | `11 h` | `antilegionella_end_hour` |
| `0x019E` | `RW` | G02 Pump Work | 0-Interval， · 1-Normal · 2-Demand | `1` | `pump_mode` |
| `0x019F` | `RW` | F35 Antifreeze Cycle | 1~60min | `2 min` | `f35_antifreeze_cycle` |
| `0x01A0` | `RW` | F36 Three-way Valve Cycle | 1~60hour | `24 h` | `f36_three_way_valve_cycle` |
| `0x01A1` | `RW` | F37 Pump Cycle In Error | 1~120min | `60 min` | `f37_pump_cycle_in_error` |
| `0x01A2` | `RW` | F38 Comp Freq Cycle | 20~60s | `20 s` | `f38_comp_freq_cycle` |
| `0x01A3` | `RW` | F41 Air Too Low Stp | -40~0 | `-30 °C` | `f41_air_too_low_stp` |
| `0x01A4` | `RW` | Hotwater Set Temp Of Timeband 1 | 56~120 · n*0.5℃（Read only lower 8 bits） | `30.0 °C` | `timeband_1_hotwater_setp` |
| `0x01A5` | `RW` | Heat Set Temp Of Timeband 1 | 30~100 · n*0.5℃（Read only lower 8 bits） | `36.0 °C` | `timeband_1_heat_setp` |
| `0x01A6` | `RW` | Cool Set Temp Of Timeband 1 | 14~60 · n*0.5℃（Read only lower 8 bits） | `12.0 °C` | `timeband_1_cool_setp` |
| `0x01A7` | `RW` | Hotwater Set Temp Of Timeband 2 | 56~120 · n*0.5℃（Read only lower 8 bits） | `50.0 °C` | `timeband_2_hotwater_setp` |
| `0x01A8` | `RW` | Heat Set Temp Of Timeband 2 | 30~100 · n*0.5℃（Read only lower 8 bits） | `35.0 °C` | `timeband_2_heat_setp` |
| `0x01A9` | `RW` | Cool Set Temp Of Timeband 2 | 14~60 · n*0.5℃（Read only lower 8 bits） | `12.0 °C` | `timeband_2_cool_setp` |
| `0x01AA` | `RW` | Hotwater Set Temp Of Timeband 3 | 56~120 · n*0.5℃（Read only lower 8 bits） | `50.0 °C` | `timeband_3_hotwater_setp` |
| `0x01AB` | `RW` | Heat Set Temp Of Timeband 3 | 30~100 · n*0.5℃（Read only lower 8 bits） | `35.0 °C` | `timeband_3_heat_setp` |
| `0x01AC` | `RW` | Cool Set Temp Of Timeband 3 | 14~60 · n*0.5℃（Read only lower 8 bits） | `12.0 °C` | `timeband_3_cool_setp` |
| `0x01AD` | `RW` | Week Set Of Timeband 1 | 0~6 | Observed `126` (`0b01111110`) — **7-bit Mon–Sat weekday bitmask (`0–127`)**, NOT `0–6` | `timeband_1_weekday` |
| `0x01AE` | `RW` | Week Set Of Timeband 2 | 0~6 | Observed `0` (7-bit weekday bitmask `0–127`) | `timeband_2_weekday` |
| `0x01AF` | `RW` | Week Set Of Timeband 3 | 0~6 | Observed `0` (7-bit weekday bitmask `0–127`) | `timeband_3_weekday` |
| `0x01B0` | `RW` | H17 Def Fan High Press | 20~40bar | `35 bar` | `h17_def_fan_high_press` |
| `0x01B1` | `RW` | H18 Def Fan Speed | 20~100 · n*10rpm | `400 rpm` | `h18_def_fan_speed` |
| `0x01B2` | `RW` | F47 High Press Adjust | -50~50 | `0` | `f47_high_press_adjust` |
| `0x01B3` | `RW` | F48 Low Press Adjust | -50~50 | `0` | `f48_low_press_adjust` |
| `0x01B4` | `RW` | F51 Air Too Low Diff | 1~10℃ | `2 °C` | `f51_air_too_low_diff` |
| `0x01B5` | `RW` | B93 AV Init Outlet Stp | 20~60℃ | `45 °C` | `b93_av_init_outlet_stp` |
| `0x01B6` | `RW` | F53 Outlet Temp Offset Stp | 30~55℃ | `48 °C` | `f53_outlet_temp_offset_stp` |
| `0x01B7` | `RW` | F52 Outlet Temp Offset | 0~50℃ | `5 °C` | `f52_outlet_temp_offset` |
| `0x01B8` | `RW` | F54 Heat Upper Limit Stp | 10~80 | `55 °C` | `f54_heat_upper_limit_stp` |
| `0x01B9` | `RW` | F55 Cool Lower Limit Stp | 7~30 | `12 °C` | `f55_cool_lower_limit_stp` |
| `0x01BA` | `RW` | F56 Model Selection | 1~10 · 1- A102508 · 2- A202508 · 3- A103008 · 4- A203008 · 5- A104008 · 6- A204008 · 7- A105008 · 8- A205008 · 9- A106008 · 10- A206008 | Observed `2` (`A202508`) | `f56_model_selection` |
| `0x01BB` | `RW` | R94 Oil Return Freq | 10~70 | `40 Hz` | `r94_oil_return_freq` |

## Integration Batching & Polling Architecture

- **Fast Telemetry Poll (every `scan_interval`, default `10s`):** 1 contiguous read `0x0000–0x0031` (`50` registers → `49` core sensors + `49` core binary sensors), measured at **`0.146–0.186 s`** live.
- **RW & Expert Batch Poll (startup + every `20` cycles / `~200 s`):** `10` confirmed batches (`<= 62` registers/batch, skipping PDF `Invalid` gaps, `0.20 s` inter-batch turnaround) + `2` optional batches (`0x006A–0x006F`, `0x0072–0x0077`), measured at **`4.084–4.384 s`** live across `385` decoded entries with zero errors.
- **Opt-in Expert Visibility & Writes (`enable_expert_writes`, default `false`):** Core telemetry/alarms (`0x0000–0x0031`) plus core controls (`P01–P07`, `E01–E24`, `G01–G11`, Antilegionella, `Power`, `Failure Reset`, `2x Climate`) total **`149`** enabled-by-default entities. All **`353` RO expert diagnostic entities** (`336` `sensor` + `17` `binary_sensor` across the newly mapped `0x0032–0x01BB` expert ranges) are created with **`entity_registry_enabled_default = False`** (hidden by default in HA until manually enabled). Enabling `enable_expert_writes` in **Configure** adds **`337`** writable CHICO `Config` entities (`322` `number` entities in `box` mode supporting `INT16`, `raw_offset`, and masked `0x01A4–0x01AC` Timeband low-byte RMW writes; `2` `select` entities; `13` `switch` entities), while keeping dangerous `parameters_reset_flag` (`0x0033` bit 6) and unconfirmed gaps non-writable.
- **Diagnostics & Logging:** Pre-release builds (`alpha`/`beta`/`rc`/`dev`) default the integration log level to `DEBUG`, and [diagnostics.py](../custom_components/sprsun_modbus/diagnostics.py) exports redacted coordinator/entity diagnostics.

For detailed user parameter descriptions, see [CHICO_PARAMETERS_GUIDE.md](CHICO_PARAMETERS_GUIDE.md).
