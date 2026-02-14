#!/usr/bin/env python3
"""Analyze which register is missing in batch reads causing the shift"""

import csv

with open('sprsun_batch_data_20260214_000136.csv', 'r') as f:
    reader = csv.DictReader(f)
    headers = list(reader.fieldnames)
    
    # Register sequence based on address
    register_sequence = [
        (0x0000, "Compressor Runtime"),
        (0x0001, "COP"),
        (0x0002, "Switching Input Symbol"),
        (0x0003, "Working Status Mark"),
        (0x0004, "Output Symbol 1"),
        (0x0005, "Output Symbol 2"),
        (0x0006, "Output Symbol 3"),
        (0x0007, "Failure Symbol 1"),
        (0x0008, "Failure Symbol 2"),
        (0x0009, "Failure Symbol 3"),
        (0x000A, "Failure Symbol 4"),
        (0x000B, "Failure Symbol 5"),
        (0x000C, "Failure Symbol 6"),
        (0x000D, "Failure Symbol 7"),
        (0x000E, "Inlet temp."),
        (0x000F, "Hotwater temp."),
        (0x0010, "Reserved 0x0010"),
        (0x0011, "Ambi temp."),
        (0x0012, "Outlet temp."),
    ]
    
    print("Looking at shifted rows to determine which register is skipped:")
    print("=" * 100)
    
    for i, row in enumerate(reader, start=2):
        # Check if this row has shift (Inlet temp = 0.0)
        if row.get("Inlet temp.") == "0.0":
            print(f"\nRow {i} (timestamp: {row['Timestamp']})")
            print("-" * 100)
            print(f"{'Register':<25} {'Expected Value':<30} {'Observation'}")
            print("-" * 100)
            
            # The shift pattern shows:
            # - Inlet temp (0x000E) = 0.0 (should be ~29°C)
            # - Hotwater temp (0x000F) = ~29°C (this is inlet temp value!)
            # - Reserved (0x0010) = 460 (this is raw hotwater value!)
            
            print(f"{'0x000E Inlet temp':<25} {'~29°C':<30} {'0.0 ← WRONG'}")
            print(f"{'0x000F Hotwater temp':<25} {'~46°C':<30} {row['Hotwater temp.']} ← shifted, actual inlet temp")
            print(f"{'0x0010 Reserved':<25} {'0':<30} {row['Reserved 0x0010']} ← shifted, raw hotwater")
            print(f"{'0x0011 Ambi temp':<25} {'~0-5°C':<30} {row['Ambi temp.']} ← shifted, reserved value")
            
            # Try to determine which register was skipped
            print("\nIf batch read returned 49 registers instead of 50:")
            print("  Hypothesis: One of registers 0x0000-0x000D was skipped")
            print("  Effect: All registers from 0x000E onwards are shifted by +1 address")
