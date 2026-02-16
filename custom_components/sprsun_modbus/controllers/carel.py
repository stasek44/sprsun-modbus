"""CAREL controller implementation."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from . import ControllerBase

if TYPE_CHECKING:
    from pymodbus.client import ModbusTcpClient

_LOGGER = logging.getLogger(__name__)


class CarelController(ControllerBase):
    """CAREL controller (alternative SPRSUN controller)."""
    
    @property
    def name(self) -> str:
        """Return controller type name."""
        return "CAREL"
    
    @property
    def manufacturer(self) -> str:
        """Return controller manufacturer."""
        return "SPRSUN (CAREL Controller)"
    
    def read_all_registers(
        self, 
        client: ModbusTcpClient, 
        device_address: int,
        initial_read: bool = False
    ) -> dict:
        """Read all CAREL registers."""
        # TODO: Implement CAREL register reading
        # CAREL uses different address space (40001-based)
        # Reference: docs/CAREL_MODBUS_REFERENCE.md
        
        _LOGGER.warning("CAREL controller support is not yet implemented")
        return {}
    
    def write_register(
        self,
        client: ModbusTcpClient,
        device_address: int,
        address: int,
        value: int,
    ) -> bool:
        """Write a CAREL register."""
        # TODO: Implement CAREL register writing
        _LOGGER.warning("CAREL controller write not yet implemented")
        return False
    
    def get_platforms(self) -> list[str]:
        """Return supported platforms for CAREL."""
        # TODO: May differ from CHICO
        return ["sensor", "binary_sensor", "number", "select", "switch"]
    
    def get_device_info(self, entry_id: str) -> dict:
        """Return device info for CAREL controller."""
        return {
            "identifiers": {("sprsun_modbus", entry_id)},
            "name": "SPRSUN Heat Pump",
            "manufacturer": "SPRSUN",
            "model": "Heat Pump (CAREL Controller)",
        }
    
    @classmethod
    def detect(cls, client: ModbusTcpClient, device_address: int) -> bool:
        """
        Detect CAREL controller by reading signature registers.
        
        CAREL has version registers at different addresses (40326-40328).
        In Modbus holding register terms: 325-327 (0-based).
        """
        try:
            # Try to read CAREL version registers
            # GeneralMng.CurrVer.X/Y/Z at addresses 325-327
            result = client.read_holding_registers(
                address=325,
                count=3,
                device_id=device_address
            )
            
            if result.isError():
                return False
            
            # If we can read these, check if they look like version numbers
            if len(result.registers) == 3:
                ver_x = result.registers[0]
                ver_y = result.registers[1]
                ver_z = result.registers[2]
                
                # Version components should be reasonable (0-99)
                if 0 <= ver_x <= 99 and 0 <= ver_y <= 99 and 0 <= ver_z <= 99:
                    _LOGGER.info(
                        "CAREL controller detected (Version %d.%d.%d)",
                        ver_x, ver_y, ver_z
                    )
                    return True
        
        except Exception as err:
            _LOGGER.debug("CAREL detection failed: %s", err)
        
        return False
