# SPRSUN Heat Pump Modbus Poller

This Python script polls all read-only Modbus registers from a SPRSUN heat pump and saves the data to a CSV file.

## Features

- Polls all read-only registers from the Modbus reference
- Runs for 15 minutes with configurable polling interval (default: 10 seconds)
- Applies proper scaling factors (0.1, 0.5, 1.0) to temperature and pressure readings
- Saves data to timestamped CSV file
- Real-time display of key parameters during polling
- Handles signed/unsigned integer conversion
- Error handling and graceful shutdown

## Configuration

The script is pre-configured with:
- **Host**: 192.168.1.234
- **Port**: 502
- **Device Address**: 1 (Modbus slave ID)
- **Poll Interval**: 10 seconds
- **Duration**: 15 minutes

To change these settings, edit the constants at the top of `modbus_poller.py`:

```python
MODBUS_HOST = "192.168.1.234"
MODBUS_PORT = 502
DEVICE_ADDRESS = 1
POLL_INTERVAL = 10  # seconds between polls
```

## Read-Only Registers

The script reads the following register categories:

1. **System Status** - Runtime, COP, software versions
2. **Input Status Flags** - Switch states, linkages
3. **Working Status** - Operation mode indicators
4. **Output Status** - Compressor, fan, valve, pump states
5. **Failure/Alarm Flags** - 7 registers of fault indicators
6. **Temperature Sensors** - 10 temperature readings with proper scaling
7. **System Measurements** - Voltage, current, flow, pressure, speeds
8. **Inverter Status** - Frequency conversion status and faults

## Usage

### Option 1: Using the run script
```bash
./run_poller.sh
```

### Option 2: Direct Python execution
```bash
/home/stanislaw/src/sprsun-modbus/.venv/bin/python modbus_poller.py
```

### Option 3: Activate venv first
```bash
source .venv/bin/activate
python modbus_poller.py
deactivate
```

## Output

The script creates a CSV file named `sprsun_modbus_data_YYYYMMDD_HHMMSS.csv` with:
- Timestamp column
- One column for each register (using the "name" from the reference document)
- Values scaled according to the Modbus reference specification

### Example CSV Structure:
```
Timestamp,Compressor Runtime,COP,Software Version (Year),...
2026-02-13 14:30:00,12345,3.5,2023,...
2026-02-13 14:30:10,12346,3.4,2023,...
```

## Data Scaling

The script automatically applies scaling factors:
- **Temperature (n×0.1°C)**: Inlet, Outlet, Hotwater, Evap., Cond. temps
- **Temperature (n×0.5°C)**: Ambient, Suction gas, Coil, Driving temps
- **Temperature (n×1°C)**: Exhaust temp
- **Pressure (n×0.1 bar)**: Suction and Discharge pressures

## Interrupt

To stop the script before 15 minutes, press `Ctrl+C`. The data collected up to that point will be saved.

## Requirements

- Python 3.12+
- pymodbus 3.5.0+

The virtual environment and dependencies are already configured in `.venv/`.

## Troubleshooting

### Connection Failed
- Verify the heat pump is powered on and connected to the network
- Check the IP address (192.168.1.234) is correct
- Ensure port 502 is not blocked by firewall
- Ping the device: `ping 192.168.1.234`

### No Data / All NULL Values
- Check the device address (slave ID) is correct (default: 1)
- Verify Modbus TCP is enabled on the heat pump
- Check if other Modbus clients can connect

### Permission Errors
- Ensure the script has execution permissions: `chmod +x modbus_poller.py`
- Check write permissions in the current directory

## Modbus Protocol Details

- **Protocol**: Modbus TCP (over RS485 Modbus RTU)
- **Command Used**: 0x03 (Read Holding Registers)
- **Data Format**: 16-bit registers, signed integers where applicable
- **Byte Order**: Big-endian (standard Modbus)

## Files

- `modbus_poller.py` - Main polling script
- `run_poller.sh` - Convenience script to run the poller
- `requirements.txt` - Python package dependencies
- `modbus_reference.md` - Complete Modbus register reference
- `.venv/` - Python virtual environment

## Notes

- Only device #1 can have parameters modified; this script only reads data
- The script reads from holding registers (function code 0x03)
- All temperature and pressure values are properly scaled
- Status flags are read as 16-bit integers (use bit masking to extract individual flags)
