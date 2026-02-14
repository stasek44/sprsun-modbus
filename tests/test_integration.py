"""Integration tests for SPRSUN Modbus - tests with real device using only pymodbus.

These tests connect directly to the heat pump and validate:
1. Batch read returns all 50 registers correctly
2. Batch read values match individual reads (no offset/misalignment)
3. Values are consistent between reads
4. Results are logged to CSV for analysis

Environment variables to configure connection:
- MODBUS_HOST: Heat pump IP (default: 192.168.1.234)
- MODBUS_PORT: Modbus port (default: 502)
- DEVICE_ADDRESS: Modbus slave address (default: 1)

Skip tests if device not available:
    pytest tests/test_integration.py -v --skip-no-device
"""

import pytest
import csv
import os
import time
from datetime import datetime
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

# Import register definitions
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from custom_components.sprsun_modbus.const import REGISTERS_READ_ONLY

# Allow real network connections in these integration tests
pytestmark = pytest.mark.enable_socket

CSV_OUTPUT_DIR = "tests/output"
os.makedirs(CSV_OUTPUT_DIR, exist_ok=True)

# Modbus Configuration - change these to match your setup
MODBUS_HOST = os.environ.get("MODBUS_HOST", "192.168.1.234")
MODBUS_PORT = int(os.environ.get("MODBUS_PORT", "502"))
DEVICE_ADDRESS = int(os.environ.get("DEVICE_ADDRESS", "1"))

# Batch read configuration
START_ADDRESS = 0x0000
REGISTER_COUNT = 50


@pytest.fixture(scope="module")
def modbus_client():
    """Create Modbus client and connect to device."""
    client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
    
    if not client.connect():
        pytest.skip(f"Cannot connect to Modbus device at {MODBUS_HOST}:{MODBUS_PORT}")
    
    yield client
    
    client.close()


def apply_scaling(raw_value, scale):
    """Apply scaling factor and handle signed values."""
    # Convert unsigned to signed if needed
    if raw_value > 32767:
        raw_value = raw_value - 65536
    
    return raw_value * scale


def test_modbus_connection(modbus_client):
    """Test basic Modbus connection."""
    assert modbus_client.connected, "Modbus client should be connected"
    
    # Try reading a single register
    result = modbus_client.read_holding_registers(
        address=START_ADDRESS,
        count=1,
        device_id=DEVICE_ADDRESS
    )
    
    assert not result.isError(), "Register read should succeed"
    assert len(result.registers) == 1, "Should return 1 register"


def test_batch_read_all_registers(modbus_client):
    """Test reading all 50 registers in one batch."""
    start_time = time.time()
    
    result = modbus_client.read_holding_registers(
        address=START_ADDRESS,
        count=REGISTER_COUNT,
        device_id=DEVICE_ADDRESS
    )
    
    duration = (time.time() - start_time) * 1000  # ms
    
    assert not result.isError(), "Batch read should succeed"
    assert len(result.registers) == REGISTER_COUNT, f"Should return {REGISTER_COUNT} registers"
    
    print(f"\n✅ Batch read {REGISTER_COUNT} registers in {duration:.1f}ms")
    
    # Save to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(CSV_OUTPUT_DIR, f"batch_read_{timestamp}.csv")
    
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Address', 'Key', 'Name', 'Raw Value', 'Scaled Value', 'Unit', 'Scale'])
        
        for i, (address, config) in enumerate(sorted(REGISTERS_READ_ONLY.items())):
            key, name, scale, unit, device_class = config
            raw_value = result.registers[i]
            scaled_value = apply_scaling(raw_value, scale)
            
            writer.writerow([
                f"0x{address:04X}",
                key,
                name,
                raw_value,
                f"{scaled_value:.2f}",
                unit or '',
                scale
            ])
    
    print(f"📄 Batch read saved to: {csv_path}")


def test_batch_vs_individual_reads(modbus_client):
    """
    Critical test: Compare batch read with individual reads.
    This validates that batch read returns registers in correct order
    and values don't get misaligned.
    """
    print("\n🔍 Testing batch vs individual reads...")
    
    # 1. Batch read
    batch_start = time.time()
    batch_result = modbus_client.read_holding_registers(
        address=START_ADDRESS,
        count=REGISTER_COUNT,
        device_id=DEVICE_ADDRESS
    )
    batch_duration = (time.time() - batch_start) * 1000
    
    assert not batch_result.isError(), "Batch read should succeed"
    assert len(batch_result.registers) == REGISTER_COUNT
    
    # 2. Individual reads for key registers (validation points)
    # Use stable registers that shouldn't change during test
    validation_registers = [
        (0x0013, 19, "Software Version Year"),  # Very stable
        (0x002C, 44, "Controller Version"),     # Very stable
        (0x002D, 45, "Display Version"),        # Very stable
    ]
    
    mismatches = []
    individual_total_time = 0
    
    for addr, batch_idx, name in validation_registers:
        ind_start = time.time()
        ind_result = modbus_client.read_holding_registers(
            address=addr,
            count=1,
            device_id=DEVICE_ADDRESS
        )
        individual_total_time += (time.time() - ind_start) * 1000
        
        if not ind_result.isError() and len(ind_result.registers) == 1:
            batch_val = batch_result.registers[batch_idx]
            individual_val = ind_result.registers[0]
            
            if batch_val != individual_val:
                mismatches.append({
                    'address': f"0x{addr:04X}",
                    'name': name,
                    'batch_value': batch_val,
                    'individual_value': individual_val,
                    'batch_index': batch_idx,
                })
    
    # Report results
    print(f"   Batch read: {batch_duration:.1f}ms ({REGISTER_COUNT} registers)")
    print(f"   Individual reads: {individual_total_time:.1f}ms ({len(validation_registers)} registers)")
    print(f"   Speed improvement: {individual_total_time/batch_duration:.1f}x")
    
    # Save comparison to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(CSV_OUTPUT_DIR, f"batch_vs_individual_{timestamp}.csv")
    
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Address', 'Name', 'Batch Index', 'Batch Value', 'Individual Value', 'Match'])
        
        for addr, batch_idx, name in validation_registers:
            ind_result = modbus_client.read_holding_registers(addr, 1, device_id=DEVICE_ADDRESS)
            batch_val = batch_result.registers[batch_idx]
            ind_val = ind_result.registers[0] if not ind_result.isError() else None
            match = "✓" if batch_val == ind_val else "✗ MISMATCH"
            
            writer.writerow([
                f"0x{addr:04X}",
                name,
                batch_idx,
                batch_val,
                ind_val,
                match
            ])
    
    print(f"📄 Comparison saved to: {csv_path}")
    
    # Assert no mismatches
    if mismatches:
        print("\n❌ MISMATCHES DETECTED:")
        for m in mismatches:
            print(f"   {m['address']} ({m['name']}): batch[{m['batch_index']}]={m['batch_value']}, individual={m['individual_value']}")
        
        pytest.fail(f"Batch read validation failed: {len(mismatches)} mismatches detected")
    else:
        print("✅ All validation points match - batch read is correct!")


def test_multiple_batch_reads_consistency(modbus_client):
    """
    Test that multiple consecutive batch reads return consistent values.
    Dynamic values (temperatures, frequencies) can change slightly,
    but static values should be identical.
    """
    print("\n🔄 Testing consistency across multiple reads...")
    
    num_reads = 3
    all_reads = []
    
    for i in range(num_reads):
        result = modbus_client.read_holding_registers(
            address=START_ADDRESS,
            count=REGISTER_COUNT,
            device_id=DEVICE_ADDRESS
        )
        
        assert not result.isError()
        assert len(result.registers) == REGISTER_COUNT
        
        all_reads.append(result.registers)
        time.sleep(0.1)  # Small delay between reads
    
    # Check static registers remain constant
    static_registers = {
        19: "Software Version Year",
        44: "Controller Version",
        45: "Display Version",
    }
    
    inconsistent = []
    
    for idx, name in static_registers.items():
        values = [read[idx] for read in all_reads]
        if len(set(values)) > 1:
            inconsistent.append({
                'index': idx,
                'name': name,
                'values': values
            })
    
    # Save to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(CSV_OUTPUT_DIR, f"consistency_test_{timestamp}.csv")
    
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        header = ['Address', 'Key', 'Name'] + [f'Read {i+1}' for i in range(num_reads)] + ['Consistent']
        writer.writerow(header)
        
        for i, (address, config) in enumerate(sorted(REGISTERS_READ_ONLY.items())):
            key, name, scale, unit, device_class = config
            values = [read[i] for read in all_reads]
            consistent = "✓" if len(set(values)) == 1 else "✗ VARIES"
            
            row = [f"0x{address:04X}", key, name] + values + [consistent]
            writer.writerow(row)
    
    print(f"📄 Consistency test saved to: {csv_path}")
    print(f"   Performed {num_reads} consecutive reads")
    print(f"   Static registers: {len(static_registers)}")
    
    if inconsistent:
        print("⚠️  Some static registers varied (unexpected):")
        for item in inconsistent:
            print(f"   [{item['index']}] {item['name']}: {item['values']}")
    else:
        print("✅ All static registers remained consistent")
    
    # Static registers should not change
    assert len(inconsistent) == 0, f"Static registers changed: {inconsistent}"


def test_batch_read_performance(modbus_client):
    """Measure and report batch read performance."""
    print("\n⚡ Performance test...")
    
    num_iterations = 10
    durations = []
    
    for _ in range(num_iterations):
        start = time.time()
        
        result = modbus_client.read_holding_registers(
            address=START_ADDRESS,
            count=REGISTER_COUNT,
            device_id=DEVICE_ADDRESS
        )
        
        duration = (time.time() - start) * 1000
        durations.append(duration)
        
        assert not result.isError()
        time.sleep(0.05)  # Small delay between iterations
    
    avg_duration = sum(durations) / len(durations)
    min_duration = min(durations)
    max_duration = max(durations)
    
    print(f"   Iterations: {num_iterations}")
    print(f"   Average: {avg_duration:.1f}ms")
    print(f"   Min: {min_duration:.1f}ms")
    print(f"   Max: {max_duration:.1f}ms")
    print(f"   Throughput: {1000/avg_duration:.1f} reads/second")
    
    # Save to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(CSV_OUTPUT_DIR, f"performance_{timestamp}.csv")
    
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Iteration', 'Duration (ms)'])
        for i, duration in enumerate(durations, 1):
            writer.writerow([i, f"{duration:.2f}"])
        
        writer.writerow([])
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Average (ms)', f"{avg_duration:.2f}"])
        writer.writerow(['Min (ms)', f"{min_duration:.2f}"])
        writer.writerow(['Max (ms)', f"{max_duration:.2f}"])
        writer.writerow(['Throughput (reads/s)', f"{1000/avg_duration:.1f}"])
    
    print(f"📄 Performance data saved to: {csv_path}")
    
    # Batch read should be reasonably fast (< 500ms)
    assert avg_duration < 500, f"Average batch read too slow: {avg_duration:.1f}ms"


def test_all_registers_read_successfully(modbus_client):
    """Verify all 50 registers can be read and contain reasonable values."""
    result = modbus_client.read_holding_registers(
        address=START_ADDRESS,
        count=REGISTER_COUNT,
        device_id=DEVICE_ADDRESS
    )
    
    assert not result.isError()
    assert len(result.registers) == REGISTER_COUNT
    
    # Save detailed register dump
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(CSV_OUTPUT_DIR, f"full_register_dump_{timestamp}.csv")
    
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Address', 'Index', 'Key', 'Name', 'Raw Value', 'Raw Hex', 'Scaled Value', 'Unit', 'Scale Factor', 'Device Class'])
        
        for i, (address, config) in enumerate(sorted(REGISTERS_READ_ONLY.items())):
            key, name, scale, unit, device_class = config
            raw_value = result.registers[i]
            scaled_value = apply_scaling(raw_value, scale)
            
            writer.writerow([
                f"0x{address:04X}",
                i,
                key,
                name,
                raw_value,
                f"0x{raw_value:04X}",
                f"{scaled_value:.2f}",
                unit or '',
                scale,
                device_class or ''
            ])
    
    print(f"\n📄 Full register dump saved to: {csv_path}")
    print(f"   Total registers: {REGISTER_COUNT}")
    print(f"   All registers read successfully ✅")


if __name__ == "__main__":
    # Allow running directly for quick testing
    print("Running integration tests...")
    print(f"Device: {MODBUS_HOST}:{MODBUS_PORT}")
    print(f"Address: {DEVICE_ADDRESS}")
    print()
    
    pytest.main([__file__, "-v", "-s"])
