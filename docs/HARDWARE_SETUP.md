# Hardware & Gateway Setup

## RS485 Wiring

| Heat Pump Terminal | Gateway Terminal | Description |
| :--- | :--- | :--- |
| **A / +** | **A** | RS485 Data + |
| **B / -** | **B** | RS485 Data - |
| **GND** | **GND** | Signal ground, strongly recommended for signal integrity |

## Recommended Gateway Settings (Elfin EW11 / W11)

| Category | Parameter | Recommended Value | Notes |
| :--- | :--- | :--- | :--- |
| **Network / Socket** | Protocol | `TCP Server` | Standard Modbus TCP server mode |
| | Port | `502` | Default Modbus TCP port |
| | Timeout | `5s` – `10s` | Clears stale sockets quickly; avoid 60s+ |
| | Max Accept | `1` | **Critical:** prevents socket contention & bus frame interleaving |
| | Buffer Size | `512` | Sufficient for full register batch frames |
| | Keep Alive | `60s` | Keeps socket connection alive |
| **Serial (RS485)** | Baud Rate | `19200` | Standard SPRSUN baud rate |
| | Data Bits | `8` | |
| | Stop Bits | `2` (or `1`) | Depends on unit firmware |
| | Parity | `None` | |
| | Flow Control | `Half Duplex` | |
| | Gap Time | `20ms` – `50ms` | Minimum inter-frame delay |
| | CLI Settings | `Disable` | **Critical:** prevents binary data from triggering CLI mode |
| | Protocol | `Modbus` | Automatic Modbus RTU ↔ Modbus TCP framing |
