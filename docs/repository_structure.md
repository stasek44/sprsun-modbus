# SPRSUN Modbus Integration - Repository Structure

## Repository Organization

```
sprsun-modbus/
├── .github/
│   └── workflows/
│       ├── validate.yaml     # HACS + Hassfest validation
│       └── tests.yaml        # Pytest CI
│
├── custom_components/
│   └── sprsun_modbus/
│       ├── __init__.py       # Coordinator, async setup
│       ├── binary_sensor.py  # 6 binary sensors (bit extraction)
│       ├── config_flow.py    # UI configuration + options
│       ├── const.py          # All register definitions
│       ├── manifest.json     # Integration metadata
│       ├── number.py         # 42 read-write parameters
│       ├── sensor.py         # 50 read-only sensors
│       ├── strings.json      # UI strings (English)
│       ├── switch.py         # (Disabled - too complex)
│       └── translations/
│           ├── en.json
│           └── pl.json
│
├── docs/
│   ├── installation.md          # Setup guide
│   ├── configuration.md         # Automations, dashboards
│   ├── batch_read_architecture.md  # Technical deep-dive
│   ├── testing.md               # How to run tests
│   └── images/                  # Screenshots (TODO)
│
├── examples/
│   ├── configuration.yaml       # Example configs
│   └── data/                    # Sample CSV outputs
│
├── scripts/
│   ├── modbus_debug_poller.py   # Debug tool (26 params)
│   ├── modbus_batch_poller.py   # Full batch poller
│   ├── modbus_full_poller.py    # Old full poller
│   ├── setup_dev.sh             # Dev environment setup
│   └── debug/                   # Old debug/test scripts
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures
│   ├── test_const.py            # Unit tests for constants
│   ├── test_config_flow.py      # Config flow tests
│   ├── test_sensor.py           # Sensor entity tests
│   ├── test_binary_sensor.py    # Binary sensor tests
│   ├── test_integration.py      # Full integration tests + CSV
│   └── output/                  # Test CSV outputs
│
├── .gitignore
├── hacs.json                    # HACS metadata
├── LICENSE                      # MIT License
├── pytest.ini                   # Pytest configuration
├── README.md                    # Main documentation
├── requirements.txt             # Runtime dependencies
├── requirements_dev.txt         # Development dependencies
│
├── BATCH_READ_EXPLANATION.md    # Batch read guide
├── ELFIN_SETTINGS.md            # Gateway timing
├── INTEGRATION_README.md        # Polish documentation
├── modbus_reference.md          # Register reference (processed)
└── modbus_reference_raw.md      # Original Modbus docs
```

## Key Files Explained

### Integration Core

| File | Purpose | Lines | Key Functions |
|------|---------|-------|---------------|
| `__init__.py` | Coordinator, data updates | ~160 | `_sync_update()`, batch reads |
| `const.py` | Register definitions | ~180 | 50+42 register maps |
| `config_flow.py` | UI setup | ~120 | Config + options flows |
| `sensor.py` | Read-only sensors | ~100 | 50 sensor entities |
| `binary_sensor.py` | Status flags | ~80 | 6 bit extractions |
| `number.py` | Read-write params | ~200 | 42 number entities |

### Documentation

| File | Audience | Contents |
|------|----------|----------|
| `README.md` | Users | Quick start, features |
| `docs/installation.md` | Users | Hardware + software setup |
| `docs/configuration.md` | Users | Automations, examples |
| `docs/batch_read_architecture.md` | Developers | Technical details |
| `INTEGRATION_README.md` | Polish users | Full guide (Polish) |

### Testing

| File | Type | Coverage |
|------|------|----------|
| `test_const.py` | Unit | Register validation |
| `test_sensor.py` | Unit | Sensor entities |
| `test_binary_sensor.py` | Unit | Binary sensors, bit logic |
| `test_config_flow.py` | Unit | UI configuration |
| `test_integration.py` | Integration | Full cycle + CSV output |

### Scripts

| File | Purpose | Usage |
|------|---------|-------|
| `modbus_debug_poller.py` | Debug 26 key params | `python scripts/modbus_debug_poller.py` |
| `modbus_batch_poller.py` | Test batch reads | Research script |
| `setup_dev.sh` | Dev environment | `./scripts/setup_dev.sh` |

## File Organization Principles

### 1. Standard HA Structure

Follows Home Assistant custom component conventions:
- `custom_components/DOMAIN/` - Integration code
- `manifest.json` - Metadata (version, deps)
- Config flow (no YAML config)
- Translations in `translations/`

### 2. Documentation Hierarchy

```
README.md           (Quick overview)
  ├── docs/installation.md    (Setup)
  ├── docs/configuration.md   (Usage)
  └── docs/batch_read_architecture.md (Technical)
```

### 3. Test Organization

```
tests/
  ├── conftest.py         (Shared fixtures)
  ├── test_*.py           (Unit tests per module)
  └── test_integration.py (Full integration)
```

### 4. Examples Separated

```
examples/
  ├── configuration.yaml  (Config examples)
  └── data/              (Sample outputs)
```

## Development Workflow

### 1. Setup

```bash
git clone https://github.com/stasek44/sprsun-modbus.git
cd sprsun-modbus
./scripts/setup_dev.sh
source .venv/bin/activate
```

### 2. Make Changes

Edit files in `custom_components/sprsun_modbus/`

### 3. Run Tests

```bash
pytest tests/ -v
```

### 4. Check Code Quality

```bash
black custom_components/
ruff check custom_components/
mypy custom_components/
```

### 5. Test Integration

```bash
# Copy to HA instance
scp -r custom_components/sprsun_modbus homeassistant@ha:/config/custom_components/

# Restart HA
# Check logs
```

## Maintenance

### Adding New Register

1. Update `const.py` - add to `REGISTERS_READ_ONLY` or `REGISTERS_NUMBER`
2. Update `test_const.py` - add test case
3. Update `docs/` - document new entity
4. Update `INTEGRATION_README.md` - Polish docs
5. Run tests: `pytest tests/test_const.py -v`

### Adding New Feature

1. Create feature branch
2. Implement in `custom_components/sprsun_modbus/`
3. Add unit tests in `tests/`
4. Update documentation
5. Run full test suite
6. Create PR

## CI/CD

### GitHub Actions

- **Validate**: Runs on every push/PR
  - HACS validation
  - Hassfest validation

- **Tests**: Runs on push to main
  - pytest on Python 3.11, 3.12
  - Coverage report to Codecov

### Pre-commit Hooks (Optional)

```bash
pre-commit install
```

Runs before each commit:
- Black formatting
- Ruff linting
- Trailing whitespace removal
- YAML validation

## Dependencies

### Runtime (`requirements.txt`)

```
pymodbus==3.12.0
```

### Development (`requirements_dev.txt`)

```
pytest>=7.4.0
pytest-cov
pytest-asyncio
pytest-homeassistant-custom-component
homeassistant>=2024.1.0
black, ruff, mypy
```

## License

MIT License - see [LICENSE](../LICENSE)

## Contributing

See [README.md](../README.md#contributing) for contribution guidelines.
