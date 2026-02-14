#!/usr/bin/env python3
"""
Analyze Modbus polling data - show statistics for each column
"""

import csv
import sys
from collections import defaultdict

def analyze_csv(filename):
    print(f"Analyzing: {filename}")
    print("=" * 80)
    print()
    
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if not rows:
        print("No data found in CSV file")
        return
    
    print(f"Total data points: {len(rows)}")
    print()
    
    # Get all column names except Timestamp
    columns = [col for col in rows[0].keys() if col != 'Timestamp']
    
    # Analyze each column
    for col in columns:
        values = []
        null_count = 0
        
        for row in rows:
            val = row[col]
            if val == '' or val == 'None':
                null_count += 1
            else:
                try:
                    values.append(float(val))
                except ValueError:
                    null_count += 1
        
        # Print column analysis
        print(f"Column: {col}")
        print("-" * 80)
        
        if not values:
            print(f"  Status: NO VALID DATA (all {null_count} values are null/invalid)")
        else:
            min_val = min(values)
            max_val = max(values)
            avg_val = sum(values) / len(values)
            
            # Check if values changed
            unique_values = set(values)
            
            print(f"  Valid readings: {len(values)}/{len(rows)}")
            if null_count > 0:
                print(f"  Null/Invalid:   {null_count}")
            print(f"  Min:            {min_val}")
            print(f"  Max:            {max_val}")
            print(f"  Average:        {avg_val:.2f}")
            print(f"  Unique values:  {len(unique_values)}")
            
            if len(unique_values) == 1:
                print(f"  Status:         CONSTANT (value: {min_val})")
            elif len(unique_values) <= 5:
                print(f"  Status:         LOW VARIATION (values: {sorted(unique_values)})")
            else:
                print(f"  Status:         VARYING")
                
            # Show all values if few data points
            if len(values) <= 10:
                print(f"  All values:     {values}")
        
        print()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        # Find latest file
        import glob
        files = sorted(glob.glob("sprsun_modbus_data_*.csv"), reverse=True)
        if not files:
            print("No CSV files found")
            sys.exit(1)
        filename = files[0]
    
    analyze_csv(filename)
