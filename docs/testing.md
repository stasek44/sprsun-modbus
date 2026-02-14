# Testing Guide

## Overview

The SPRSUN Modbus integration includes comprehensive tests:

1. **Local Integration Tests** - Test batch read consistency with real device (standalone script, **no Home Assistant required**)
2. **Unit Tests** - Test individual components without hardware (use pytest)

## Quick Start

### Local Integration Tests (Recommended)

**Test with your real device - no pytest, no Home Assistant required:**

```bash
# Test with default IP (192.168.1.234)
python scripts/test_local.py

# Customize connection
MODBUS_HOST=192.168.1.100 python scripts/test_local.py
```

Expected output:
```
============================================================
SPRSUN Modbus Local Integration Tests
============================================================
Device: 192.168.1.234:502
Slave Address: 1
Registers: 50 (0x0000-0x0031)
============================================================

✅ PASSED: connection
✅ PASSED: batch_read
✅ PASSED: batch_vs_individual  ← KEY TEST!
✅ PASSED: consistency
✅ PASSED: performance

Results: 5/5 tests passed
CSV outputs saved to: tests/output/
```

## Local Integration Tests Details

### What Gets Tested

#### Test 1: Connection
- Verifies Modbus TCP connection
- Reads first register to validate communication

#### Test 2: Batch Read  
- Reads all 50 registers in one request (~160-200ms)
- Saves all values to CSV: `tests/output/batch_read_TIMESTAMP.csv`

#### Test 3: Batch vs Individual (CRITICAL)
- **This validates batch reading works correctly!**
- Compares batch read with individual register reads
- Tests stable registers (software version, controller version, display version)
- Saves comparison: `tests/output/batch_vs_individual_TIMESTAMP.csv`

Example output when working:
```csv
Address,Name,Batch Index,Batch Value,Individual Value,Match
0x0013,Software Version Year,19,8228,8228,✓ YES
0x002C,Controller Version,44,590,590,✓ YES
0x002D,Display Version,45,660,660,✓ YES
```

#### Test 4: Consistency
- Performs 3 consecutive batch reads
- Verifies static registers don't change
- Saves to: `tests/output/consistency_TIMESTAMP.csv`

#### Test 5: Performance
- Measures batch read time over 10 iterations  
- Expected: ~160-200ms per read
- Saves to: `tests/output/performance_TIMESTAMP.csv`

### CSV Output Files

All files in `tests/output/`:

- **batch_read_TIMESTAMP.csv** - Full register dump with scaled values
- **batch_vs_individual_TIMESTAMP.csv** - Validation results (key file!)
- **consistency_TIMESTAMP.csv** - Multiple reads comparison
- **performance_TIMESTAMP.csv** - Timing measurements

## Unit Tests (pytest)

```bash
#Activate virtual environment
source .venv/bin/activate

# Install dependencies if needed
pip install -r requirements_dev.txt

# Run all unit tests
pytest tests/ -v

# Run specific tests
pytest tests/test_const.py -v
pytest tests/test_sensor.py -v
pytest tests/test_binary_sensor.py -v

# With coverage
pytest tests/ --cov=custom_components/sprsun_modbus --cov-report=html
```

### Unit Test Files

- **test_const.py** (15 tests) - Register definitions
- **test_sensor.py** (8 tests) - Sensor entities
- **test_binary_sensor.py** (9 tests) - Binary sensor bit extraction
- **test_config_flow.py** (5 tests) - UI configuration flow

## Interpreting Results

### ✅ All Tests Passed

Your device is working correctly! Batch read returns accurate values.

### ❌ Connection Failed

```
❌ FATAL ERROR: Cannot connect to 192.168.1.234:502
```

Check:
- Device powered on
- IP address correct
- Network connectivity
- No firewall blocking port 502

### ❌ Batch vs Individual Mismatch

```
❌ FAILED: batch[19]=8228 != individual=8229
```

**This means batch reading has problems - values don't match!**

Possible causes:
- Device firmware bug
- Modbus gateway (Elfin W11) issue
- Network problems

Actions:
1. Run test multiple times
2. Update Elfin W11 firmware
3. Try Ethernet instead of WiFi
4. Report issue with device/firmware details

## Configuration

```bash
# Environment variables
export MODBUS_HOST=192.168.1.234  # Your device IP
export MODBUS_PORT=502             # Modbus port
export DEVICE_ADDRESS=1            # Slave address

python scripts/test_local.py
```

## Recommended Workflow

### Before Release
```bash
# Hardware validation
python scripts/test_local.py
```

Check:
- All 5 tests pass ✅
- `batch_vs_individual_*.csv` shows all `✓ YES`
- Performance < 500ms

### During Development
```bash
# Quick validation
pytest tests/test_const.py -v

# Full suite
pytest tests/ -v --cov
```

### On Real HA Installation
- Install integration
- Verify all 98 entities appear
- Test write operations
- Monitor for 24 hours

## Troubleshooting

### pytest-socket blocks connections

Use local tests instead:
```bash
python scripts/test_local.py  # No pytest, real sockets
```

### Home Assistant import errors

Install test dependencies:
```bash
pip install -r requirements_dev.txt
```

Or use local tests (no HA required).

## Getting Help

If tests fail:

1. Collect diagnostics:
   ```bash
   python scripts/test_local.py > test_results.txt 2>&1
   ```

2. Review CSV files in `tests/output/`

3. Create GitHub issue with:
   - Test output
   - CSV files (especially `batch_vs_individual_*.csv`)
   - Device model/firmware version
   - Network setup
