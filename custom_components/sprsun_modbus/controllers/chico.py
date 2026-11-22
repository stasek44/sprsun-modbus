"""CHICO controller implementation."""
from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from . import ControllerBase

if TYPE_CHECKING:
    from pymodbus.client import ModbusTcpClient

_LOGGER = logging.getLogger(__name__)


class ChicoController(ControllerBase):
    """CHICO controller (original SPRSUN controller)."""
    
    @property
    def name(self) -> str:
        """Return controller type name."""
        return "CHICO"
    
    @property
    def manufacturer(self) -> str:
        """Return controller manufacturer."""
        return "SPRSUN (CHICO Controller)"
    
    def read_all_registers(
        self, 
        client: ModbusTcpClient, 
        device_address: int,
        initial_read: bool = False
    ) -> dict:
        """Read all CHICO registers."""
        from ..const import (
            REGISTERS_READ_ONLY,
            REGISTERS_NUMBER,
            REGISTERS_SELECT,
            REGISTERS_SWITCH,
        )
        
        data = {}
        
        # Registers that should be interpreted as signed int16
        SIGNED_REGISTERS = {
            0x0011,  # ambient_temp
            0x0015,  # suction_gas_temp
            0x0016,  # coil_temp
            0x001A,  # ac_current (0xFFFF = -1A ADC noise around 0)
            0x0022,  # driving_temp
            0x0023,  # compressor_current (ADC noise around 0)
            0x0028,  # evap_temp
        }
        SIGNED_RW_REGISTERS = {
            0x0169, 0x016A, 0x016B, 0x016C,  # E01-E04
            0x016D, 0x016E, 0x016F, 0x0170,  # E05-E08
            0x0171, 0x0172, 0x0173, 0x0174,  # E09-E12
            0x0183, 0x0184, 0x0192,  # G05, G07, G10
        }
        
        # Read all read-only registers in one batch (0x0000-0x0031 = 50 registers)
        try:
            result = client.read_holding_registers(
                address=0x0000,
                count=50,
                device_id=device_address
            )
            
            if result.isError():
                raise ValueError(f"Modbus read error: {result}")
            
            if not result.registers or len(result.registers) < 50:
                raise ValueError(
                    f"Modbus read error: expected 50 registers, got {len(result.registers) if result.registers else 0}"
                )
            
            # Sanity check: detect corrupt zero-filled frames from RS485 gateway
            # In a live heat pump, controller_version (0x002C, index 44) is non-zero (e.g. 590),
            # and water temperatures (inlet, hotwater, outlet) are never simultaneously zero.
            is_all_zeros = not any(result.registers)
            controller_ver = result.registers[0x002C] if len(result.registers) > 0x002C else 0
            water_temps_zero = (
                result.registers[0x000E] == 0  # inlet_temp
                and result.registers[0x000F] == 0  # hotwater_temp
                and result.registers[0x0012] == 0  # outlet_temp
            )
            
            if is_all_zeros or (controller_ver == 0 and water_temps_zero):
                raise ValueError(
                    f"Corrupt Modbus frame detected: all registers zero or key parameters invalid "
                    f"(all_zeros={is_all_zeros}, controller_version={controller_ver}, "
                    f"inlet={result.registers[0x000E]}, hotwater={result.registers[0x000F]}). Discarding."
                )
            
            # Parse read-only registers
            for address, (key, name, scale, unit, device_class) in REGISTERS_READ_ONLY.items():
                index = address - 0x0000
                if index < len(result.registers):
                    raw_value = result.registers[index]
                    
                    # Convert to signed int16 if needed
                    if address in SIGNED_REGISTERS:
                        if raw_value > 32767:
                            raw_value = raw_value - 65536
                    
                    # For current sensors, clamp small negative noise values to 0
                    if key in ("ac_current", "compressor_current") and raw_value < 0:
                        raw_value = 0
                    
                    data[key] = raw_value * scale
            
            _LOGGER.debug("CHICO: Read %d read-only registers", len(data))
            
        except Exception as err:
            _LOGGER.debug("CHICO: Error reading RO registers: %s", err)
            raise
        
        # Read status registers for binary sensors
        status_register_map = {
            0x0002: "switching_input_symbol",
            0x0003: "working_status_register",
            0x0004: "output_symbol_1",
            0x0005: "output_symbol_2",
            0x0006: "output_symbol_3",
            0x0007: "failure_symbol_1",
            0x0008: "failure_symbol_2",
            0x0009: "failure_symbol_3",
            0x000A: "failure_symbol_4",
            0x000B: "failure_symbol_5",
            0x000C: "failure_symbol_6",
            0x000D: "failure_symbol_7",
        }
        
        for address, key in status_register_map.items():
            index = address - 0x0000
            if index < len(result.registers):
                data[key] = result.registers[index]
        
        # Read RW registers (Phase 6: Batch RW reading for performance)
        if initial_read:
            _LOGGER.debug("CHICO: Reading RW registers in batches...")
            
            # Build address-to-config mapping for all RW registers
            rw_config = {}
            for addr, config in REGISTERS_NUMBER.items():
                key, name, scale, *_ = config
                rw_config[addr] = (key, scale)
            for addr, (key, name, options) in REGISTERS_SELECT.items():
                rw_config[addr] = (key, 1)
            
            # Add switch registers (control marks)
            for key, (addr, bit, name, icon) in REGISTERS_SWITCH.items():
                # Switch entities share registers, create unique key for each register
                reg_key = f"_control_{addr:04x}"
                if addr not in rw_config:
                    rw_config[addr] = (reg_key, 1)
            
            # Define optimized RW register batches
            # Each batch covers contiguous registers physically readable in Chico controller
            rw_batches = [
                # Batch 1: Control marks + P06 Unit mode (0x0032-0x0036) - Power switch, Reset, Antilegionella/G01, P06
                (0x0032, 5, "Control Marks + Unit Mode (0x0032-0x0036)"),
                
                # Batch 2: P parameters setpoints (0x00C6-0x00CC) - P03, P05, P04, P02, P01
                (0x00C6, 7, "P Parameters Setpoints (0x00C6-0x00CC)"),
                
                # Batch 3: Economic curves & general settings (0x0169-0x0185) - E01-E24 + G08, G06, G07, G05, G03
                (0x0169, 29, "Economic Curves E01-E24 + General Settings (0x0169-0x0185)"),
                
                # Batch 4: G04 DC Pump + P07 Fan mode & G09-G11 Mode control (0x018D-0x0193)
                (0x018D, 7, "G04 DC Pump + P07 Fan + Mode Control (0x018D-0x0193)"),
                
                # Batch 5: Antilegionella config & G02 Pump work mode (0x019A-0x019E)
                (0x019A, 5, "Antilegionella + G02 Pump Mode (0x019A-0x019E)"),
            ]
            
            total_rw_read = 0
            for start_addr, count, description in rw_batches:
                try:
                    time.sleep(0.20)  # Safe turnaround time on half-duplex RS485
                    result = client.read_holding_registers(
                        address=start_addr,
                        count=count,
                        device_id=device_address
                    )
                    
                    if result.isError():
                        _LOGGER.debug("CHICO: Error reading batch %s (0x%04X): %s", description, start_addr, result)
                        continue
                    
                    if len(result.registers) != count:
                        _LOGGER.error(
                            "CHICO: Batch size mismatch for %s! Expected %d, got %d registers. "
                            "Resetting connection to prevent stream desynchronization.",
                            description, count, len(result.registers)
                        )
                        try:
                            client.close()
                        except Exception:
                            pass
                        break
                    
                    # Parse batch results
                    for i in range(count):
                        addr = start_addr + i
                        if addr in rw_config:
                            key, scale = rw_config[addr]
                            raw_value = result.registers[i]
                            
                            # Convert signed int16 if needed
                            if addr in SIGNED_RW_REGISTERS:
                                if raw_value > 32767:
                                    raw_value = raw_value - 65536
                            
                            data[key] = raw_value * scale
                            total_rw_read += 1
                    
                    _LOGGER.debug("CHICO: Read batch %s (%d registers)", description, count)
                    
                except Exception as err:
                    _LOGGER.debug("CHICO: Exception reading batch %s: %s", description, err)
            
            _LOGGER.debug("CHICO: Batch RW read completed (%d registers in %d batches)", total_rw_read, len(rw_batches))
        
        return data
    
    def write_register(
        self,
        client: ModbusTcpClient,
        device_address: int,
        address: int,
        value: int,
    ) -> bool:
        """Write a CHICO register."""
        if not client.connected:
            if not client.connect():
                raise ConnectionError("Cannot connect to Modbus device")
        
        result = client.write_register(
            address=address,
            value=value,
            device_id=device_address
        )
        
        if result.isError():
            raise ValueError(f"Modbus write error: {result}")
        
        return True
    
    def get_platforms(self) -> list[str]:
        """Return supported platforms for CHICO."""
        return ["sensor", "binary_sensor", "number", "select", "switch", "button", "climate"]
    
    def get_device_info(self, entry_id: str) -> dict:
        """Return device info for CHICO controller."""
        return {
            "identifiers": {("sprsun_modbus", entry_id)},
            "name": "SPRSUN Heat Pump",
            "manufacturer": "SPRSUN",
            "model": "Heat Pump (CHICO Controller)",
        }
    
    @classmethod
    def detect(cls, client: ModbusTcpClient, device_address: int) -> bool:
        """
        Detect CHICO controller by reading signature registers.
        
        CHICO has controller/display version registers at 0x002C/0x002D.
        """
        try:
            # Try to read version registers (CHICO specific)
            result = client.read_holding_registers(
                address=0x002C,
                count=2,
                device_id=device_address
            )
            
            if result.isError():
                return False
            
            # If we can read these registers, likely CHICO
            # Controller and Display versions should be reasonable values (0-999)
            if len(result.registers) == 2:
                controller_ver = result.registers[0]
                display_ver = result.registers[1]
                
                # Sanity check: versions should be 0-999
                if 0 <= controller_ver <= 999 and 0 <= display_ver <= 999:
                    _LOGGER.info(
                        "CHICO controller detected (Controller v%d, Display v%d)",
                        controller_ver, display_ver
                    )
                    return True
        
        except Exception as err:
            _LOGGER.debug("CHICO detection failed: %s", err)
        
        return False
