# SPRSUN Heat Pump Modbus Integration for Home Assistant

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/stasek44/sprsun-modbus.svg)](https://github.com/stasek44/sprsun-modbus/releases)
[![License](https://img.shields.io/github/license/stasek44/sprsun-modbus.svg)](LICENSE)

Home Assistant integration for SPRSUN heat pumps via Modbus TCP (using Elfin-EW11/W11 gateway).

## Features

- **98 Entities**: 50 read-only sensors + 42 read-write number entities + 6 binary sensors
- **Batch Reading**: All read-only parameters in ONE request (~200ms) for optimal performance
- **Real-time Monitoring**: Temperature, pressure, power, COP, status flags
- **Remote Control**: Adjust operating modes, setpoints, economic mode parameters
- **Energy Dashboard**: Power sensors compatible with HA Energy
- **Reliable**: Batch read validation tests ensure data consistency

## Quick Start

### Installation

#### Via HACS (Recommended)
1. Add custom repository: `stasek44/sprsun-modbus`
2. Install "SPRSUN Modbus"
3. Restart Home Assistant

#### Manual Installation
```bash
cd /config/custom_components/
git clone https://github.com/stasek44/sprsun-modbus.git sprsun_modbus
# Restart Home Assistant
```

### Configuration

1. **Settings** → **Devices & Services** → **Add Integration**
2. Search for "SPRSUN"
3. Enter:
   - **Host**: Elfin W11 IP (e.g., 192.168.1.234)
   - **Port**: 502
   - **Device Address**: 1
   - **Name**: My Heat Pump

### Hardware Setup

Connect RS485 from heat pump to Elfin-EW11/W11:
- **A/+** → Terminal A
- **B/-** → Terminal B  
- **GND** → GND (recommended)

Configure Elfin W11 at http://192.168.1.234:
- Mode: TCP Server
- Baud: 9600, 8N1
- Timeout: 30s

[See full installation guide →](docs/installation.md)

## Entities

### Sensors (50 read-only)
- **Temperatures**: Inlet, outlet, hotwater, ambient, evaporator, condenser, coil, etc.
- **Pressures**: Suction, discharge
- **Power**: Heating/cooling capacity, AC voltage/current
- **Status**: COP, compressor runtime, frequencies, fan speeds
- **Diagnostics**: Software versions, failure symbols

### Number Entities (42 read-write)
- **Operating Modes**: Unit mode, fan mode
- **Setpoints**: Heating, cooling, DHW temperatures
- **Temperature Differentials**: Heating, DHW
- **Economic Mode**: 4 ambient temps + 4 water temps for heating/cooling
- **Antilegionella**: Temperature, schedule (weekday, start/end hour)

### Binary Sensors (6)
- Heating mode active
- Cooling mode active  
- DHW mode active
- Silent mode active
- Extra hot water
- Compressor running

## Testing

### Local Hardware Test (No Home Assistant Required)

```bash
# Test batch read consistency with your device
python scripts/test_local.py

# Customize connection
MODBUS_HOST=192.168.1.100 python scripts/test_local.py
```

Expected output:
```
✅ PASSED: connection
✅ PASSED: batch_read  (50 registers in ~200ms)
✅ PASSED: batch_vs_individual  ← Validates no value mismatches
✅ PASSED: consistency
✅ PASSED: performance

Results: 5/5 tests passed
CSV outputs saved to: tests/output/
```

**Key test**: `batch_vs_individual` - validates batch read returns identical values to individual reads (no offset/misalignment).

[See full testing guide →](docs/testing.md)

### Unit Tests

```bash
pip install -r requirements_dev.txt
pytest tests/ -v --cov
```

## Performance

- **Read-Only (50 registers)**: ONE batch request ~200ms
- **Binary Sensors (6 bits)**: ONE register read ~50ms  
- **Total per scan**: 2 requests ~250ms
- **RW Parameters (42)**: Read individually at startup only (~4200ms once)

Network efficiency: **16x faster** than individual reads (250ms vs 4000ms)

[See architecture details →](docs/batch_read_architecture.md)

## Configuration Examples

### Lovelace Dashboard

```yaml
type: entities
entities:
  - entity: sensor.sprsun_inlet_temp
  - entity: sensor.sprsun_outlet_temp
  - entity: sensor.sprsun_hotwater_temp
  - entity: sensor.sprsun_cop
  - entity: sensor.sprsun_heating_capacity
  - entity: binary_sensor.sprsun_heating_mode
```

### Automations

```yaml
# Low COP Alert
automation:
  - alias: "Heat Pump Low COP Warning"
    trigger:
      - platform: numeric_state
        entity_id: sensor.sprsun_cop
        below: 2.0
    action:
      - service: notify.mobile_app
        data:
          message: "Heat pump COP dropped to {{ states('sensor.sprsun_cop') }}"
```

[See more examples →](docs/configuration.md)

## Documentation

- [Installation Guide](docs/installation.md) - Hardware setup, Elfin W11 config
- [Configuration Guide](docs/configuration.md) - Lovelace, automations, templates
- [Batch Read Architecture](docs/batch_read_architecture.md) - Technical deep-dive
- [Testing Guide](docs/testing.md) - Local tests, unit tests, validation
- [Repository Structure](docs/repository_structure.md) - File organization

## Troubleshooting

### Connection Issues

```bash
# Test Modbus connection
telnet 192.168.1.234 502

# Run diagnostics
python scripts/test_local.py
```

### Batch Read Validation Failed

If `batch_vs_individual` test fails (values mismatch):
1. Update Elfin W11 firmware
2. Try Ethernet instead of WiFi
3. Check for other Modbus tools polling device

### Values Not Updating

Check:
- Scan interval in integration options (default: 30s)
- Home Assistant logs for errors
- Elfin W11 web interface shows active connection

## Known Limitations

- **RW Parameters**: Use individual connections (not batch read)
  - Reason: Sparse addresses (0x0036, 0x00C6-CC, 0x0169-019E)
  - Impact: Minimal (only read at startup)
- **Switch Platform**: Not implemented (bitfield complexity)
- **Climate Entity**: Not implemented (use number entities + automations)

## Contributing

Pull requests welcome!

1. Fork the repository
2. Create feature branch
3. Run tests: `pytest tests/ -v` and `python scripts/test_local.py`
4. Submit PR

## License

MIT License - see [LICENSE](LICENSE)

## Author

[@stasek44](https://github.com/stasek44)

## Acknowledgments

- SPRSUN heat pump Modbus reference documentation
- Elfin-EW11/W11 RS485 to WiFi gateway
- Home Assistant community

## Support

- **Issues**: [GitHub Issues](https://github.com/stasek44/sprsun-modbus/issues)
- **Discussions**: [GitHub Discussions](https://github.com/stasek44/sprsun-modbus/discussions)

---

**⭐ If this integration works for you, consider starring the repository!**
