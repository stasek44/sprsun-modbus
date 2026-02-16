"""Controller abstraction for different heat pump controller types."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pymodbus.client import ModbusTcpClient


class ControllerBase(ABC):
    """Base class for heat pump controllers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return controller type name."""
    
    @property
    @abstractmethod
    def manufacturer(self) -> str:
        """Return controller manufacturer."""
    
    @abstractmethod
    def read_all_registers(
        self, 
        client: ModbusTcpClient, 
        device_address: int,
        initial_read: bool = False
    ) -> dict:
        """
        Read all relevant registers from the device.
        
        Args:
            client: Modbus client
            device_address: Device address (1-247)
            initial_read: True if this is the first read (include RW registers)
            
        Returns:
            Dictionary of register values keyed by register name
        """
    
    @abstractmethod
    def write_register(
        self,
        client: ModbusTcpClient,
        device_address: int,
        address: int,
        value: int,
    ) -> bool:
        """
        Write a single register value.
        
        Args:
            client: Modbus client
            device_address: Device address
            address: Register address
            value: Value to write
            
        Returns:
            True if successful
        """
    
    @abstractmethod
    def get_platforms(self) -> list[str]:
        """Return list of supported platforms for this controller."""
    
    @abstractmethod
    def get_device_info(self, entry_id: str) -> dict:
        """Return device info dict for Home Assistant."""
    
    @classmethod
    @abstractmethod
    def detect(cls, client: ModbusTcpClient, device_address: int) -> bool:
        """
        Detect if this controller type is present.
        
        Args:
            client: Modbus client
            device_address: Device address to check
            
        Returns:
            True if this controller is detected
        """


def detect_controller_type(
    client: ModbusTcpClient, 
    device_address: int
) -> str | None:
    """
    Auto-detect controller type by reading identification registers.
    
    Args:
        client: Modbus client
        device_address: Device address
        
    Returns:
        Controller type string ("chico" or "carel") or None if detection failed
    """
    from .chico import ChicoController
    from .carel import CarelController
    
    # Try detection in order
    for controller_class in [ChicoController, CarelController]:
        try:
            if controller_class.detect(client, device_address):
                return controller_class().name.lower()
        except Exception:
            continue
    
    return None


def get_controller(controller_type: str) -> ControllerBase:
    """
    Get controller instance by type.
    
    Args:
        controller_type: Controller type string ("chico" or "carel")
        
    Returns:
        Controller instance
        
    Raises:
        ValueError: If controller type is unknown
    """
    from .chico import ChicoController
    from .carel import CarelController
    
    controllers = {
        "chico": ChicoController,
        "carel": CarelController,
    }
    
    controller_class = controllers.get(controller_type.lower())
    if controller_class is None:
        raise ValueError(f"Unknown controller type: {controller_type}")
    
    return controller_class()
