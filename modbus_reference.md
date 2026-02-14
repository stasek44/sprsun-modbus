# SPRSUN Heat Pump Modbus Reference

## Communication Protocol Specification

### Basic Configuration
- **Interface**: RS485 Modbus RTU
- **Signal**: Asynchronous serial
- **Format**: 1 start bit, 8 data bits, 2 stop bits, no parity
- **Baud Rate**: 19200 bps
- **Data Structure**: 16-bit, compliant with standard MODBUS RTU protocol
- **Checksum**: 16-bit CRC (low byte first, high byte second)

### Device Addressing
- Unit addresses: #1 - #8 (determined by dial codes 2-4)
- Upper computer: Call host (master)
- Controller: Slave
- **Note**: Parameters can only be modified in #1 machine; other units are query-only

---

## Supported Modbus Commands

### 03H - Read Holding Registers (4x)

**Request (TX):**
```
[Device Address] + [03H] + [Start Register High 8 bits] + [Low 8 bits] + 
[Number of Registers High 8 bits] + [Low 8 bits] + [CRC Low] + [CRC High]
```

**Response (RX):**
```
[Device Address] + [03H] + [Number of Bytes] + [Data 1] + [Data 2] + ... + 
[Data n] + [CRC Low] + [CRC High]
```

### 06H - Write Single Register

**Request (TX):**
```
[Device Address] + [06H] + [Register Address High 8 bits] + [Low 8 bits] + 
[Data High 8 bits] + [Low 8 bits] + [CRC Low] + [CRC High]
```

**Response (RX):**
- If successful: Returns the command as sent
- If failed: No response

### 10H - Write Multiple Registers

**Request (TX):**
```
[Device Address] + [10H] + [Start Register High 8 bits] + [Low 8 bits] + 
[Number of Registers High 8 bits] + [Low 8 bits] + [Number of Bytes] + 
[Data 1 High 8 bits] + [Low 8 bits] + ... + [Data N High 8 bits] + [Low 8 bits] + 
[CRC Low] + [CRC High]
```

**Response (RX):**
```
[Device Address] + [10H] + [Start Register High 8 bits] + [Low 8 bits] + 
[Number of Registers High 8 bits] + [Low 8 bits] + [CRC Low] + [CRC High]
```

### 01H - Read Coils

**Request (TX):**
```
[Device Address] + [01H] + [Query Bit Address High 8 bits] + [Low 8 bits] + 
[Number of Query Bits High 8 bits] + [Low 8 bits] + [CRC Low] + [CRC High]
```

**Response (RX):**
```
[Device Address] + [01H] + [Number of Bytes] + [Data 1] + [Data 2] + ... + 
[Data n] + [CRC Low] + [CRC High]
```

### 05H - Write Single Coil

**Request (TX):**
```
[Device Address] + [05H] + [Bit Address High 8 bits] + [Low 8 bits] + 
[Data High 8 bits] + [Low 8 bits] + [CRC Low] + [CRC High]
```

**Coil Data:**
- `[FF][00]` = 1 (ON)
- `[00][00]` = 0 (OFF)

**Response (RX):**
- If successful: Returns the command as sent
- If failed: No response

---

## Register Map

### System Status Registers (Read-Only)

| Address | Name | Data Range | Scaling | Description |
|---------|------|------------|---------|-------------|
| R 0x0000 | Compressor Runtime | - | - | Accumulated operating time of compressor |
| R 0x0001 | COP | - | - | Coefficient of Performance |
| R 0x0013 | Software Version (Year) | - | - | Time of software change (years) |
| R 0x0014 | Software Version (Month/Day) | - | - | Time of software change (month)(day) |
| R 0x002C | Controller Version | - | - | Master software version |
| R 0x002D | Display Version | - | - | Line controller software version |

### Input Status Flags (Read-Only)

#### R 0x0002 - Switching Input Symbol
| Bit | Description |
|-----|-------------|
| 0 | End linkage switch / A/C Linkage switch |
| 1 | Emergency switch / Linkage switch |
| 2 | Heating Control Switch / Heating linkage |
| 3 | Cooling control switch / Cooling linkage |
| 4 | Water flow switch / Flow Switch |
| 5 | High voltage switch / High pressure switch |
| 6 | Phase Sequence Switch / Phase sequence detection |
| 7 | Grid SG Signal / Invalid |
| 8 | Grid EUV Signal |

#### R 0x0003 - Working Status Mark
| Bit | Description |
|-----|-------------|
| 0 | Hot water demand |
| 1 | Heating demand |
| 2 | With or without heating |
| 3 | With or without cooling |
| 4 | Antilegionella on |
| 5 | Cooling demand |
| 6 | Alarm stop |
| 7 | Defrost |

### Output Status Flags (Read-Only)

#### R 0x0004 - Output Symbol 1
| Bit | Description |
|-----|-------------|
| 0 | Press status / Compressor |
| 1 | Switch off / Invalid |
| 2 | Reserved |
| 3 | Reserved |
| 4 | Reserved |
| 5 | Fan status |
| 6 | 4-way valve status |
| 7 | High and low wind status (0=low, 1=high) |

#### R 0x0005 - Output Symbol 2
| Bit | Description |
|-----|-------------|
| 0 | Chassis electric heating status |
| 1 | Reserved |
| 2 | Reserved |
| 3 | Reserved |
| 4 | Reserved |
| 5 | Heating heater status |
| 6 | Three-way valve status |
| 7 | Hot water heater status |

#### R 0x0006 - Output Symbol 3
| Bit | Description |
|-----|-------------|
| 0 | End pump status / A/C PUMP |
| 1 | Crank heater status |
| 2 | Reserved |
| 3 | Reserved |
| 4 | Reserved |
| 5 | Enhanced enthalpy valve status / Assistant solenoid valve |
| 6 | Water pump status |
| 7 | Reserved |

### Failure/Alarm Flags (Read-Only)

#### R 0x0007 - Failure Symbol 1
| Bit | Description |
|-----|-------------|
| 0 | Tank temperature sensor failure |
| 1 | Ambient temperature sensor failure |
| 2 | Coil temperature sensor failure |
| 3 | Reserved |
| 4 | Outlet temperature sensor failure |
| 5 | High voltage fault |
| 6 | Reserved |
| 7 | Power failure / Phase sequence |

#### R 0x0008 - Failure Symbol 2
| Bit | Description |
|-----|-------------|
| 0 | Water flow switch failure |
| 1 | Reserved |
| 2 | High protection of heating water outlet |
| 3-7 | Reserved |

#### R 0x0009 - Failure Symbol 3
| Bit | Description |
|-----|-------------|
| 0-5 | Reserved |
| 6 | Outlet gas temperature failure |
| 7 | Reserved |

#### R 0x000A - Failure Symbol 4
| Bit | Description |
|-----|-------------|
| 0 | Water inlet temp sensor failure |
| 1 | High exhaust temperature protection |
| 2 | Economy inlet temperature sensor failure |
| 3 | Economy outlet temperature sensor failure |
| 4 | Reserved |
| 5 | Overcooling protection of cooling outlet water |
| 6 | Return air temperature sensor failure |
| 7 | Reserved |

#### R 0x000B - Failure Symbol 5
| Bit | Description |
|-----|-------------|
| 0 | Underpressure protection of low pressure |
| 1 | Overpressure protection of high pressure |
| 2 | High protection of coil temperature |
| 3-5 | Reserved |
| 6 | High pressure sensor failure |
| 7 | Low pressure sensor failure |

#### R 0x000C - Failure Symbol 6
| Bit | Description |
|-----|-------------|
| 0-3 | Reserved |
| 4 | Secondary antifreeze |
| 5 | Primary antifreeze |
| 6-7 | Reserved |

#### R 0x000D - Failure Symbol 7
| Bit | Description |
|-----|-------------|
| 0 | Reserved |
| 1 | Low ambient temperature protection |
| 2-3 | Reserved |
| 4 | Inverter module communication failure |
| 5 | DC fan 2 fault |
| 6 | DC fan 1 fault |
| 7 | Reserved |

### Temperature Sensors (Read-Only)

| Address | Name | Range | Scaling | Description |
|---------|------|-------|---------|-------------|
| R 0x000E | Inlet temp. | - | n×0.1℃ | Water inlet temperature |
| R 0x000F | Hotwater temp. | - | n×0.1℃ | Water tank temperature |
| R 0x0011 | Ambi temp. | - | n×0.5℃ | Ambient temperature |
| R 0x0012 | Outlet temp. | - | n×0.1℃ | Water outlet temperature |
| R 0x0015 | Suct gas temp. | - | n×0.5℃ | Return gas temperature |
| R 0x0016 | Coil temp. | - | n×0.5℃ | Coil temperature |
| R 0x001B | Exhaust temp. | - | n×1℃ | Exhaust temperature |
| R 0x0022 | Driving temp. | - | n×0.5℃ | Heat sink temperature |
| R 0x0028 | Evap. temp. | - | n×0.1℃ | Evaporation temperature |
| R 0x0029 | Cond. temp. | - | n×0.1℃ | Condensation temperature |

### System Measurements (Read-Only)

| Address | Name | Unit | Description |
|---------|------|------|-------------|
| R 0x0017 | AC Voltage | W | AC voltage |
| R 0x0018 | Pump Flow | m³/h | Pump water flow |
| R 0x0019 | Heating/Cooling Capacity | W | Heating/cooling capacity |
| R 0x001A | AC Current | A | AC current |
| R 0x001C | EEV1 Step | - | Main valve opening |
| R 0x001D | EEV2 Step | - | Auxiliary valve opening |
| R 0x001E | Comp. Frequency | Hz | Actual frequency of compressor |
| R 0x0021 | DC Bus Voltage | V | DC bus voltage value |
| R 0x0023 | Comp. Current | A | Compressor current |
| R 0x0024 | Target Frequency | Hz | Compressor target frequency |
| R 0x0026 | DC Fan 1 Speed | - | Actual speed of DC fan 1 |
| R 0x0027 | DC Fan 2 Speed | - | Actual speed of DC fan 2 |
| R 0x002E | DC Pump Speed | - | DC water pump speed |
| R 0x002F | Suct. Press | - | n×0.1 bar | High pressure values |
| R 0x0030 | Disch. Press | - | n×0.1 bar | Low pressure values |
| R 0x0031 | DC Fan Target | - | Target wind speed |

### Inverter Status (Read-Only)

| Address | Name | Description |
|---------|------|-------------|
| R 0x001F | Frequency Conversion Failure 1 | DC inverter failure 1 |
| R 0x0020 | Frequency Conversion Failure 2 | DC inverter failure 2 |
| R 0x0025 | Smart Grid Status | Smart grid status |
| R 0x002A | Freq. Conversion Fault High | Inverter fault high 8 bits (0xFF = fault) |
| R 0x002B | Freq. Conversion Fault Low | Inverter fault low 8 bits |

### Control Registers (Read/Write)

#### RW 0x0032 - Parameter Marker Definition
| Bit | Address | Description |
|-----|---------|-------------|
| 0 | 0x0032×16+0 | Switch on/off: 0=off, 1=on |
| 1 | 0x0032×16+1 | Main valve mode: 0=auto, 1=manual |
| 2 | 0x0032×16+2 | Manual frequency selection |
| 3-4 | - | Reserved |
| 5 | 0x0032×16+5 | Auxiliary valve initial opening: 0=auto, 1=manual |
| 6 | 0x0032×16+6 | Expansion valve initial opening: 0=fixed, 1=adjustable |
| 7 | - | Reserved |

#### RW 0x0033 - Control Mark 1
| Bit | Address | Description |
|-----|---------|-------------|
| 0 | 0x0033×16+0 | Thermostatic adjustment: 0=no, 1=yes |
| 1 | 0x0033×16+1 | Pressure sensor valid: 0=no, 1=yes |
| 2 | 0x0033×16+2 | Cooling auxiliary circuit: 0=allowed, 1=not allowed |
| 3 | 0x0033×16+3 | Auxiliary expansion valve mode: 0=enhanced enthalpy superheat, 1=exhaust superheat |
| 4 | 0x0033×16+4 | DC Fan 1 selection: 0=no, 1=yes |
| 5 | 0x0033×16+5 | DC Fan 2 selection: 0=no, 1=yes |
| 6 | 0x0033×16+6 | Parameter reset: 0=normal, 1=requires reset |
| 7 | 0x0033×16+7 | Lockout fault reset: 0=normal, 1=requires reset |

#### RW 0x0034 - Control Mark 2
| Bit | Address | Description |
|-----|---------|-------------|
| 0 | 0x0034×16+0 | With or without antilegionella |
| 1 | 0x0034×16+1 | With or without hot water |
| 2 | 0x0034×16+2 | Whether clock is at night (20:00-08:00) |
| 3 | 0x0034×16+3 | Load fast check mode: 0=normal, 1=load |
| 4 | 0x0034×16+4 | Forced defrost: 0=no effect, 1=forced entry |
| 5 | - | Reserved |
| 6 | 0x0034×16+6 | With or without smart grid: 0=no, 1=yes |
| 7 | 0x0034×16+7 | Smart grid with or without electric heater: 0=no, 1=yes |

### Basic Configuration Parameters (Read/Write)

| Address | Parameter | Range | Scaling | Description |
|---------|-----------|-------|---------|-------------|
| RW 0x0036 | P06 Unit Mode | 0-4 | - | 0=DHW, 1=Heating, 2=Cooling, 3=Heating+DHW, 4=Cooling+DHW |
| RW 0x00C6 | P03 Temp. Diff | 2-18℃ | - | Cooling/heating startup differential |
| RW 0x00C8 | P05 Temp. Diff | 2-18℃ | - | Hot water startup differential |
| RW 0x00CA | P04 Hotwater Setp. | 10-55 | n×0.5℃ | Hot water setting temperature (read lower 8 bits only) |
| RW 0x00CB | P02 Cooling Setp | 12-30 | n×0.5℃ | Cooling setting temperature (read lower 8 bits only) |
| RW 0x00CC | P01 Heating Setp | 10-55 | n×0.5℃ | Heating setting temperature (read lower 8 bits only) |

### Economic Mode - Heating Parameters (Read/Write)

| Address | Parameter | Range | Description |
|---------|-----------|-------|-------------|
| RW 0x0169 | E01 Economic Heat Ambi 1 | -30~50℃ | Economy mode - heating ambient temperature 1 |
| RW 0x016A | E02 Economic Heat Ambi 2 | -30~50℃ | Economy mode - heating ambient temperature 2 |
| RW 0x016B | E03 Economic Heat Ambi 3 | -30~50℃ | Economy mode - heating ambient temperature 3 |
| RW 0x016C | E04 Economic Heat Ambi 4 | -30~50℃ | Economy mode - heating ambient temperature 4 |
| RW 0x0175 | E13 Economic Heat Temp 1 | 10-55 | n×0.5℃ | Economy mode - heating water temperature 1 |
| RW 0x0176 | E14 Economic Heat Temp 2 | 10-55 | n×0.5℃ | Economy mode - heating water temperature 2 |
| RW 0x0177 | E15 Economic Heat Temp 3 | 10-55 | n×0.5℃ | Economy mode - heating water temperature 3 |
| RW 0x0178 | E16 Economic Heat Temp 4 | 10-55 | n×0.5℃ | Economy mode - heating water temperature 4 |

### Economic Mode - Hot Water Parameters (Read/Write)

| Address | Parameter | Range | Scaling | Description |
|---------|-----------|-------|---------|-------------|
| RW 0x016D | E05 Economic Water Ambi 1 | -30~50℃ | - | Economy mode - hot water ambient temperature 1 |
| RW 0x016E | E06 Economic Water Ambi 2 | -30~50℃ | - | Economy mode - hot water ambient temperature 2 |
| RW 0x016F | E07 Economic Water Ambi 3 | -30~50℃ | - | Economy mode - hot water ambient temperature 3 |
| RW 0x0170 | E08 Economic Water Ambi 4 | -30~50℃ | - | Economy mode - hot water ambient temperature 4 |
| RW 0x0179 | E17 Economic Water Temp 1 | 10-55 | n×0.5℃ | Economy mode - hot water temperature 1 |
| RW 0x017A | E18 Economic Water Temp 2 | 10-55 | n×0.5℃ | Economy mode - hot water temperature 2 |
| RW 0x017B | E19 Economic Water Temp 3 | 10-55 | n×0.5℃ | Economy mode - hot water temperature 3 |
| RW 0x017C | E20 Economic Water Temp 4 | 10-55 | n×0.5℃ | Economy mode - hot water temperature 4 |

### Economic Mode - Cooling Parameters (Read/Write)

| Address | Parameter | Range | Scaling | Description |
|---------|-----------|-------|---------|-------------|
| RW 0x0171 | E09 Economic Cool Ambi 1 | -30~50℃ | - | Economy mode - cooling ambient temperature 1 |
| RW 0x0172 | E10 Economic Cool Ambi 2 | -30~50℃ | - | Economy mode - cooling ambient temperature 2 |
| RW 0x0173 | E11 Economic Cool Ambi 3 | -30~50℃ | - | Economy mode - cooling ambient temperature 3 |
| RW 0x0174 | E12 Economic Cool Ambi 4 | -30~50℃ | - | Economy mode - cooling ambient temperature 4 |
| RW 0x017D | E21 Economic Cool Temp 1 | 12-30 | n×0.5℃ | Economy mode - cooling water temperature 1 |
| RW 0x017E | E22 Economic Cool Temp 2 | 12-30 | n×0.5℃ | Economy mode - cooling water temperature 2 |
| RW 0x017F | E23 Economic Cool Temp 3 | 12-30 | n×0.5℃ | Economy mode - cooling water temperature 3 |
| RW 0x0180 | E24 Economic Cool Temp 4 | 12-30 | n×0.5℃ | Economy mode - cooling water temperature 4 |

### General Configuration Parameters (Read/Write)

| Address | Parameter | Range | Description |
|---------|-----------|-------|-------------|
| RW 0x0181 | G08 Comp. Delay | 1-60 min | Hot water heater startup delay |
| RW 0x0182 | G06 Comp. Delay | 1-60 min | Heating heater startup delay |
| RW 0x0183 | G07 Hotwater Heater Ext. | -30~30℃ | Hot water heater startup ambient temperature |
| RW 0x0184 | G05 Heating Heater Ext. | -30~30℃ | Heating heater startup ambient temperature |
| RW 0x0185 | G03 Start Internal | 1-120 min | Pump thermostatic start/stop cycle |
| RW 0x018D | G04 Delta Temp. Set | 5-30℃ | DC pump inlet/outlet water temperature differential setting |
| RW 0x0190 | P07 FAN Mode | 0-3 | Fan operating mode: 0=NOR, 1=ECO, 2=Night, 3=Test |
| RW 0x0191 | G09 Enable Switch | - | Mode control: NO linkage / YES amb |
| RW 0x0192 | G10 Ambtemp Switch Setp. | -20~30℃ | Switching mode by ambient temperature - setpoint |
| RW 0x0193 | G11 Ambtemp Diff. | 1-10℃ | Switching mode by ambient temperature - differential |
| RW 0x019E | G02 Pump Work | 0-2 | Pump standby operation mode: 0=Interval, 1=Normal, 2=Demand |

### Antilegionella Configuration (Read/Write)

| Address | Parameter | Range | Description |
|---------|-----------|-------|-------------|
| RW 0x019A | Temp. Set Point of Antilegionella | 30-70℃ | Antilegionella temperature setting |
| RW 0x019B | Weekday of Antilegionella | 0-6 | Day of week: 0=Sun, 6=Sat |
| RW 0x019C | Start Timer of Antilegionella | 0-23 | Start time (hours) |
| RW 0x019D | End Timer of Antilegionella | 0-23 | End time (hours) |

---

## Data Type Conventions

### Temperature Scaling
- **n×0.1℃**: Divide register value by 10 to get actual temperature
- **n×0.5℃**: Divide register value by 2 to get actual temperature  
- **n×1℃**: Register value equals actual temperature

### Pressure Scaling
- **n×0.1 bar**: Divide register value by 10 to get actual pressure

### Bit Field Notation
- Bit addresses can be calculated as: `Register_Address × 16 + Bit_Number`
- Example: Bit 3 of register 0x0033 = 0x0033 × 16 + 3

### Read-Only vs Read/Write
- **R**: Read-only registers (query only)
- **RW**: Read/write registers (can be modified on device #1)

---

## Implementation Notes

1. **Error Handling**: If a write command fails, the device will not respond. Implement timeouts and retry logic.

2. **Temperature Conversion**: Always apply the correct scaling factor when reading temperature values.

3. **Bit Manipulation**: When working with status flags and control bits, use proper bit masking techniques.

4. **Device Addressing**: Ensure you're communicating with the correct device address (1-8).

5. **Write Restrictions**: Only device #1 can have parameters modified. Other devices are read-only.

6. **CRC Calculation**: Use standard Modbus RTU CRC-16 algorithm with low byte transmitted first.

7. **Register Size**: All registers are 16-bit (2 bytes).
