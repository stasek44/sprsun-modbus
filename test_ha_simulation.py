#!/usr/bin/env python3
"""
Simulate Home Assistant data fetching to debug register reading issues.
Mimics exactly what HA does: batch read 0x0000-0x0031 with proper scaling.
Dumps results to CSV for analysis.

IMPORTANT: This version properly handles SIGNED int16 for temperature registers
that can go negative (ambient, suction gas, coil, driving, evaporation temps).
"""
import time
import csv
from datetime import datetime
from pymodbus.client import ModbusTcpClient

# Configuration
HOST = "192.168.1.234"
PORT = 502
DEVICE_ADDRESS = 1
SCAN_INTERVAL = 10  # seconds
TEST_DURATION = 3600  # 1 hour (adjust as needed)

# Register definitions - EXACTLY as HA uses them
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
    
    # Temperature Sensors (NOTE: Some are SIGNED int16 for negative temps)
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


def fetch_data_like_ha(client):
    """Fetch data EXACTLY like Home Assistant does."""
    data = {}
    
    # Registers that should be interpreted as signed int16 (negative temperatures)
    SIGNED_REGISTERS = {
        0x0011,  # ambient_temp
        0x0015,  # suction_gas_temp
        0x0016,  # coil_temp
        0x0022,  # driving_temp
        0x0028,  # evap_temp
    }
    
    # Read all read-only registers in one batch (0x0000-0x0031 = 50 registers)
    # This is EXACTLY what HA's coordinator does
    try:
        result = client.read_holding_registers(
            address=0x0000,
            count=50,
            device_id=DEVICE_ADDRESS
        )
        
        if result.isError():
            print(f"ERROR: Modbus read error: {result}")
            return None
        
        # Parse registers with EXACT same logic as HA
        for address, (key, name, scale, unit, device_class) in REGISTERS_READ_ONLY.items():
            index = address - 0x0000
            if index < len(result.registers):
                raw_value = result.registers[index]
                
                # Convert to signed int16 if needed
                if address in SIGNED_REGISTERS:
                    if raw_value > 32767:
                        raw_value = raw_value - 65536
                
                scaled_value = raw_value * scale
                data[key] = {
                    'name': name,
                    'raw': raw_value,
                    'scaled': scaled_value,
                    'unit': unit,
                    'scale': scale
                }
        
        return data
        
    except Exception as err:
        print(f"ERROR: Exception during read: {err}")
        return None


def main():
    """Run simulation."""
    print(f"Starting HA simulation test")
    print(f"Host: {HOST}:{PORT}")
    print(f"Device Address: {DEVICE_ADDRESS}")
    print(f"Scan Interval: {SCAN_INTERVAL}s")
    print(f"Test Duration: {TEST_DURATION}s ({TEST_DURATION//60} minutes)")
    print(f"Output: ha_simulation_data.csv")
    print("-" * 80)
    
    # Create CSV file
    csv_filename = f"ha_simulation_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    # Prepare CSV headers
    headers = ['timestamp', 'iteration']
    for address in sorted(REGISTERS_READ_ONLY.keys()):
        key, name, scale, unit, _ = REGISTERS_READ_ONLY[address]
        headers.append(f"{key}_raw")
        headers.append(f"{key}_scaled")
    
    client = ModbusTcpClient(host=HOST, port=PORT, timeout=30)
    
    try:
        # Connect
        if not client.connect():
            print("FAILED to connect to Modbus device!")
            return
        
        print("Connected successfully!")
        print()
        
        with open(csv_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            
            iteration = 0
            start_time = time.time()
            
            while True:
                iteration += 1
                elapsed = time.time() - start_time
                
                if elapsed > TEST_DURATION:
                    print("\nTest duration reached. Stopping.")
                    break
                
                print(f"[{iteration}] Fetching data... ", end='', flush=True)
                
                data = fetch_data_like_ha(client)
                
                if data:
                    # Build CSV row
                    timestamp = datetime.now().isoformat()
                    row = [timestamp, iteration]
                    
                    for address in sorted(REGISTERS_READ_ONLY.keys()):
                        key, name, scale, unit, _ = REGISTERS_READ_ONLY[address]
                        if key in data:
                            row.append(data[key]['raw'])
                            row.append(data[key]['scaled'])
                        else:
                            row.append('')
                            row.append('')
                    
                    writer.writerow(row)
                    csvfile.flush()  # Ensure data is written
                    
                    # Print interesting values
                    print(f"OK - ", end='')
                    if 'suction_gas_temp' in data:
                        print(f"Suction Gas: {data['suction_gas_temp']['scaled']:.1f}°C (raw: {data['suction_gas_temp']['raw']}), ", end='')
                    if 'inlet_temp' in data:
                        print(f"Inlet: {data['inlet_temp']['scaled']:.1f}°C, ", end='')
                    if 'outlet_temp' in data:
                        print(f"Outlet: {data['outlet_temp']['scaled']:.1f}°C", end='')
                    print()
                else:
                    print("FAILED")
                
                # Wait for next scan
                time.sleep(SCAN_INTERVAL)
        
        print(f"\nData saved to: {csv_filename}")
        print(f"Total iterations: {iteration}")
        
    finally:
        client.close()
        print("Disconnected.")


if __name__ == "__main__":
    main()
