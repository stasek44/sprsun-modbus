#!/usr/bin/env python3
"""
SPRSUN Heat Pump Modbus Batch Poller
Polls all read-only registers using batch reads and saves to CSV
Uses a single batch read for all 50 registers for optimal performance
"""

import csv
import time
from datetime import datetime, timedelta
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
import sys

# Modbus Configuration
MODBUS_HOST = "192.168.1.234"
MODBUS_PORT = 502
DEVICE_ADDRESS = 1
POLL_INTERVAL = 5  # seconds between polls

# Starting register address and count
START_ADDRESS = 0x0000
REGISTER_COUNT = 50  # 0x0000 to 0x0031 (50 registers)

# Register definitions with scaling factors (same as individual poller)
REGISTERS = {
    # System Status Registers
    0x0000: {"name": "Compressor Runtime", "scale": 1, "unit": ""},
    0x0001: {"name": "COP", "scale": 1, "unit": ""},
    0x0013: {"name": "Software Version (Year)", "scale": 1, "unit": ""},
    0x0014: {"name": "Software Version (Month/Day)", "scale": 1, "unit": ""},
    0x002C: {"name": "Controller Version", "scale": 1, "unit": ""},
    0x002D: {"name": "Display Version", "scale": 1, "unit": ""},
    
    # Input Status Flags
    0x0002: {"name": "Switching Input Symbol", "scale": 1, "unit": ""},
    
    # Working Status Mark
    0x0003: {"name": "Working Status Mark", "scale": 1, "unit": ""},
    
    # Output Status Flags
    0x0004: {"name": "Output Symbol 1", "scale": 1, "unit": ""},
    0x0005: {"name": "Output Symbol 2", "scale": 1, "unit": ""},
    0x0006: {"name": "Output Symbol 3", "scale": 1, "unit": ""},
    
    # Failure/Alarm Flags
    0x0007: {"name": "Failure Symbol 1", "scale": 1, "unit": ""},
    0x0008: {"name": "Failure Symbol 2", "scale": 1, "unit": ""},
    0x0009: {"name": "Failure Symbol 3", "scale": 1, "unit": ""},
    0x000A: {"name": "Failure Symbol 4", "scale": 1, "unit": ""},
    0x000B: {"name": "Failure Symbol 5", "scale": 1, "unit": ""},
    0x000C: {"name": "Failure Symbol 6", "scale": 1, "unit": ""},
    0x000D: {"name": "Failure Symbol 7", "scale": 1, "unit": ""},
    
    # Temperature Sensors
    0x000E: {"name": "Inlet temp.", "scale": 0.1, "unit": "°C"},
    0x000F: {"name": "Hotwater temp.", "scale": 0.1, "unit": "°C"},
    0x0010: {"name": "Reserved 0x0010", "scale": 1, "unit": ""},  # Undocumented register
    0x0011: {"name": "Ambi temp.", "scale": 0.5, "unit": "°C"},
    0x0012: {"name": "Outlet temp.", "scale": 0.1, "unit": "°C"},
    0x0015: {"name": "Suct gas temp.", "scale": 0.5, "unit": "°C"},
    0x0016: {"name": "Coil temp.", "scale": 0.5, "unit": "°C"},
    0x001B: {"name": "Exhaust temp.", "scale": 1, "unit": "°C"},
    0x0022: {"name": "Driving temp.", "scale": 0.5, "unit": "°C"},
    0x0028: {"name": "Evap. temp.", "scale": 0.1, "unit": "°C"},
    0x0029: {"name": "Cond. temp.", "scale": 0.1, "unit": "°C"},
    
    # System Measurements
    0x0017: {"name": "AC Voltage", "scale": 1, "unit": "W"},
    0x0018: {"name": "Pump Flow", "scale": 1, "unit": "m³/h"},
    0x0019: {"name": "Heating/Cooling Capacity", "scale": 1, "unit": "W"},
    0x001A: {"name": "AC Current", "scale": 1, "unit": "A"},
    0x001C: {"name": "EEV1 Step", "scale": 1, "unit": ""},
    0x001D: {"name": "EEV2 Step", "scale": 1, "unit": ""},
    0x001E: {"name": "Comp. Frequency", "scale": 1, "unit": "Hz"},
    0x0021: {"name": "DC Bus Voltage", "scale": 1, "unit": "V"},
    0x0023: {"name": "Comp. Current", "scale": 1, "unit": "A"},
    0x0024: {"name": "Target Frequency", "scale": 1, "unit": "Hz"},
    0x0026: {"name": "DC Fan 1 Speed", "scale": 1, "unit": ""},
    0x0027: {"name": "DC Fan 2 Speed", "scale": 1, "unit": ""},
    0x002E: {"name": "DC Pump Speed", "scale": 1, "unit": ""},
    0x002F: {"name": "Suct. Press", "scale": 0.1, "unit": "bar"},
    0x0030: {"name": "Disch. Press", "scale": 0.1, "unit": "bar"},
    0x0031: {"name": "DC Fan Target", "scale": 1, "unit": ""},
    
    # Inverter Status
    0x001F: {"name": "Frequency Conversion Failure 1", "scale": 1, "unit": ""},
    0x0020: {"name": "Frequency Conversion Failure 2", "scale": 1, "unit": ""},
    0x0025: {"name": "Smart Grid Status", "scale": 1, "unit": ""},
    0x002A: {"name": "Freq. Conversion Fault High", "scale": 1, "unit": ""},
    0x002B: {"name": "Freq. Conversion Fault Low", "scale": 1, "unit": ""},
}


def apply_scaling(raw_value, scale):
    """Apply scaling and signed conversion to raw register value"""
    # Handle signed values (convert from unsigned 16-bit to signed)
    if raw_value > 32767:
        raw_value = raw_value - 65536
    
    scaled_value = raw_value * scale
    return scaled_value


def read_register_individual(client, address):
    """Read a single holding register (fallback method)"""
    try:
        result = client.read_holding_registers(address, count=1, device_id=DEVICE_ADDRESS)
        if result.isError() or len(result.registers) == 0:
            return None
        
        raw_value = result.registers[0]
        register_info = REGISTERS.get(address, {"scale": 1})
        return apply_scaling(raw_value, register_info["scale"])
    except Exception as e:
        print(f"  Error reading register 0x{address:04X}: {e}")
        return None


def poll_all_registers_individual(client):
    """Fallback: Read registers individually (slower but more reliable)"""
    print("  ⚠️  Using individual read fallback")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {"Timestamp": timestamp}
    
    for address, info in sorted(REGISTERS.items()):
        value = read_register_individual(client, address)
        data[info["name"]] = value
        time.sleep(0.01)  # Small delay between reads
    
    return data, "individual"  # Return data and status


def validate_batch_read(client, batch_registers):
    """
    Validate that batch read returned correct registers by spot-checking stable values.
    Returns (is_valid, issues) tuple.
    """
    issues = []
    
    # Validation registers: These should be relatively stable
    # Using addresses that are unlikely to change rapidly
    validation_points = [
        (0x0013, 13, "Software Version (Year)"),      # Should be around 8228 (year 2022, version 28)
        (0x002C, 44, "Controller Version"),           # Firmware version - very stable
        (0x002D, 45, "Display Version"),              # Display firmware - very stable
    ]
    
    for addr, batch_idx, name in validation_points:
        # Read individual register
        result = client.read_holding_registers(addr, count=1, device_id=DEVICE_ADDRESS)
        if result.isError() or len(result.registers) == 0:
            continue  # Skip validation if individual read fails
        
        individual_val = result.registers[0]
        batch_val = batch_registers[batch_idx]
        
        # Check if values match (allowing for small timing differences in dynamic registers)
        if batch_val != individual_val:
            issues.append(f"0x{addr:04X} ({name}): batch={batch_val}, individual={individual_val}")
    
    is_valid = len(issues) == 0
    return is_valid, issues


def poll_all_registers_batch(client):
    """Read all registers in a single batch request with validation"""
    start_time = time.time()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        # Read all 50 registers in one batch
        result = client.read_holding_registers(
            START_ADDRESS, 
            count=REGISTER_COUNT, 
            device_id=DEVICE_ADDRESS
        )
        
        # Check if the batch read was successful
        if result.isError() or len(result.registers) != REGISTER_COUNT:
            print(f"  ⚠️  Batch read failed: got {len(result.registers) if hasattr(result, 'registers') else 0} registers, expected {REGISTER_COUNT}")
            return poll_all_registers_individual(client)
        
        # VALIDATION: Verify batch read returned correct registers
        is_valid, issues = validate_batch_read(client, result.registers)
        
        if not is_valid:
            print(f"  ⚠️  Batch read validation FAILED - register mapping incorrect!")
            for issue in issues:
                print(f"      {issue}")
            print(f"  ⚠️  Falling back to individual reads")
            data, _ = poll_all_registers_individual(client)
            return data, "validation_failed"
        
        # Process the batch results
        data = {"Timestamp": timestamp}
        
        for i, (address, info) in enumerate(sorted(REGISTERS.items())):
            raw_value = result.registers[i]
            scaled_value = apply_scaling(raw_value, info["scale"])
            data[info["name"]] = scaled_value
        
        read_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        print(f"  ✓ Batch read successful & validated in {read_time:.1f}ms")
        
        return data, "batch_validated"  # Return data and success status
        
    except ModbusException as e:
        print(f"  ⚠️  Batch read Modbus error: {e}")
        data, _ = poll_all_registers_individual(client)
        return data, "modbus_error"
    except Exception as e:
        print(f"  ⚠️  Batch read unexpected error: {e}")
        data, _ = poll_all_registers_individual(client)
        return data, "read_error"


def main():
    # Generate output filename with timestamp
    start_time = datetime.now()
    filename = f"sprsun_batch_data_{start_time.strftime('%Y%m%d_%H%M%S')}.csv"
    
    print(f"SPRSUN Heat Pump Modbus BATCH Poller")
    print(f"====================================")
    print(f"Host: {MODBUS_HOST}:{MODBUS_PORT}")
    print(f"Device Address: {DEVICE_ADDRESS}")
    print(f"Poll Interval: {POLL_INTERVAL} seconds")
    print(f"Batch Read: {REGISTER_COUNT} registers (0x{START_ADDRESS:04X}-0x{START_ADDRESS+REGISTER_COUNT-1:04X})")
    print(f"Duration: Continuous (Ctrl+C to stop)")
    print(f"Output File: {filename}")
    print(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Connect to Modbus device
    client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
    
    try:
        if not client.connect():
            print(f"ERROR: Failed to connect to {MODBUS_HOST}:{MODBUS_PORT}")
            sys.exit(1)
        
        print("Connected to Modbus device successfully")
        print()
        
        # Initialize CSV file
        fieldnames = ["Timestamp"] + [info["name"] for _, info in sorted(REGISTERS.items())]
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            poll_count = 0
            batch_success_count = 0
            validation_failure_count = 0
            other_failure_count = 0
            
            while True:  # Run forever until Ctrl+C
                poll_count += 1
                current_time = datetime.now()
                elapsed = current_time - start_time
                elapsed_str = f"{int(elapsed.total_seconds() // 3600):02d}:{int((elapsed.total_seconds() % 3600) // 60):02d}:{int(elapsed.total_seconds() % 60):02d}"
                
                print(f"Poll #{poll_count} - {current_time.strftime('%H:%M:%S')} (Elapsed: {elapsed_str})")
                
                # Read all registers using batch method
                poll_start = time.time()
                data, status = poll_all_registers_batch(client)
                poll_duration = (time.time() - poll_start) * 1000
                
                # Track success rate
                if status == "batch_validated":
                    batch_success_count += 1
                elif status == "validation_failed":
                    validation_failure_count += 1
                else:
                    other_failure_count += 1
                
                # Write to CSV
                writer.writerow(data)
                csvfile.flush()  # Ensure data is written immediately
                
                # Display some key values
                print(f"  Inlet Temp: {data.get('Inlet temp.', 'N/A')} °C")
                print(f"  Outlet Temp: {data.get('Outlet temp.', 'N/A')} °C")
                print(f"  Ambient Temp: {data.get('Ambi temp.', 'N/A')} °C")
                print(f"  Compressor Freq: {data.get('Comp. Frequency', 'N/A')} Hz")
                status = data.get('Working Status Mark', 0)
                if status is not None:
                    print(f"  Working Status: 0x{int(status):04X}" if isinstance(status, (int, float)) else f"  Working Status: {status}")
                else:
                    print(f"  Working Status: N/A")
                
                # Show statistics
                fallback_count = validation_failure_count + other_failure_count
                batch_rate = (batch_success_count / poll_count * 100) if poll_count > 0 else 0
                validation_fail_rate = (validation_failure_count / poll_count * 100) if poll_count > 0 else 0
                print(f"  Stats: Batch OK: {batch_success_count} | Validation Failed: {validation_failure_count} | Other Errors: {other_failure_count}")
                print(f"         Success Rate: {batch_rate:.1f}% | Validation Failure Rate: {validation_fail_rate:.1f}%")
                print()
                
                # Wait for next poll
                time.sleep(POLL_INTERVAL)
        
        print(f"\nPolling stopped!")
        print(f"Total polls: {poll_count}")
        print(f"Data saved to: {filename}")
        
    except KeyboardInterrupt:
        print("\n\nPolling interrupted by user")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()
        print("Modbus connection closed")


if __name__ == "__main__":
    main()
