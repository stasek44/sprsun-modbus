# 🎛️ Built-in Home Assistant Dashboards (100% Native Lovelace)

The integration ships with built-in **100% native Home Assistant Lovelace strategies** for both **CHICO** and **CAREL** controllers (built with the modern `sections` layout — **no HACS custom cards and no YAML copy-paste required**).

- **Automatic language selection:** Reads your Home Assistant UI language (`en`, `pl`, `fr`, `de`, `es`, `cs`, `sk`, `hu`, `lt`, `uk`) from a single template + i18n dictionary.
- **Automatic entity detection:** Resolves your actual entity IDs automatically via `unique_id` — even if you renamed your heat pump device.
- **Editable anytime:** Click **Take control** in Home Assistant whenever you want to convert the generated dashboard into a manually editable one.

---

## 📦 What's Included

| Component | Description |
| :--- | :--- |
| **Built-in Dashboard (`custom:sprsun`)** | Full **4-tab Dashboard** (`Default`, `Detailed`, `Diagnostics`, `Optimization`) selectable directly from **+ Add Dashboard** |
| **Built-in Control Section (`custom:sprsun-control`)** | Compact single control section selectable from **+ Add Section** on any Sections dashboard |
| **Built-in 24h Counters** | `Defrost Count (24h)`, `Defrost Time (24h)`, `Compressor Starts (24h)`, `Electric Heaters Time (24h)` included directly under **Derived / Calculated Sensors** (persisted across HA restarts) |

### The 4 Views Explained

1. **Default (`default`)**: Everyday household control — ON/OFF, unit mode (`P06`), fan/noise profile (`P07`), `[-]` / `[+]` buttons for heating/DHW/cooling setpoints and hysteresis, thermostats, conditional fault banner with Reset, and a live plain-language summary of what the pump is doing.
2. **Detailed (`detailed`)**: Water loop & `Delta T`, full ECO weather curve (`E01–E24`) vs live `ECO Curve Target`, compressor/fan/EEV/pressure telemetry, electrical power/runtime, Antilegionella, and 24h comparison charts.
3. **Diagnostics (`diagnostics`)**: Automatic active-fault summary across all `24` alarm bits with physical troubleshooting tips, heat-exchanger & refrigerant health (`Condenser Approach`, `Suction Superheat`, `Discharge Superheat`, `Exhaust Temp`), relay & input statuses, and firmware versions.
4. **Optimization (`optimization`)**: Live plain-language assistant checking short-cycling, `Water Delta T`, backup electric heaters (`COP = 1.0`), ECO curve offset, frost buildup (`Outdoor - Coil`), and defrost duration/interval — plus safe `P`/`G` levers and hidden-until-enabled `[EXPERT]` tuning for **defrost time & frequency** (`H01–H18`, `A43`, `A51`), DC pump limits (`F13–F17`), compressor Hz curves (`R04–R45`), and `Timeband 1`.

---

## 🛠️ Step-by-Step Installation

### 1. Enable Derived Sensors (Recommended)
For the `Detailed`, `Diagnostics`, and `Optimization` views to show calculated metrics (`Operating State`, `Water Delta T`, `Coil-Ambient Delta`, `Defrost Interval`, `ECO Curve Target`, `Estimated Power`, etc.):
1. Go to **Settings → Devices & Services → SPRSUN Heat Pump (Modbus)**.
2. Click **Configure**.
3. Enable **Enable Derived / Calculated Sensors** and submit (the integration reloads automatically).

> **Note on Expert Settings (`[EXPERT]` sections):** Leave **Enable Expert Settings** disabled until you want to tune factory parameters (`H01–H18`, `F`, `R`). The dashboard automatically hides `[EXPERT]` sections when the option is off so you won't see broken tiles.

### 2. Add the Built-in 4-Tab Dashboard (No YAML Needed)
1. In Home Assistant, go to **Settings → Dashboards → + Add Dashboard**.
2. Pick **SPRSUN Heat Pump** from the dashboard strategies list (if your browser still has cached assets after an upgrade, refresh once with `Ctrl+F5`).
3. *(Alternative YAML)* Or create an empty dashboard, open **Raw configuration editor**, and paste:
   ```yaml
   strategy:
     type: custom:sprsun
   ```
   *(Optional fields under `strategy:`: `entry_id` if you run multiple heat pumps, or `language: en` / `pl` to override your HA profile language.)*

### 3. Add the Compact Control Card to an Existing Dashboard
In any Sections view, click **Edit → + Add Section** and choose **SPRSUN — Quick Control** (`strategy: type: custom:sprsun-control`).

### 4. (Optional) External Power Meter
- **External Energy Meter:** Some CHICO firmware variants (e.g. without the factory flow/power board) report `0` for internal `COP`, `Heating/Cooling Capacity`, `AC Voltage`, and `Pump Flow`. If you have a smart meter (Shelly 3EM, Tuya, etc.), simply add its `kW` / `kWh` sensor to the Optimization tab.

---

## 💡 Optimization Guide ("What I See → What to Adjust")

### A. Reducing Electricity Consumption (Beyond Defrost)

| Symptom / Metric | What It Means in Plain Language | Recommended Adjustment |
| :--- | :--- | :--- |
| **Supply vs ECO Curve** is high (`+5°C`+) or rooms are overheated | Every **1°C** higher water temp costs **~2–3% more electricity** | Lower `P01` (or tune `E13–E16` curve points downward by 1–2°C) |
| **Compressor Cycle Duration** `< 15 min` (frequent ON/OFF) | Short-cycling wastes startup power and wears the compressor | Increase Heating Hysteresis `P03` (e.g. `2°C -> 4°C`) and check `G03` min restart delay (`5–10 min`) |
| **DHW Setpoint `P04` > 50°C** | Heating hot water above 50°C sharply lowers heat pump COP | Target **45–48°C** for daily DHW and rely on weekly **Antilegionella** (`60°C+`) |
| **Electric Heater (`OUT4` / `OUT12`) turns ON** | Resistive heating runs at `COP = 1.0` (3–4x costlier than compressor) | Lower `G05` / `G07` ambient thresholds to `-10..-15°C` and raise delays `G06` / `G08` to `45–60 min` |
| **Water Delta T `< 2°C`** with high pump `%` | Circulation pump wastes power or water circulates too fast | Set `G02 = Demand` or `Normal`, raise `G04` Target Delta T (aim for `3–5°C` floor / `5–8°C` radiators), or check `[EXPERT] F16/F17` |
| **Water Delta T `> 7.5°C`** or **Condenser Approach `> 6°C`** | Restricted water flow raises condensing pressure and cuts COP | Clean the Y-strainer, bleed air, open radiator/manifold loops |
| **Expensive peak-tariff / PV wasted** | Heating DHW at cold night peaks costs more than sunny midday | Use `Timeband 1–3` (`[EXPERT]`) or HA automations to boost DHW at midday (higher outdoor temp = higher COP + solar surplus) |

### B. Optimizing Defrost Time & Frequency (`H01–H18`)

Every defrost reverses the cycle and pulls heat **out of your house** to melt ice off the outdoor coil. Look at the **24h Defrost Analysis** chart on the Optimization tab before changing any factory parameter (change **one setting at a time** in small steps and observe for 24h):

| Metric / Observation | What Is Happening | Safe Tuning Lever (`[EXPERT]`) |
| :--- | :--- | :--- |
| **Defrost triggers every ~45–60 min** while **Outdoor - Coil Delta** was still low (`< 7–8°C`) and coil looks clear | Minimum timer `H08/H11/H14` or delta `H07/H10/H13` is too sensitive | Increase `H08/H11/H14` (e.g. `45 -> 60 min`) or raise `H07/H10/H13` by `+1..2°C` (e.g. `10 -> 11–12°C`) |
| **Frequent defrosts around `0..+2°C` in Night/Eco mode** | Lower fan RPM (`P07 = Night`) chills the evaporator faster in damp air | Switch to `P07 = Normal` during humid `0..+2°C` weather, or raise fan curve `D09–D14` |
| **Coil Temp shoots to `+35..+45°C`** well after steam/water stopped dripping (`Defrost Duration > 5 min`) | Defrost keeps heating an already-clean outdoor coil | Slightly lower `H04` Exit Coil Temp (e.g. `15°C -> 12–13°C`) or lower `H01` Defrost Freq (e.g. `70 -> 55–60 Hz`) |
| **Ice remains on coil after defrost** (`Defrost Duration` hits `H05` max time) | Defrost ends too early or lacks heat | Raise `H04` (e.g. `15 -> 18°C`), check `H05` max time (`8–10 min`), and ensure good water flow during defrost (keep enough heating loops open) |
| **Chassis Heater ON continuously** | Draws ~`43 W` (`~1 kWh/day`) to prevent drain pan freezing | Normal in freezing conditions; monitor 24h runtime via helpers |

### C. Understanding Sensor Filtering & Normal Defrost Transients

- **Filtered Outdoor Temp (`ambient_temp_filtered`):** Holds the pre-defrost outdoor reading during defrost and keeps holding post-defrost until `7 minutes` of **outdoor fan runtime** accumulate (or a `45-minute` wall-clock cap if the unit stays idle), so warm stagnant air around the casing does not trigger fake positive temperature spikes.
- **Frost Buildup (`coil_ambient_delta`):** Clamped to `0.0 °C` during active defrost and whenever `coil_temp >= ambient_temp_filtered` (preventing negative `-40 °C` spikes when defrost heats the coil). Rising values `4 -> 10 °C` during heating reflect real frost buildup and are charted separately from raw `Coil Temp`.
- **Negative `Water Delta T` & `Condenser Approach` during Defrost:** Kept raw for true telemetry — negative values during reverse-cycle defrost are expected (heat is drawn from heating water to melt frost), and the Live Assistant suppresses low-delta warnings automatically during defrost/startup transients.
- **Optional Smoothing in HA:** Raw Modbus values (`±1 Hz` compressor steps, `±0.1 °C` sensor quantization, defrost-cycle `Estimated Power` peaks) are intentionally left unfiltered; if you want smoother trend lines, add Home Assistant's built-in `filter` or `statistics` helper (`time_simple_moving_average`, 1–3 min) on the UI side.
