#!/bin/bash
# Monitor the Modbus poller progress

echo "SPRSUN Modbus Poller - Monitor"
echo "=============================="
echo

# Find the latest CSV file
LATEST_CSV=$(ls -t sprsun_modbus_data_*.csv 2>/dev/null | head -1)

if [ -z "$LATEST_CSV" ]; then
    echo "No CSV files found. Poller may not be running."
    exit 1
fi

echo "Latest data file: $LATEST_CSV"
echo "File size: $(du -h "$LATEST_CSV" | cut -f1)"
echo

# Count data rows (exclude header)
ROW_COUNT=$(($(wc -l < "$LATEST_CSV") - 1))
echo "Data points collected: $ROW_COUNT"
echo

# Show start and end timestamps
echo "Data collection period:"
FIRST_TS=$(sed -n '2p' "$LATEST_CSV" | cut -d',' -f1)
LAST_TS=$(tail -1 "$LATEST_CSV" | cut -d',' -f1)
echo "  Started: $FIRST_TS"
echo "  Latest:  $LAST_TS"
echo

# Show latest values
echo "Latest readings:"
echo "----------------"
/home/stanislaw/src/sprsun-modbus/.venv/bin/python3 << PYEOF
import csv

try:
    with open('$LATEST_CSV', 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        if rows:
            row = rows[-1]
            print(f"  Timestamp:         {row['Timestamp']}")
            print(f"  Inlet temp:        {row['Inlet temp.']} °C")
            print(f"  Outlet temp:       {row['Outlet temp.']} °C")
            print(f"  Hotwater temp:     {row['Hotwater temp.']} °C")
            print(f"  Ambi temp:         {row['Ambi temp.']} °C")
            print(f"  Comp. Frequency:   {row['Comp. Frequency']} Hz")
            print(f"  Suct. Press:       {row['Suct. Press']} bar")
            print(f"  Disch. Press:      {row['Disch. Press']} bar")
            print(f"  Working Status:    {row['Working Status Mark']}")
except Exception as e:
    print(f"Error reading data: {e}")
PYEOF

echo
echo "Poll rate: ~10 seconds per sample"
echo "Target: ~90 samples over 15 minutes"
