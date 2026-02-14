#!/usr/bin/env python3
"""
Standalone local test script - NO pytest required. 
Tests batch read consistency directly with pymodbus.

Run: python scripts/test_local.py
"""

import csv
import os
import time
from datetime import datetime
from pymodbus.client import ModbusTcpClient

# Import register definitions
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from custom_components.sprsun_modbus.const import REGISTERS_READ_ONLY

# Configuration
MODBUS_HOST = os.environ.get("MODBUS_HOST", "192.168.1.234")
MODBUS_PORT = int(os.environ.get("MODBUS_PORT", "502"))
DEVICE_ADDRESS = int(os.environ.get("DEVICE_ADDRESS", "1"))

START_ADDRESS = 0x0000
REGISTER_COUNT = 50

CSV_OUTPUT_DIR = "tests/output"
os.makedirs(CSV_OUTPUT_DIR, exist_ok=True)


def apply_scaling(raw_value, scale):
    """Apply scaling factor and handle signed values."""
    if raw_value > 32767:
        raw_value = raw_value - 65536
    return raw_value * scale


def test_connection(client):
    """Test 1: Basic connection."""
    print("\n📝 Test 1: Connection Test")
    print("=" * 60)
    
    result = client.read_holding_registers(
        address=START_ADDRESS,
        count=1,
        device_id=DEVICE_ADDRESS
    )
    
    if result.isError():
        print("❌ FAILED: Cannot read register")
        return False
    
    print(f"✅ PASSED: Connected to {MODBUS_HOST}:{MODBUS_PORT}")
    print(f"   First register (0x{START_ADDRESS:04X}): {result.registers[0]}")
    return True


def test_batch_read(client):
    """Test 2: Batch read all 50 registers."""
    print("\n📝 Test 2: Batch Read Test")
    print("=" * 60)
    
    start_time = time.time()
    result = client.read_holding_registers(
        address=START_ADDRESS,
        count=REGISTER_COUNT,
        device_id=DEVICE_ADDRESS
    )
    duration = (time.time() - start_time) * 1000
    
    if result.isError():
        print("❌ FAILED: Batch read error")
        return False, None
    
    if len(result.registers) != REGISTER_COUNT:
        print(f"❌ FAILED: Expected {REGISTER_COUNT} registers, got {len(result.registers)}")
        return False, None
    
    print(f"✅ PASSED: Read {REGISTER_COUNT} registers in {duration:.1f}ms")
    
    # Save to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(CSV_OUTPUT_DIR, f"batch_read_{timestamp}.csv")
    
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Address', 'Index', 'Key', 'Name', 'Raw Value', 'Hex', 'Scaled Value', 'Unit', 'Scale'])
        
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
                scale
            ])
    
    print(f"📄 Saved to: {csv_path}")
    return True, result.registers


def test_batch_vs_individual(client, batch_registers):
    """Test 3: Compare batch read vs individual reads (CRITICAL TEST)."""
    print("\n📝 Test 3: Batch vs Individual Consistency")
    print("=" * 60)
    
    # Test stable registers (should not change)
    validation_points = [
        (0x0013, 19, "Software Version Year"),
        (0x002C, 44, "Controller Version"),
        (0x002D, 45, "Display Version"),
    ]
    
    mismatches = []
    batch_time = 0
    individual_time = 0
    
    # Re-read batch for fair comparison
    batch_start = time.time()
    batch_result = client.read_holding_registers(address=START_ADDRESS, count=REGISTER_COUNT, device_id=DEVICE_ADDRESS)
    batch_time = (time.time() - batch_start) * 1000
    
    if batch_result.isError():
        print("❌ FAILED: Batch read error")
        return False
    
    print(f"   Batch read: {batch_time:.1f}ms ({REGISTER_COUNT} registers)")
    
    # Individual reads
    for addr, batch_idx, name in validation_points:
        ind_start = time.time()
        ind_result = client.read_holding_registers(address=addr, count=1, device_id=DEVICE_ADDRESS)
        individual_time += (time.time() - ind_start) * 1000
        
        if not ind_result.isError():
            batch_val = batch_result.registers[batch_idx]
            individual_val = ind_result.registers[0]
            
            if batch_val != individual_val:
                mismatches.append({
                    'address': f"0x{addr:04X}",
                    'name': name,
                    'batch_index': batch_idx,
                    'batch_value': batch_val,
                    'individual_value': individual_val
                })
    
    print(f"   Individual reads: {individual_time:.1f}ms ({len(validation_points)} registers)")
    print(f"   Speed improvement: {individual_time/batch_time:.1f}x")
    
    # Save comparison
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(CSV_OUTPUT_DIR, f"batch_vs_individual_{timestamp}.csv")
    
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Address', 'Name', 'Batch Index', 'Batch Value', 'Individual Value', 'Match'])
        
        for addr, batch_idx, name in validation_points:
            ind_result = client.read_holding_registers(address=addr, count=1, device_id=DEVICE_ADDRESS)
            batch_val = batch_result.registers[batch_idx]
            ind_val = ind_result.registers[0] if not ind_result.isError() else None
            match = "✓ YES" if batch_val == ind_val else "✗ MISMATCH"
            
            writer.writerow([
                f"0x{addr:04X}",
                name,
                batch_idx,
                batch_val,
                ind_val,
                match
            ])
    
    print(f"📄 Saved to: {csv_path}")
    
    if mismatches:
        print(f"\n❌ FAILED: {len(mismatches)} mismatches detected!")
        for m in mismatches:
            print(f"   {m['address']} ({m['name']}): batch[{m['batch_index']}]={m['batch_value']} != individual={m['individual_value']}")
        return False
    else:
        print("✅ PASSED: All validation points match!")
        return True


def test_consistency(client):
    """Test 4: Multiple reads consistency."""
    print("\n📝 Test 4: Multiple Reads Consistency")
    print("=" * 60)
    
    num_reads = 3
    all_reads = []
    
    for i in range(num_reads):
        result = client.read_holding_registers(address=START_ADDRESS, count=REGISTER_COUNT, device_id=DEVICE_ADDRESS)
        if result.isError():
            print(f"❌ FAILED: Read {i+1} failed")
            return False
        all_reads.append(result.registers)
        time.sleep(0.1)
    
    # Check static registers
    static_registers = {
        19: "Software Version Year",
        44: "Controller Version",
        45: "Display Version",
    }
    
    inconsistent = []
    for idx, name in static_registers.items():
        values = [read[idx] for read in all_reads]
        if len(set(values)) > 1:
            inconsistent.append({'index': idx, 'name': name, 'values': values})
    
    # Save to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(CSV_OUTPUT_DIR, f"consistency_{timestamp}.csv")
    
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        header = ['Address', 'Key', 'Name'] + [f'Read {i+1}' for i in range(num_reads)] + ['Consistent']
        writer.writerow(header)
        
        for i, (address, config) in enumerate(sorted(REGISTERS_READ_ONLY.items())):
            key, name, scale, unit, device_class = config
            values = [read[i] for read in all_reads]
            consistent = "✓" if len(set(values)) == 1 else "✗"
            
            row = [f"0x{address:04X}", key, name] + values + [consistent]
            writer.writerow(row)
    
    print(f"📄 Saved to: {csv_path}")
    print(f"   Performed {num_reads} consecutive reads")
    
    if inconsistent:
        print(f"⚠️  WARNING: {len(inconsistent)} static registers varied:")
        for item in inconsistent:
            print(f"   [{item['index']}] {item['name']}: {item['values']}")
        return False
    else:
        print("✅ PASSED: All static registers consistent")
        return True


def test_performance(client):
    """Test 5: Performance measurement."""
    print("\n📝 Test 5: Performance Test")
    print("=" * 60)
    
    num_iterations = 10
    durations = []
    
    for _ in range(num_iterations):
        start = time.time()
        result = client.read_holding_registers(address=START_ADDRESS, count=REGISTER_COUNT, device_id=DEVICE_ADDRESS)
        duration = (time.time() - start) * 1000
        
        if result.isError():
            print("❌ FAILED: Read error during performance test")
            return False
        
        durations.append(duration)
        time.sleep(0.05)
    
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
    
    print(f"📄 Saved to: {csv_path}")
    
    if avg_duration < 500:
        print("✅ PASSED: Performance acceptable")
        return True
    else:
        print(f"⚠️  WARNING: Performance slow ({avg_duration:.1f}ms > 500ms)")
        return True  # Don't fail on performance


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("SPRSUN Modbus Local Integration Tests")
    print("=" * 60)
    print(f"Device: {MODBUS_HOST}:{MODBUS_PORT}")
    print(f"Slave Address: {DEVICE_ADDRESS}")
    print(f"Registers: {REGISTER_COUNT} (0x{START_ADDRESS:04X}-0x{START_ADDRESS+REGISTER_COUNT-1:04X})")
    print(f"Output: {CSV_OUTPUT_DIR}/")
    print("=" * 60)
    
    # Connect
    client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
    
    if not client.connect():
        print(f"\n❌ FATAL ERROR: Cannot connect to {MODBUS_HOST}:{MODBUS_PORT}")
        print("   Check:")
        print("   - Device is powered on")
        print("   - IP address is correct")
        print("   - Network connection")
        print("   - Firewall settings")
        return 1
    
    print(f"\n🔌 Connected to {MODBUS_HOST}:{MODBUS_PORT}")
    
    # Run tests
    results = {}
    
    try:
        results['connection'] = test_connection(client)
        
        passed, batch_regs = test_batch_read(client)
        results['batch_read'] = passed
        
        if batch_regs:
            results['batch_vs_individual'] = test_batch_vs_individual(client, batch_regs)
        
        results['consistency'] = test_consistency(client)
        results['performance'] = test_performance(client)
        
    finally:
        client.close()
        print("\n🔌 Disconnected")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print(f"CSV outputs saved to: {CSV_OUTPUT_DIR}/")
    print("=" * 60)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    exit(main())
