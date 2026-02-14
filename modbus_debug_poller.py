#!/usr/bin/env python3
"""
SPRSUN Heat Pump - Debug Poller (Simplified)

Czyta tylko NAJWAŻNIEJSZE parametry do debugowania:
- Core temps (inlet, hotwater, heating, ambient)
- Core setpoints (heating, cooling, hotwater)
- Unit mode
- Status flags
- COP i power

Do pełnej kontroli użyj Home Assistant!
"""

import csv
import time
from datetime import datetime
from pymodbus.client import ModbusTcpClient

# Konfiguracja
MODBUS_HOST = "192.168.1.234"
MODBUS_PORT = 502
DEVICE_ADDRESS = 1
CLIENT_TIMEOUT = 10  # sekundy timeout dla klienta Modbus
POLL_INTERVAL = 5  # sekundy między odczytami

# UWAGA: Elfin W11 timeout powinien być >= (POLL_INTERVAL + cycle_time)
# Cycle time: ~2s
# Zalecane: Elfin timeout = 10s dla POLL_INTERVAL = 5s
RECONNECT_ON_ERROR = True  # reconnect jeśli błąd
KEEP_CONNECTION_ALIVE = True  # utrzymuj połączenie

# UPROSZCZONA mapa - tylko essentials + wszystkie RW do porównania z HA
ESSENTIAL_REGISTERS = {
    # Core temps (R)
    0x000E: ("inlet_temp", 0.1, "R"),
    0x000F: ("hotwater_temp", 0.1, "R"),
    0x0011: ("heating_temp", 0.1, "R"),
    0x0012: ("ambient_temp", 0.1, "R"),
    0x0016: ("coil_temp", 0.1, "R"),
    0x0017: ("exhaust_temp", 0.1, "R"),
    
    # Core performance (R)
    0x0001: ("cop", 1.0, "R"),
    0x001D: ("compressor_frequency", 1.0, "R"),
    0x0029: ("inverter_power", 1.0, "R"),
    
    # Pressures (R)
    0x001B: ("high_pressure", 0.1, "R"),
    0x001C: ("low_pressure", 0.1, "R"),
    
    # Status flags (R)
    0x0003: ("working_status_mark", 1.0, "R"),
    0x0004: ("output_symbol_1", 1.0, "R"),
    
    # Failures (R)
    0x0007: ("failure_symbol_1", 1.0, "R"),
    0x0008: ("failure_symbol_2", 1.0, "R"),
    
    # Control (RW) - będą też w HA
    0x0032: ("control_parameter_marker", 1.0, "RW"),
    0x0033: ("control_mark_1", 1.0, "RW"),
    0x0034: ("control_mark_2", 1.0, "RW"),
    
    # Unit mode (RW) - NAJWAŻNIEJSZE
    0x0036: ("unit_mode", 1.0, "RW"),
    
    # Setpoints (RW) - NAJWAŻNIEJSZE
    0x00CC: ("heating_setpoint", 0.5, "RW"),
    0x00CB: ("cooling_setpoint", 0.5, "RW"),
    0x00CA: ("hotwater_setpoint", 0.5, "RW"),
    
    # Temperature diffs (RW)
    0x00C6: ("temp_diff_heating_cooling", 1.0, "RW"),
    0x00C8: ("temp_diff_hotwater", 1.0, "RW"),
    
    # Fan mode (RW)
    0x0190: ("fan_mode", 1.0, "RW"),
    
    # Pump mode (RW)
    0x019E: ("pump_work_mode", 1.0, "RW"),
}


def read_essential_batch(client):
    """
    Czyta tylko essentials - szybko i niezawodnie
    
    Strategia:
    - Batch 1: R 0x0000-0x001F (~32 regs) - wszystkie core temps + perf
    - Individual: RW registers (scattered addresses)
    
    OPTYMALIZACJA: Minimalne delays, keep connection alive
    """
    results = {}
    
    try:
        # Batch: Read-Only core (0x0000 - 0x001F = 32 regs)
        start = time.time()
        result = client.read_holding_registers(0x0000, count=32, device_id=DEVICE_ADDRESS)
        batch_time = time.time() - start
        
        if result.isError():
            print(f"  ❌ Batch R failed: {result}")
            return None
            
        if len(result.registers) != 32:
            print(f"  ❌ Batch R wrong size: {len(result.registers)} != 32")
            return None
        
        # Wyciągnij potrzebne rejestry
        for addr in [0x0001, 0x000E, 0x000F, 0x0011, 0x0012, 0x0016, 0x0017, 
                     0x001B, 0x001C, 0x001D]:
            if addr in ESSENTIAL_REGISTERS:
                name, scale, rw = ESSENTIAL_REGISTERS[addr]
                raw = result.registers[addr]
                scaled = raw * scale
                results[name] = (raw, scaled, rw)
        
        # Status flags - są w batchu
        for addr in [0x0003, 0x0004, 0x0007, 0x0008]:
            if addr in ESSENTIAL_REGISTERS:
                name, scale, rw = ESSENTIAL_REGISTERS[addr]
                raw = result.registers[addr]
                scaled = raw * scale
                results[name] = (raw, scaled, rw)
        
        print(f"  ✓ Batch R: 32 regs in {batch_time:.3f}s")
        
        # Individual RW registers (scattered) - BEZ delays między odczytami!
        rw_addresses = [0x0032, 0x0033, 0x0034, 0x0036, 0x00C6, 0x00C8, 
                        0x00CA, 0x00CB, 0x00CC, 0x0190, 0x019E]
        
        rw_start = time.time()
        rw_success = 0
        rw_failed = 0
        
        for addr in rw_addresses:
            if addr in ESSENTIAL_REGISTERS:
                try:
                    result = client.read_holding_registers(addr, count=1, device_id=DEVICE_ADDRESS)
                    if not result.isError() and len(result.registers) == 1:
                        name, scale, rw = ESSENTIAL_REGISTERS[addr]
                        raw = result.registers[0]
                        scaled = raw * scale
                        results[name] = (raw, scaled, rw)
                        rw_success += 1
                    else:
                        rw_failed += 1
                except Exception:
                    rw_failed += 1
                # NIE MA DELAY - maksymalna szybkość!
        
        rw_time = time.time() - rw_start
        print(f"  ✓ RW reads: {rw_success} OK, {rw_failed} failed in {rw_time:.3f}s")
        
        return results
        
    except Exception as e:
        print(f"  ❌ Exception: {e}")
        return None


def write_to_csv(data, csv_file="sprsun_debug_data.csv"):
    """Zapisz do CSV z oznaczeniem R/RW"""
    timestamp = datetime.now().isoformat()
    
    # Przygotuj wiersz
    row = {"timestamp": timestamp}
    
    # Dodaj kolumny: name, name_raw, name_rw
    for name, (raw, scaled, rw) in data.items():
        row[name] = scaled
        row[f"{name}_raw"] = raw
        row[f"{name}_type"] = rw
    
    # Sprawdź czy plik istnieje
    import os
    file_exists = os.path.isfile(csv_file)
    
    with open(csv_file, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp"] + list(row.keys())[1:])
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(row)


def main():
    """Main loop"""
    print("="*80)
    print("SPRSUN Heat Pump - Debug Poller (Essentials Only)")
    print("="*80)
    print(f"Host: {MODBUS_HOST}:{MODBUS_PORT}")
    print(f"Poll interval: {POLL_INTERVAL}s")
    print(f"Parameters: {len(ESSENTIAL_REGISTERS)}")
    print()
    print("⚠️  TEN SKRYPT JEST TYLKO DO DEBUGOWANIA!")
    print("   Do pełnej kontroli użyj Home Assistant Modbus integration.")
    print()
    print("Czytane parametry:")
    r_count = sum(1 for _, (_, _, rw) in ESSENTIAL_REGISTERS.items() if rw == "R")
    rw_count = sum(1 for _, (_, _, rw) in ESSENTIAL_REGISTERS.items() if rw == "RW")
    print(f"  - Read-Only (R): {r_count}")
    print(f"  - Read-Write (RW): {rw_count}")
    print()
    print("Press Ctrl+C to stop...")
    print("="*80)
    print()
    
    # Połącz
    client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT, timeout=CLIENT_TIMEOUT)
    
    if not client.connect():
        print("❌ Connection failed!")
        return
    
    print("✓ Connected")
    print()
    
    poll_count = 0
    success_count = 0
    
    try:
        while True:
            poll_count += 1
            start_time = time.time()
            
            print(f"Poll #{poll_count}...")
            data = read_essential_batch(client)
            
            elapsed = time.time() - start_time
            
            if data:
                success_count += 1
                write_to_csv(data)
                
                print(f"✓ SUCCESS ({elapsed:.2f}s) - {len(data)} parameters")
                print(f"  📊 Current Status:")
                print(f"    Temps: Inlet={data.get('inlet_temp', (0,0,''))[1]:.1f}°C, "
                      f"HotWater={data.get('hotwater_temp', (0,0,''))[1]:.1f}°C, "
                      f"Heating={data.get('heating_temp', (0,0,''))[1]:.1f}°C, "
                      f"Ambient={data.get('ambient_temp', (0,0,''))[1]:.1f}°C")
                print(f"    Setpoints: Heat={data.get('heating_setpoint', (0,0,''))[1]:.1f}°C, "
                      f"Cool={data.get('cooling_setpoint', (0,0,''))[1]:.1f}°C, "
                      f"HW={data.get('hotwater_setpoint', (0,0,''))[1]:.1f}°C")
                print(f"    Mode: {int(data.get('unit_mode', (0,0,''))[1])} "
                      f"(0=DHW, 1=Heat, 2=Cool, 3=Heat+DHW, 4=Cool+DHW)")
                print(f"    Performance: COP={int(data.get('cop', (0,0,''))[1])}, "
                      f"Freq={int(data.get('compressor_frequency', (0,0,''))[1])}Hz, "
                      f"Power={int(data.get('inverter_power', (0,0,''))[1])}W")
                print()
            else:
                print(f"✗ FAILED ({elapsed:.2f}s)")
                print("  Attempting reconnect...")
                try:
                    client.close()
                    time.sleep(1)
                    if client.connect():
                        print("  ✓ Reconnected")
                    else:
                        print("  ❌ Reconnect failed")
                except Exception as e:
                    print(f"  ❌ Exception: {e}")
                print()
            
            # Stats every 10 polls
            if poll_count % 10 == 0:
                rate = success_count * 100 // poll_count
                print(f"{'='*80}")
                print(f"Stats: {success_count}/{poll_count} polls OK ({rate}%)")
                print(f"{'='*80}")
                print()
            
            # Wait
            time.sleep(POLL_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n" + "="*80)
        print("Stopped by user")
        print(f"Total polls: {poll_count}, OK: {success_count}, Failed: {poll_count - success_count}")
        if poll_count > 0:
            print(f"Success rate: {success_count * 100 // poll_count}%")
        print("="*80)
    
    finally:
        client.close()
        print("✓ Disconnected")


if __name__ == "__main__":
    main()
