"""Unit tests for SPRSUN Heat Pump Modbus Integration."""
import sys
from pathlib import Path

# Add sprsun-modbus root to sys.path so custom_components can be imported
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Setup mocks if running outside Home Assistant test environment
from tests.mock_ha import setup_mocks
setup_mocks()
