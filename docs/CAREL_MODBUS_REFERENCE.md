# SPRSUN CAREL Controller — Modbus Register Reference

> **Status:** Experimental / Beta support (`CarelController`, `v5.6.0-beta.1`).
> Verified against SPRSUN CAREL OEM specifications (`Modbus for DC inverter heat pump v3.xlsx`, `220224 ModBus Adresy Carel CGK.docx`) and community live hardware captures (`CGK0x0V2`, `CGK025–060V3L`). Live community feedback & diagnostic exports on CAREL units are welcome via GitHub Issues.

---

## Serial & Protocol Basics

- **Bus:** RS485 Modbus RTU (`19200-8-N-2` or `19200-8-N-1`, slave ID `#1`), bridged to Modbus TCP via RS485-to-TCP gateway (e.g., Elfin EW11).
- **Modbus Function Codes:**
  - `FC 0x01` / `FC 0x05`: Coils (`0xxxx`)
  - `FC 0x02`: Discrete Inputs (`1xxxx`)
  - `FC 0x03` / `FC 0x06`: Holding Registers (`4xxxx`)
- **Data Encoding:** Analog values and setpoints use **single 16-bit signed Big-Endian (`INT16`)** scaled by `0.1`, except where noted below.

---

## Core Control & Setpoints (Holding Registers `0–15` & Coils `0–42`)

| Space | 0-based Addr | Modbus Addr | Key | Type | Scale | Range / Notes |
| :--- | :---: | :---: | :--- | :---: | :---: | :--- |
| Holding | `0` | `40001` | `unit_mode` | `UINT16` | `1` | `0=Cooling`, `1=Heating`, `2=Hot Water`, `3=Cooling+DHW`, `4=Heating+DHW`. Changing mode while running automatically cycles `Coil 40` OFF → write → ON. |
| Holding | `1` | `40002` | `heating_setpoint` | `INT16` | `0.1` | `10.0–55.0 °C` |
| Holding | `2` | `40003` | `cooling_setpoint` | `INT16` | `0.1` | `12.0–40.0 °C` |
| Holding | `3` | `40004` | `hotwater_setpoint` | `INT16` | `0.1` | `10.0–60.0 °C` |
| Holding | `4` | `40005` | `hotwater_start_diff` | `INT16` | `0.1` | `1.0–15.0 °C` |
| Holding | `5` | `40006` | `hotwater_stop_diff` | `INT16` | `0.1` | `0.0–5.0 °C` |
| Holding | `6` | `40007` | `temp_diff_start` | `INT16` | `0.1` | `1.0–15.0 °C` |
| Holding | `7` | `40008` | `temp_diff_stop` | `INT16` | `0.1` | `0.0–5.0 °C` |
| Holding | `11` | `40012` | `pump_mode` | `UINT16` | `1` | `0=Normal`, `1=Demand`, `2=Interval` |
| Holding | `12` | `40013` | `fan_mode` | `UINT16` | `1` | `0=Daytime`, `1=Night`, `2=Eco`, `3=Pressure` |
| Holding | `14` | `40015` | `aux_heat_ambient_setpoint` | `INT16` | `0.1` | `-30.0–20.0 °C` |
| Holding | `15` | `40016` | `pump_delta_t_setpoint` | `INT16` | `0.1` | `1.0–15.0 °C` |
| Coil | `0` | `00001` | `aux_heat_enable` | `BOOL` | — | Auxiliary heater enable |
| Coil | `2` | `00003` | `auto_restart` | `BOOL` | — | Auto restart after power loss |
| Coil | `38` | `00039` | `schedule_onoff_enable` | `BOOL` | — | Weekly ON/OFF schedule enable |
| Coil | `39` | `00040` | `schedule_setpoint_enable` | `BOOL` | — | Hourly setpoint schedule enable |
| Coil | `40` | `00041` | `power` | `BOOL` | — | **Unit Power ON/OFF** (`OnOffUnitMng.KeybOnOff`) |
| Coil | `41` | `00042` | `reset_alarm` | `BOOL` | — | **Alarm Reset** (momentary button, OEM verified) |
| Coil | `42` | `00043` | `dhw_enable` | `BOOL` | — | **Active-low (`inverted=True`)**: `0=Hot Water ON`, `1=Hot Water OFF` |

---

## Fast Telemetry (Holding `188–217`, `333–335` & Discrete Inputs `0–12`, `178–183`)

| Space | 0-based Addr | Modbus Addr | Key | Type | Scale / Unit |
| :--- | :---: | :---: | :--- | :---: | :--- |
| Holding | `188–192` | `40189–40193` | `inlet_temp`, `outlet_temp`, `ambient_temp`, `discharge_temp`, `suction_temp` | `INT16` | `0.1 °C` |
| Holding | `193–194` | `40194–40195` | `discharge_pressure`, `suction_pressure` | `INT16` | `0.1 bar` |
| Holding | `195–196` | `40196–40197` | `hotwater_temp`, `coil_temp` | `INT16` | `0.1 °C` |
| Holding | `197–198` | `40198–40199` | `fan_output`, `pump_output` | `INT16` | `0.1 %` |
| Holding | `199–202` | `40200–40203` | `fan1_rpm_out`, `fan1_rpm_feedback`, `fan2_rpm_out`, `fan2_rpm_feedback` | `UINT16` | `1 rpm` |
| Holding | `203–205` | `40204–40206` | `compressor_request` (`%`), `compressor_actual_cap` (`%`), `compressor_speed` (`rps`) | `INT16` | `0.1` |
| Holding | `206–211` | `40207–40212` | `evap_temp`, `eev_opening` (`1 steps`), `discharge_superheat`, `bldc_status` (`0..2`), `eev_protection` (`0..5`), `suction_superheat` | `INT16` / `UINT16` | `0.1` / `1` |
| Holding | `215–217` | `40216–40218` | `unit_run_mode` (`0..2`), `target_temp` (`0.1 °C`), `unit_status` (`0..10`) | `UINT16` / `INT16` | — |
| Holding | `333–335` | `40334–40336` | `bldc_power` (`*100 W`), `bldc_voltage` (`1 V`), `bldc_current` (`0.1 A`) | `INT16` / `UINT16` | Optional batch |
| DI | `0–4` | `10001–10005` | `unit_on`, `flow_switch`, `linkage_switch`, `ac_linkage_switch`, `phase_switch` | `BOOL` | Active-high |
| DI | `5–12` | `10006–10013` | `DO1–DO7`, `DO9` (Fan High/Low, 4-Way Valve, Pump, Chassis/Crank Heater, 3-Way Valve, Backup Heater) | `BOOL` | Active-high |
| DI | `178–183` | `10179–10184` | `pump_running`, `compressor_running`, `fan_running`, `cooling_linkage`, `heating_linkage`, `terminal_pump` | `BOOL` | Active-high |
| DI | `13–177` | `10014–10178` | Alarms `AL001`–`AL155`, `AL165`–`AL174` | `BOOL` | Aggregated into `alarm_active` + `active_alarms` (with `alarms` attribute) |

---

## Opt-In Expert Parameters & Safety Locks

When **Enable Expert Settings** (`enable_expert_writes=True`) is turned on in integration options, the following CAREL engineering registers are exposed as `NumberMode.BOX` / `EntityCategory.CONFIG`:
- **PID & Aux Delay:** Holding `8..10` (`Kp`, `Ti`, `Td`), `13` (`aux_comp_delay`).
- **Night Mode Limits:** Holding `263..264` (max compressor rps / fan rpm).
- **ECO Weather Curves (4-point):** Holding `276..296`, `336..338` (Cooling/Heating/DHW `X1–X4`, `Y1–Y4`).
- **Defrost Tuning:** Holding `77..91`, Coil `36` (`defrost_enable`).
- **Heater Type & Linkage Polarity:** Holding `323`, Coil `18` (`ac_linkage_normally_open`).

### Permanently Locked Safety Registers (NEVER Writable)

The following OEM registers are explicitly blocked in `tests/test_protocol_invariants.py`:
- **Coil `57` (`00058`):** Factory parameter reset (`Reset parametrów`)
- **Holding `332` (`40333`):** Insert BLDC default (`Insert BLDC default`)
