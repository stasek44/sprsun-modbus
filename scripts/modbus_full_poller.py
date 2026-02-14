#!/usr/bin/env python3
"""
SPRSUN Heat Pump - Full Modbus Poller (READ-ONLY + READ-WRITE registers)

Czyta WSZYSTKIE rejestry z SPRSUN heat pump:
- Read-Only (0x0000-0x002D): Status, temps, flags
- Read-Write (0x0032-0x019D): Configuration, setpoints

UWAGA: Ten skrypt tylko CZYTA rejestry RW, nie zapisuje!
       Zapisy (WRITE) będą wykonywane przez Home Assistant.
"""

import csv
import time
from datetime import datetime
from pymodbus.client import ModbusTcpClient

# Konfiguracja Modbus
MODBUS_HOST = "192.168.1.234"
MODBUS_PORT = 502
DEVICE_ADDRESS = 1
CLIENT_TIMEOUT = 3  # sekundy
POLL_INTERVAL = 15  # sekund - dłużej niż czas cyklu (~2-3s) aby uniknąć konfliktów

# Mapowanie rejestrów Read-Only (0x0000 - 0x002D)
READ_ONLY_REGISTERS = {
    0x0000: ("compressor_runtime", 1.0),
    0x0001: ("cop", 1.0),
    0x0002: ("switching_input_symbol", 1.0),
    0x0003: ("working_status_mark", 1.0),
    0x0004: ("output_symbol_1", 1.0),
    0x0005: ("output_symbol_2", 1.0),
    0x0006: ("output_symbol_3", 1.0),
    0x0007: ("failure_symbol_1", 1.0),
    0x0008: ("failure_symbol_2", 1.0),
    0x0009: ("failure_symbol_3", 1.0),
    0x000A: ("failure_symbol_4", 1.0),
    0x000B: ("failure_symbol_5", 1.0),
    0x000C: ("failure_symbol_6", 1.0),
    0x000D: ("failure_symbol_7", 1.0),
    0x000E: ("inlet_temp", 0.1),
    0x000F: ("hotwater_temp", 0.1),
    0x0010: ("unknown_0010", 1.0),  # Niezadokumentowany
    0x0011: ("heating_temp", 0.1),
    0x0012: ("ambient_temp", 0.1),
    0x0013: ("software_version_year", 1.0),
    0x0014: ("software_version_month_day", 1.0),
    0x0015: ("return_air_temp", 0.1),
    0x0016: ("coil_temp", 0.1),
    0x0017: ("exhaust_temp", 0.1),
    0x0018: ("economizer_inlet_temp", 0.5),
    0x0019: ("economizer_outlet_temp", 0.5),
    0x001A: ("cooling_temp", 0.1),
    0x001B: ("high_pressure", 0.1),
    0x001C: ("low_pressure", 0.1),
    0x001D: ("current_compressor_frequency", 1.0),
    0x001E: ("current_dc_fan_speed", 1.0),
    0x001F: ("frequency_conversion_failure_1", 1.0),
    0x0020: ("frequency_conversion_failure_2", 1.0),
    0x0021: ("frequency_conversion_current", 0.1),
    0x0022: ("frequency_conversion_voltage", 1.0),
    0x0023: ("condenser_outlet_temp", 0.5),
    0x0024: ("main_valve_opening", 1.0),
    0x0025: ("smart_grid_status", 1.0),
    0x0026: ("auxiliary_valve_opening", 1.0),
    0x0027: ("inverter_inlet_temp", 0.1),
    0x0028: ("inverter_exhaust_temp", 0.1),
    0x0029: ("frequency_conversion_power", 1.0),
    0x002A: ("freq_conversion_fault_high", 1.0),
    0x002B: ("freq_conversion_fault_low", 1.0),
    0x002C: ("controller_version", 1.0),
    0x002D: ("display_version", 1.0),
}

# Mapowanie rejestrów Read-Write - KLUCZOWE PARAMETRY
# Te same rejestry może czytać/zapisywać Home Assistant!
READ_WRITE_REGISTERS = {
    # Control marks (bitowe)
    0x0032: ("control_parameter_marker", 1.0),
    0x0033: ("control_mark_1", 1.0),
    0x0034: ("control_mark_2", 1.0),
    
    # Podstawowe ustawienia (NAJWAŻNIEJSZE dla HA)
    0x0036: ("unit_mode", 1.0),  # 0=DHW, 1=Heat, 2=Cool, 3=Heat+DHW, 4=Cool+DHW
    0x00C6: ("temp_diff_heating_cooling", 1.0),  # P03: Cooling/heating startup differential
    0x00C8: ("temp_diff_hotwater", 1.0),  # P05: Hot water startup differential
    0x00CA: ("hotwater_setpoint", 0.5),  # P04: Hot water temp (10-55°C)
    0x00CB: ("cooling_setpoint", 0.5),   # P02: Cooling temp (12-30°C)
    0x00CC: ("heating_setpoint", 0.5),   # P01: Heating temp (10-55°C)
    
    # Economic mode - Heating (ambient temps)
    0x0169: ("econ_heat_ambi_1", 1.0),  # E01: -30~50°C
    0x016A: ("econ_heat_ambi_2", 1.0),  # E02
    0x016B: ("econ_heat_ambi_3", 1.0),  # E03
    0x016C: ("econ_heat_ambi_4", 1.0),  # E04
    
    # Economic mode - Hot Water (ambient temps)
    0x016D: ("econ_water_ambi_1", 1.0),  # E05
    0x016E: ("econ_water_ambi_2", 1.0),  # E06
    0x016F: ("econ_water_ambi_3", 1.0),  # E07
    0x0170: ("econ_water_ambi_4", 1.0),  # E08
    
    # Economic mode - Cooling (ambient temps)
    0x0171: ("econ_cool_ambi_1", 1.0),   # E09
    0x0172: ("econ_cool_ambi_2", 1.0),   # E10
    0x0173: ("econ_cool_ambi_3", 1.0),   # E11
    0x0174: ("econ_cool_ambi_4", 1.0),   # E12
    
    # Economic mode - Heating (water temps)
    0x0175: ("econ_heat_temp_1", 0.5),   # E13
    0x0176: ("econ_heat_temp_2", 0.5),   # E14
    0x0177: ("econ_heat_temp_3", 0.5),   # E15
    0x0178: ("econ_heat_temp_4", 0.5),   # E16
    
    # Economic mode - Hot Water (water temps)
    0x0179: ("econ_water_temp_1", 0.5),  # E17
    0x017A: ("econ_water_temp_2", 0.5),  # E18
    0x017B: ("econ_water_temp_3", 0.5),  # E19
    0x017C: ("econ_water_temp_4", 0.5),  # E20
    
    # Economic mode - Cooling (water temps)
    0x017D: ("econ_cool_temp_1", 0.5),   # E21
    0x017E: ("econ_cool_temp_2", 0.5),   # E22
    0x017F: ("econ_cool_temp_3", 0.5),   # E23
    0x0180: ("econ_cool_temp_4", 0.5),   # E24
    
    # General configuration
    0x0181: ("comp_delay_hotwater", 1.0),      # G08: 1-60 min
    0x0182: ("comp_delay_heating", 1.0),       # G06: 1-60 min
    0x0183: ("hotwater_heater_ext_temp", 1.0), # G07: -30~30°C
    0x0184: ("heating_heater_ext_temp", 1.0),  # G05: -30~30°C
    0x0185: ("pump_start_interval", 1.0),      # G03: 1-120 min
    0x018D: ("delta_temp_set", 1.0),           # G04: 5-30°C
    0x0190: ("fan_mode", 1.0),                 # P07: 0=NOR, 1=ECO, 2=Night, 3=Test
    0x0191: ("enable_switch", 1.0),            # G09: Mode control
    0x0192: ("ambtemp_switch_setp", 1.0),      # G10: -20~30°C
    0x0193: ("ambtemp_diff", 1.0),             # G11: 1-10°C
    0x019E: ("pump_work_mode", 1.0),           # G02: 0=Interval, 1=Normal, 2=Demand
    
    # Antilegionella
    0x019A: ("antilegionella_temp", 1.0),      # 30-70°C
    0x019B: ("antilegionella_weekday", 1.0),   # 0=Sun, 6=Sat
    0x019C: ("antilegionella_start_hour", 1.0),# 0-23
    0x019D: ("antilegionella_end_hour", 1.0),  # 0-23
}

# Wszystkie rejestry razem
ALL_REGISTERS = {**READ_ONLY_REGISTERS, **READ_WRITE_REGISTERS}


def read_all_registers_batch(client):
    """
    Czyta wszystkie rejestry w inteligentnych batchach
    
    Strategia:
    - Batch 1: R 0x0000-0x002D (46 regs) - kompletny blok read-only
    - Batch 2: RW 0x0032-0x0036 (5 regs) - control marks + unit mode
    - Batch 3: RW 0x00C6-0x00CC (pojedyncze - przerwy w adresach)
    - Batch 4: RW 0x0169-0x0180 (24 regs) - economic mode
    - Batch 5: RW 0x0181-0x019E (pojedyncze lub małe batche)
    
    OPTYMALIZACJA: Reconnect jeśli połączenie zerwane
    
    Returns:
        dict: {register_name: (raw_value, scaled_value)} lub None jeśli błąd
    """
    results = {}
    
    # Sprawdź połączenie i reconnect jeśli potrzeba
    if not client.connected:
        print("  ⚠️  Connection lost, reconnecting...")
        if not client.connect():
            print("  ❌ Reconnect failed!")
            return None
    
    try:
        # Batch 1: Read-Only rejestry (0x0000 - 0x002D)
        result = client.read_holding_registers(0x0000, count=46, device_id=DEVICE_ADDRESS)
        if result.isError() or len(result.registers) != 46:
            print(f"❌ Batch 1 failed: {len(result.registers) if not result.isError() else 'ERROR'}")
            return None
        
        for i, addr in enumerate(range(0x0000, 0x002E)):
            if addr in READ_ONLY_REGISTERS:
                name, scale = READ_ONLY_REGISTERS[addr]
                raw = result.registers[i]
                scaled = raw * scale
                results[name] = (raw, scaled)
        
        time.sleep(0.05)  # Krótszy delay - musimy zmieścić się w 5s timeout
        
        # Batch 2: Control marks + unit mode (0x0032 - 0x0036)
        result = client.read_holding_registers(0x0032, count=5, device_id=DEVICE_ADDRESS)
        if result.isError() or len(result.registers) != 5:
            print(f"⚠️  Batch 2 failed (non-critical)")
        else:
            for i, addr in enumerate(range(0x0032, 0x0037)):
                if addr in READ_WRITE_REGISTERS:
                    name, scale = READ_WRITE_REGISTERS[addr]
                    raw = result.registers[i]
                    scaled = raw * scale
                    results[name] = (raw, scaled)
        
        time.sleep(0.05)
        
        # Batch 3: Podstawowe setpointy (pojedyncze odczyty - są przerwy w adresach)
        for addr in [0x00C6, 0x00C8, 0x00CA, 0x00CB, 0x00CC]:
            try:
                result = client.read_holding_registers(addr, count=1, device_id=DEVICE_ADDRESS)
                if not result.isError() and len(result.registers) == 1:
                    name, scale = READ_WRITE_REGISTERS[addr]
                    raw = result.registers[0]
                    scaled = raw * scale
                    results[name] = (raw, scaled)
            except Exception as e:
                print(f"  ⚠️  Failed to read 0x{addr:04X}: {e}")
            time.sleep(0.02)  # Bardzo krótki delay
        
        time.sleep(0.05)
        
        # Batch 4: Economic mode (0x0169 - 0x0180)
        try:
            result = client.read_holding_registers(0x0169, count=24, device_id=DEVICE_ADDRESS)
            if not result.isError() and len(result.registers) == 24:
                for i, addr in enumerate(range(0x0169, 0x0181)):
                    if addr in READ_WRITE_REGISTERS:
                        name, scale = READ_WRITE_REGISTERS[addr]
                        raw = result.registers[i]
                        scaled = raw * scale
                        results[name] = (raw, scaled)
            else:
                print(f"  ⚠️  Batch 4 (economic mode) failed - skipping")
        except Exception as e:
            print(f"  ⚠️  Batch 4 exception: {e}")
        
        time.sleep(0.05)
        
        # Batch 5: General config (pojedyncze - są duże przerwy)
        for addr in [0x0181, 0x0182, 0x0183, 0x0184, 0x0185, 0x018D, 
                     0x0190, 0x0191, 0x0192, 0x0193, 0x019A, 0x019B, 
                     0x019C, 0x019D, 0x019E]:
            if addr in READ_WRITE_REGISTERS:
                try:
                    result = client.read_holding_registers(addr, count=1, device_id=DEVICE_ADDRESS)
                    if not result.isError() and len(result.registers) == 1:
                        name, scale = READ_WRITE_REGISTERS[addr]
                        raw = result.registers[0]
                        scaled = raw * scale
                        results[name] = (raw, scaled)
                except Exception as e:
                    print(f"  ⚠️  Failed to read 0x{addr:04X}: {e}")
                time.sleep(0.02)  # Bardzo krótki delay
        
        return results
        
    except Exception as e:
        print(f"❌ Exception during batch read: {e}")
        return None


def write_to_csv(data, csv_file="sprsun_full_data.csv"):
    """Zapisz dane do CSV"""
    timestamp = datetime.now().isoformat()
    
    # Przygotuj wiersz: timestamp + wszystkie scaled values
    row = {"timestamp": timestamp}
    for name, (raw, scaled) in data.items():
        row[name] = scaled
    
    # Sprawdź czy plik istnieje
    import os
    file_exists = os.path.isfile(csv_file)
    
    with open(csv_file, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp"] + list(data.keys()))
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(row)


def main():
    """Główna pętla pollingu"""
    print("="*80)
    print("SPRSUN Heat Pump - Full Modbus Poller")
    print("="*80)
    print(f"Host: {MODBUS_HOST}:{MODBUS_PORT}")
    print(f"Poll interval: {POLL_INTERVAL}s")
    print(f"Read-Only registers: {len(READ_ONLY_REGISTERS)}")
    print(f"Read-Write registers: {len(READ_WRITE_REGISTERS)}")
    print(f"Total: {len(ALL_REGISTERS)} rejestrów")
    print()
    print("⚠️  UWAGA: Ten skrypt tylko CZYTA rejestry RW!")
    print("   Zapisy (WRITE) będą wykonywane przez Home Assistant.")
    print()
    print("Press Ctrl+C to stop...")
    print("="*80)
    print()
    
    # Połącz z Modbus
    client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT, timeout=CLIENT_TIMEOUT)
    
    if not client.connect():
        print("❌ Nie można połączyć z Modbus!")
        return
    
    print("✓ Połączono z Modbus")
    print()
    
    poll_count = 0
    success_count = 0
    
    try:
        while True:
            poll_count += 1
            start_time = time.time()
            
            # Czytaj wszystkie rejestry
            data = read_all_registers_batch(client)
            
            elapsed = time.time() - start_time
            
            if data:
                success_count += 1
                
                # Zapisz do CSV
                write_to_csv(data)
                
                # Wyświetl kluczowe wartości
                print(f"Poll #{poll_count} ({elapsed:.2f}s) - ✓ OK - {len(data)} parametrów")
                print(f"  Temps: Inlet={data.get('inlet_temp', (0,0))[1]:.1f}°C, "
                      f"HotWater={data.get('hotwater_temp', (0,0))[1]:.1f}°C, "
                      f"Heating={data.get('heating_temp', (0,0))[1]:.1f}°C")
                print(f"  Setpoints: Heat={data.get('heating_setpoint', (0,0))[1]:.1f}°C, "
                      f"Cool={data.get('cooling_setpoint', (0,0))[1]:.1f}°C, "
                      f"HW={data.get('hotwater_setpoint', (0,0))[1]:.1f}°C")
                print(f"  Mode: {int(data.get('unit_mode', (0,0))[1])} "
                      f"(0=DHW, 1=Heat, 2=Cool, 3=Heat+DHW, 4=Cool+DHW)")
                print()
            else:
                print(f"Poll #{poll_count} ({elapsed:.2f}s) - ✗ FAILED")
                # Spróbuj reconnect
                print("  Attempting reconnect...")
                try:
                    client.close()
                    time.sleep(1)
                    if client.connect():
                        print("  ✓ Reconnected successfully")
                    else:
                        print("  ❌ Reconnect failed")
                except Exception as e:
                    print(f"  ❌ Reconnect exception: {e}")
                print()
            
            # Success rate
            if poll_count % 10 == 0:
                rate = success_count * 100 // poll_count
                print(f"--- Success rate: {success_count}/{poll_count} ({rate}%) ---")
                print()
            
            # Czekaj przed następnym pollem
            time.sleep(POLL_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n" + "="*80)
        print("Zatrzymano przez użytkownika")
        print(f"Total polls: {poll_count}")
        print(f"Successful: {success_count}")
        print(f"Failed: {poll_count - success_count}")
        if poll_count > 0:
            print(f"Success rate: {success_count * 100 // poll_count}%")
        print("="*80)
    
    finally:
        client.close()
        print("✓ Połączenie zamknięte")


if __name__ == "__main__":
    main()
