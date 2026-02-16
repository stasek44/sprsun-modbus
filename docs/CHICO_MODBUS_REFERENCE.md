# SPRSUN Heat Pump Modbus Protocol Reference

## Communication Protocol

**Physical Layer:**
- RS485 Modbus RTU
- Baud rate: 19200 bps
- Data format: 8 data bits, 2 stop bits, no parity, 1 start bit
- Asynchronous serial signal

**Protocol Details:**
- Standard MODBUS RTU protocol
- 16-bit data structure
- 16-bit CRC checksum (low byte first, high byte second)
- Device addresses: #1 to #8 (determined by dial codes 2-4)
- Master-slave architecture (Upper computer = master, Controller = slave)

## Supported Modbus Commands

### 03H - Read Holding Registers (4x)
**TX:** `[Device address] + [03H] + [Start register high] + [Start register low] + [Count high] + [Count low] + [CRC low] + [CRC high]`

**RX:** `[Device address] + [03H] + [Byte count] + [Data 1] + [Data 2] + ... + [Data n] + [CRC low] + [CRC high]`

### 06H - Write Single Register
**TX:** `[Device address] + [06H] + [Register high] + [Register low] + [Data high] + [Data low] + [CRC low] + [CRC high]`

**RX:** If successful, returns TX command as-is. Otherwise, no response.

### 10H - Write Multiple Registers
**TX:** `[Device address] + [10H] + [Start high] + [Start low] + [Count high] + [Count low] + [Byte count] + [Data 1 high] + [Data 1 low] + ... + [Data N high] + [Data N low] + [CRC low] + [CRC high]`

**RX:** `[Device address] + [10H] + [Start high] + [Start low] + [Count high] + [Count low] + [CRC low] + [CRC high]`

### 01H - Read Coils
**TX:** `[Device address] + [01H] + [Address high] + [Address low] + [Count high] + [Count low] + [CRC low] + [CRC high]`

**RX:** `[Device address] + [01H] + [Byte count] + [Data 1] + [Data 2] + ... + [Data n] + [CRC low] + [CRC high]`

### 05H - Write Single Coil
**TX:** `[Device address] + [05H] + [Address high] + [Address low] + [Data high] + [Data low] + [CRC low] + [CRC high]`
- Coil data: `[FF][00]` = 1 (ON), `[00][00]` = 0 (OFF)

**RX:** If successful, returns TX command as-is. Otherwise, no response.

## Important Notes

⚠️ **Write Protection:** Only device #1 can modify parameters. Other addresses can only query (read-only).

⚠️ **Signed Integers:** Some temperature registers use signed int16 values (can be negative for ambient/outdoor temperatures in winter).

## Register Map

| Address  | Type | Name                                  | Range/Values                         | Scale/Unit         | Description                                                                                                                                                                                 |
|----------|------|---------------------------------------|--------------------------------------|-------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 0x0000   | R    | Compressor runtime                    | 0-65535                              | hours             | Total compressor running time                                                                                                                                                               |
| 0x0001   | R    | COP                                   | 0-65535                              | 0.01              | Coefficient of Performance                                                                                                                                                                  |
| 0x0002   | R    | Switching input symbol                | Bitfield                             | bits              | **bit 0:** A/C linkage switch<br>**bit 1:** Linkage switch<br>**bit 2:** Heating linkage<br>**bit 3:** Cooling linkage<br>**bit 4:** Flow switch<br>**bit 5:** High pressure switch<br>**bit 6:** Phase sequence detection |
| 0x0003   | R    | Working status mark                   | Bitfield                             | bits              | **bit 0:** Hot water demand<br>**bit 1:** Heating demand<br>**bit 2:** With/without heating<br>**bit 3:** With/without cooling<br>**bit 4:** Antilegionella ON<br>**bit 5:** Cooling demand<br>**bit 6:** Alarm stop<br>**bit 7:** Defrost |
| 0x0004   | R    | Output symbol 1                       | Bitfield                             | bits              | **bit 0:** Compressor<br>**bit 5:** Fan<br>**bit 6:** 4-way valve<br>**bit 7:** Fan speed (0=low, 1=high)                                                                                 |
| 0x0005   | R    | Output symbol 2                       | Bitfield                             | bits              | **bit 0:** Chassis heater<br>**bit 5:** Heating heater<br>**bit 6:** 3-way valve<br>**bit 7:** Hot water heater                                                                           |
| 0x0006   | R    | Output symbol 3                       | Bitfield                             | bits              | **bit 0:** A/C pump<br>**bit 1:** Crank heater<br>**bit 5:** Assistant solenoid valve<br>**bit 6:** Circulation pump                                                                      |
| 0x0007   | R    | Failure symbol 1                      | Bitfield                             | bits              | **bit 0:** Hot water temp sensor<br>**bit 1:** Ambient temp sensor<br>**bit 2:** Coil temp sensor<br>**bit 4:** Outlet temp sensor<br>**bit 5:** High pressure sensor<br>**bit 7:** Phase sequence error |
| 0x0008   | R    | Failure symbol 2                      | Bitfield                             | bits              | **bit 0:** Water flow failure<br>**bit 2:** High protection of heating water outlet                                                                                                        |
| 0x0009   | R    | Failure symbol 3                      | Bitfield                             | bits              | **bit 6:** Outlet gas temp failure                                                                                                                                                          |
| 0x000A   | R    | Failure symbol 4                      | Bitfield                             | bits              | **bit 0:** Water inlet temp failure<br>**bit 1:** Exhaust temp too high<br>**bit 5:** Low protection of cooling water outlet<br>**bit 6:** Inlet gas temp failure                         |
| 0x000B   | R    | Failure symbol 5                      | Bitfield                             | bits              | **bit 0:** Low pressure protection<br>**bit 1:** High pressure protection<br>**bit 2:** Coil temp too high<br>**bit 6:** High pressure sensor failure<br>**bit 7:** Low pressure sensor failure |
| 0x000C   | R    | Failure symbol 6                      | Bitfield                             | bits              | **bit 4:** Secondary antifreeze<br>**bit 5:** Primary antifreeze                                                                                                                           |
| 0x000D   | R    | Failure symbol 7                      | Bitfield                             | bits              | **bit 1:** Ambient temp too low<br>**bit 4:** Frequency conversion module fault<br>**bit 5:** DC fan 2 failure<br>**bit 6:** DC fan 1 failure                                             |
| 0x000E   | R    | Inlet temperature                     | 0-1000                               | 0.1 °C            | Water inlet temperature (return from installation)                                                                                                                                          |
| 0x000F   | R    | Hot water temperature                 | 0-1000                               | 0.1 °C            | DHW tank temperature                                                                                                                                                                        |
| 0x0010   | R    | Invalid                               | -                                    | -                 | Reserved                                                                                                                                                                                    |
| 0x0011   | R    | Ambient temperature                   | -60 to 100 (signed)                  | 0.5 °C            | Outdoor air temperature (⚠️ **SIGNED INT16**)                                                                                                                                               |
| 0x0012   | R    | Outlet temperature                    | 0-1000                               | 0.1 °C            | Water outlet temperature (supply to installation)                                                                                                                                           |
| 0x0013   | R    | Software change time (year)           | 0-99                                 | year              | Firmware version year                                                                                                                                                                       |
| 0x0014   | R    | Software change time (month/day)      | 0-1231                               | MMDD              | Firmware version month/day                                                                                                                                                                  |
| 0x0015   | R    | Suction gas temperature               | -60 to 100 (signed)                  | 0.5 °C            | Refrigerant gas temperature before compressor (⚠️ **SIGNED INT16**)                                                                                                                         |
| 0x0016   | R    | Coil temperature                      | -60 to 100 (signed)                  | 0.5 °C            | Heat exchanger coil temperature (⚠️ **SIGNED INT16**)                                                                                                                                       |
| 0x0017   | R    | AC voltage                            | 0-500                                | V                 | Input voltage                                                                                                                                                                               |
| 0x0018   | R    | Pump flow                             | 0-100                                | m³/h              | Water flow rate                                                                                                                                                                             |
| 0x0019   | R    | Heating/cooling capacity              | 0-30000                              | W                 | Current heating or cooling power output                                                                                                                                                     |
| 0x001A   | R    | AC current                            | 0-100                                | A                 | Input current                                                                                                                                                                               |
| 0x001B   | R    | Exhaust temperature                   | 0-150                                | °C                | Compressor discharge gas temperature                                                                                                                                                        |
| 0x001C   | R    | EEV1 step                             | 0-500                                | steps             | Electronic expansion valve 1 position                                                                                                                                                       |
| 0x001D   | R    | EEV2 step                             | 0-500                                | steps             | Electronic expansion valve 2 position                                                                                                                                                       |
| 0x001E   | R    | Compressor frequency                  | 30-120                               | Hz                | Current compressor speed                                                                                                                                                                    |
| 0x001F   | R    | Frequency conversion failure 1        | 0-255                                | error code        | Inverter error code 1                                                                                                                                                                       |
| 0x0020   | R    | Frequency conversion failure 2        | 0-255                                | error code        | Inverter error code 2                                                                                                                                                                       |
| 0x0021   | R    | DC bus voltage                        | 0-500                                | V                 | Inverter DC bus voltage                                                                                                                                                                     |
| 0x0022   | R    | Driving temperature                   | -60 to 100 (signed)                  | 0.5 °C            | Inverter/motor temperature (⚠️ **SIGNED INT16**)                                                                                                                                            |
| 0x0023   | R    | Compressor current                    | 0-50                                 | A                 | Compressor current draw                                                                                                                                                                     |
| 0x0024   | R    | Target frequency                      | 30-120                               | Hz                | Target compressor speed                                                                                                                                                                     |
| 0x0025   | R    | Smart grid status                     | 0-255                                | -                 | Smart grid communication status                                                                                                                                                             |
| 0x0026   | R    | DC fan 1 speed                        | 0-3000                               | RPM               | Fan 1 speed                                                                                                                                                                                 |
| 0x0027   | R    | DC fan 2 speed                        | 0-3000                               | RPM               | Fan 2 speed                                                                                                                                                                                 |
| 0x0028   | R    | Evaporator temperature                | -60 to 100 (signed)                  | 0.1 °C            | Evaporator temperature (⚠️ **SIGNED INT16**, often negative in heating mode)                                                                                                               |
| 0x0029   | R    | Condenser temperature                 | 0-1000                               | 0.1 °C            | Condenser temperature                                                                                                                                                                       |
| 0x002A   | R    | Frequency conversion fault (high)     | 0-255                                | error code        | Inverter error code (upper 8 bits)                                                                                                                                                          |
| 0x002B   | R    | Frequency conversion fault (low)      | 0-255                                | error code        | Inverter error code (lower 8 bits)                                                                                                                                                          |
| 0x002C   | R    | Controller version                    | 0-999                                | version           | Main controller firmware version                                                                                                                                                            |
| 0x002D   | R    | Display version                       | 0-999                                | version           | Display panel firmware version                                                                                                                                                              |
| 0x002E   | R    | DC pump speed                         | 0-100                                | %                 | Variable speed pump speed percentage                                                                                                                                                        |
| 0x002F   | R    | Discharge pressure                    | 0-50                                 | 0.1 PSI (×0.0069=bar) | High-side pressure (⚠️ **Documentation labels this as "Suct.press" but it's actually discharge**)                                                                                          |
| 0x0030   | R    | Suction pressure                      | 0-50                                 | 0.1 PSI (×0.0069=bar) | Low-side pressure (⚠️ **Documentation labels this as "Disch.press" but it's actually suction**)                                                                                            |
| 0x0031   | R    | DC fan target                         | 0-3000                               | RPM               | Target fan speed                                                                                                                                                                            |
| 0x0032   | RW   | Parameter marker                      | Bitfield                             | bits              | **bit 0:** Power ON/OFF (0=OFF, 1=ON) - Coil address 0x0320                                                                                                                                |
| 0x0033   | RW   | Control mark 1                        | Bitfield                             | bits              | **bit 7:** Failure reset (0=unused, 1=reset) - Coil address 0x0337                                                                                                                         |
| 0x0034   | RW   | Control mark 2                        | Bitfield                             | bits              | **bit 0:** Antilegionella enable (0=disabled, 1=enabled) - Coil 0x0340<br>**bit 1:** Two/Three function (G01) (0=two, 1=three) - Coil 0x0341                                              |
| 0x0036   | RW   | **P06** Unit mode                     | 0-4                                  | mode              | **0:** DHW only<br>**1:** Heating only<br>**2:** Cooling only<br>**3:** Heating + DHW<br>**4:** Cooling + DHW                                                                              |
| 0x00C6   | RW   | **P03** Temperature differential      | 2-18                                 | °C                | Heating/cooling hysteresis                                                                                                                                                                  |
| 0x00C8   | RW   | **P05** Hot water temp differential   | 2-18                                 | °C                | DHW hysteresis                                                                                                                                                                              |
| 0x00CA   | RW   | **P04** Hot water setpoint            | 10-55                                | 0.5 °C            | DHW target temperature (read only lower 8 bits)                                                                                                                                             |
| 0x00CB   | RW   | **P02** Cooling setpoint              | 12-30                                | 0.5 °C            | Cooling target temperature (read only lower 8 bits)                                                                                                                                         |
| 0x00CC   | RW   | **P01** Heating setpoint              | 10-55                                | 0.5 °C            | Heating target temperature (read only lower 8 bits)                                                                                                                                         |
| 0x0169   | RW   | **E01** Economic heat ambient 1       | -30 to 50 (signed)                   | °C                | Economic mode: Ambient temp point 1 for heating (⚠️ **SIGNED INT16**)                                                                                                                      |
| 0x016A   | RW   | **E02** Economic heat ambient 2       | -30 to 50 (signed)                   | °C                | Economic mode: Ambient temp point 2 for heating (⚠️ **SIGNED INT16**)                                                                                                                      |
| 0x016B   | RW   | **E03** Economic heat ambient 3       | -30 to 50 (signed)                   | °C                | Economic mode: Ambient temp point 3 for heating (⚠️ **SIGNED INT16**)                                                                                                                      |
| 0x016C   | RW   | **E04** Economic heat ambient 4       | -30 to 50 (signed)                   | °C                | Economic mode: Ambient temp point 4 for heating (⚠️ **SIGNED INT16**)                                                                                                                      |
| 0x016D   | RW   | **E05** Economic water ambient 1      | -30 to 50 (signed)                   | °C                | Economic mode: Ambient temp point 1 for DHW (⚠️ **SIGNED INT16**)                                                                                                                          |
| 0x016E   | RW   | **E06** Economic water ambient 2      | -30 to 50 (signed)                   | °C                | Economic mode: Ambient temp point 2 for DHW (⚠️ **SIGNED INT16**)                                                                                                                          |
| 0x016F   | RW   | **E07** Economic water ambient 3      | -30 to 50 (signed)                   | °C                | Economic mode: Ambient temp point 3 for DHW (⚠️ **SIGNED INT16**)                                                                                                                          |
| 0x0170   | RW   | **E08** Economic water ambient 4      | -30 to 50 (signed)                   | °C                | Economic mode: Ambient temp point 4 for DHW (⚠️ **SIGNED INT16**)                                                                                                                          |
| 0x0171   | RW   | **E09** Economic cool ambient 1       | -30 to 50 (signed)                   | °C                | Economic mode: Ambient temp point 1 for cooling (⚠️ **SIGNED INT16**)                                                                                                                      |
| 0x0172   | RW   | **E10** Economic cool ambient 2       | -30 to 50 (signed)                   | °C                | Economic mode: Ambient temp point 2 for cooling (⚠️ **SIGNED INT16**)                                                                                                                      |
| 0x0173   | RW   | **E11** Economic cool ambient 3       | -30 to 50 (signed)                   | °C                | Economic mode: Ambient temp point 3 for cooling (⚠️ **SIGNED INT16**)                                                                                                                      |
| 0x0174   | RW   | **E12** Economic cool ambient 4       | -30 to 50 (signed)                   | °C                | Economic mode: Ambient temp point 4 for cooling (⚠️ **SIGNED INT16**)                                                                                                                      |
| 0x0175   | RW   | **E13** Economic heat temp 1          | 10-55                                | 0.5 °C            | Economic mode: Target temp 1 for heating (read only lower 8 bits)                                                                                                                          |
| 0x0176   | RW   | **E14** Economic heat temp 2          | 10-55                                | 0.5 °C            | Economic mode: Target temp 2 for heating (read only lower 8 bits)                                                                                                                          |
| 0x0177   | RW   | **E15** Economic heat temp 3          | 10-55                                | 0.5 °C            | Economic mode: Target temp 3 for heating (read only lower 8 bits)                                                                                                                          |
| 0x0178   | RW   | **E16** Economic heat temp 4          | 10-55                                | 0.5 °C            | Economic mode: Target temp 4 for heating (read only lower 8 bits)                                                                                                                          |
| 0x0179   | RW   | **E17** Economic water temp 1         | 10-55                                | 0.5 °C            | Economic mode: Target temp 1 for DHW (read only lower 8 bits)                                                                                                                              |
| 0x017A   | RW   | **E18** Economic water temp 2         | 10-55                                | 0.5 °C            | Economic mode: Target temp 2 for DHW (read only lower 8 bits)                                                                                                                              |
| 0x017B   | RW   | **E19** Economic water temp 3         | 10-55                                | 0.5 °C            | Economic mode: Target temp 3 for DHW (read only lower 8 bits)                                                                                                                              |
| 0x017C   | RW   | **E20** Economic water temp 4         | 10-55                                | 0.5 °C            | Economic mode: Target temp 4 for DHW (read only lower 8 bits)                                                                                                                              |
| 0x017D   | RW   | **E21** Economic cool temp 1          | 12-30                                | 0.5 °C            | Economic mode: Target temp 1 for cooling (read only lower 8 bits)                                                                                                                          |
| 0x017E   | RW   | **E22** Economic cool temp 2          | 12-30                                | 0.5 °C            | Economic mode: Target temp 2 for cooling (read only lower 8 bits)                                                                                                                          |
| 0x017F   | RW   | **E23** Economic cool temp 3          | 12-30                                | 0.5 °C            | Economic mode: Target temp 3 for cooling (read only lower 8 bits)                                                                                                                          |
| 0x0180   | RW   | **E24** Economic cool temp 4          | 12-30                                | 0.5 °C            | Economic mode: Target temp 4 for cooling (read only lower 8 bits)                                                                                                                          |
| 0x0181   | RW   | **G08** Compressor delay (DHW)        | 1-60                                 | minutes           | Delay before compressor start after DHW heater stops                                                                                                                                        |
| 0x0182   | RW   | **G06** Compressor delay (heating)    | 1-60                                 | minutes           | Delay before compressor start after heating heater stops                                                                                                                                    |
| 0x0183   | RW   | **G07** Hot water heater external temp| -30 to 30 (signed)                   | °C                | Ambient temp below which DHW heater activates (⚠️ **SIGNED INT16**)                                                                                                                        |
| 0x0184   | RW   | **G05** Heating heater external temp  | -30 to 30 (signed)                   | °C                | Ambient temp below which heating heater activates (⚠️ **SIGNED INT16**)                                                                                                                    |
| 0x0185   | RW   | **G03** Start interval                | 1-120                                | minutes           | Minimum time between compressor starts (protection)                                                                                                                                         |
| 0x018D   | RW   | **G04** Delta temperature set         | 5-30                                 | °C                | Temperature differential for DC pump speed control                                                                                                                                          |
| 0x0190   | RW   | **P07** Fan mode                      | 0-3                                  | mode              | **0:** Normal<br>**1:** Economic<br>**2:** Night (quiet)<br>**3:** Test                                                                                                                    |
| 0x0191   | RW   | **G09** Enable switch                 | 0-1                                  | mode              | **0:** NO linkage (manual mode)<br>**1:** YES amb (auto mode based on ambient temp)                                                                                                        |
| 0x0192   | RW   | **G10** Ambient temp switch setpoint  | -20 to 30 (signed)                   | °C                | Ambient temperature for automatic mode switching (⚠️ **SIGNED INT16**)                                                                                                                     |
| 0x0193   | RW   | **G11** Ambient temp differential     | 1-10                                 | °C                | Hysteresis for automatic mode switching                                                                                                                                                     |
| 0x019A   | RW   | Antilegionella temperature setpoint   | 30-70                                | °C                | Target temperature for Legionella disinfection cycle                                                                                                                                        |
| 0x019B   | RW   | Antilegionella weekday                | 0-6                                  | day               | Day of week for Legionella cycle (0=Sunday, 6=Saturday)                                                                                                                                    |
| 0x019C   | RW   | Antilegionella start hour             | 0-23                                 | hour              | Start time for Legionella cycle                                                                                                                                                             |
| 0x019D   | RW   | Antilegionella end hour               | 0-23                                 | hour              | End time for Legionella cycle                                                                                                                                                               |
| 0x019E   | RW   | **G02** Pump work mode                | 0-2                                  | mode              | **0:** Interval (anti-freeze cycles)<br>**1:** Normal (continuous)<br>**2:** Demand (on-demand only)                                                                                       |

## Register Notes

### Pressure Registers Swap (0x002F/0x0030)
⚠️ **IMPORTANT:** The register labels in the original documentation are swapped:
- **0x002F** is labeled "Suct.press" but actually contains **discharge pressure** (high-side, ~15-30 bar)
- **0x0030** is labeled "Disch.press" but actually contains **suction pressure** (low-side, ~4-7 bar)

This integration uses the **correct** labeling based on actual values observed.

### Signed Integer Registers
The following registers use signed int16 encoding (values >32767 should be converted to negative):

**Read-Only (5 registers):**
- 0x0011 - Ambient temperature
- 0x0015 - Suction gas temperature
- 0x0016 - Coil temperature
- 0x0022 - Driving temperature
- 0x0028 - Evaporator temperature

**Read-Write (15 registers):**
- 0x0169-0x016C - E01-E04 (Economic heat ambient)
- 0x016D-0x0170 - E05-E08 (Economic water ambient)
- 0x0171-0x0174 - E09-E12 (Economic cool ambient)
- 0x0183 - G07 (Hot water heater external temp)
- 0x0184 - G05 (Heating heater external temp)
- 0x0192 - G10 (Ambient temp switch setpoint)

### Pressure Conversion
Pressure values are reported in **0.1 PSI** units. To convert to bar:
```
bar = register_value × 0.1 PSI × 0.0689476 PSI/bar ≈ register_value × 0.0069
```

### Coil Addresses
Some bitfield registers support individual coil addressing:
- 0x0320 = 0x0032 bit 0 (Power switch)
- 0x0337 = 0x0033 bit 7 (Failure reset)
- 0x0340 = 0x0034 bit 0 (Antilegionella enable)
- 0x0341 = 0x0034 bit 1 (Two/Three function)

## Integration Implementation

This Home Assistant integration reads:
- **50 Read-Only registers** (0x0000-0x0031) in **one batch request** for optimal performance
- **~45 Read-Write registers** individually (scattered addresses, read at startup only)
- **11 Bitfield registers** decoded into **43 binary sensors**

Write operations use device address **#1** only (per protocol specification).

For detailed parameter explanations, see [PARAMETERS_GUIDE.md](PARAMETERS_GUIDE.md).
