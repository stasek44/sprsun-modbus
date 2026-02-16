# Climate Entity Options for SPRSUN Heat Pump

## Overview

Home Assistant's `climate` platform provides a standardized interface for HVAC control. For the SPRSUN heat pump, there are several implementation approaches to consider.

## Current State

The integration currently exposes:
- **Sensors**: Temperature readings, COP, pressures, etc.
- **Numbers**: Setpoints (heating, cooling, DHW) and differentials
- **Selects**: Unit mode (heating/cooling/DHW combinations), fan mode
- **Switches**: Power, antilegionella, two/three function
- **Buttons**: Failure reset

## Climate Entity Options

### Option 1: Single Climate Entity (Recommended)

**Concept**: One climate entity that controls the primary heating/cooling function.

**Mapping**:
- **hvac_mode**: 
  - `off` → Power switch OFF (0x0032 bit 0 = 0)
  - `heat` → Unit Mode = Heating Only or Heating+DHW (P06 = 1 or 3)
  - `cool` → Unit Mode = Cooling Only or Cooling+DHW (P06 = 2 or 4)
  - `heat_cool` → Auto mode with G09 enabled (automatic switching based on ambient temp)
  
- **target_temperature**: 
  - In heat mode → Heating Setpoint (P01/0x00CC)
  - In cool mode → Cooling Setpoint (P02/0x00CB)
  
- **current_temperature**: 
  - Outlet Water Temperature (0x0012) - what's being delivered to the system
  
- **fan_mode**:
  - Maps to P07 Fan Mode (Normal, Economic, Night, Test)
  
- **preset_mode**:
  - `none` → Manual temperature control
  - `eco` → Enable economic mode (uses E01-E24 curve parameters)
  - `boost` → Fan Mode = Normal (maximum capacity)
  - `away` → Lower temperature setpoints

**Pros**:
- ✅ Standard HA interface - works with voice assistants, dashboards, automations
- ✅ Simple for users - one entity to control heating/cooling
- ✅ Compatible with HA climate card
- ✅ Matches typical thermostat behavior

**Cons**:
- ❌ DHW control separate (use number entity or create second climate)
- ❌ Some advanced features not exposed (economic curve points)
- ❌ Multiple setpoints (P01-P05) need abstraction

### Option 2: Multiple Climate Entities

**Concept**: Separate climate entities for different zones/functions.

**Entities**:
1. **Heating Climate**: Controls heating function only
   - hvac_mode: off, heat
   - target_temperature: P01 Heating Setpoint
   - current_temperature: Outlet temp (heating mode)
   
2. **Cooling Climate**: Controls cooling function only
   - hvac_mode: off, cool
   - target_temperature: P02 Cooling Setpoint
   - current_temperature: Outlet temp (cooling mode)
   
3. **DHW Climate**: Controls hot water
   - hvac_mode: off, heat
   - target_temperature: P04 Hotwater Setpoint
   - current_temperature: Hot Water Temperature (0x000F)

**Pros**:
- ✅ Explicit control of each function
- ✅ DHW has its own climate entity (more intuitive for water heaters)
- ✅ Can expose all setpoints independently

**Cons**:
- ❌ More entities cluttering the UI
- ❌ Complex interactions (if heating climate is "on", which P06 mode to use?)
- ❌ Unit can only do ONE thing at a time (either heating OR cooling OR DHW)
- ❌ Potential conflicts between entities

### Option 3: No Climate Entity (Current Approach)

**Keep using existing entities**:
- Number entities for setpoints
- Select entity for mode
- Switch for power

**Pros**:
- ✅ Maximum flexibility and control
- ✅ All parameters directly accessible
- ✅ No abstraction layer hiding functionality
- ✅ Advanced users have full control

**Cons**:
- ❌ Not compatible with standard HA climate automations
- ❌ Voice assistants won't recognize it as a thermostat
- ❌ Requires custom dashboards/cards
- ❌ Steeper learning curve for users

## Recommendation

### **Implement Option 1 + Option 3 (Hybrid Approach)**

**Add a single climate entity** alongside existing entities:

```python
# Climate entity configuration
- hvac_modes: [off, heat, cool, heat_cool]
- target_temperature: P01 (heat) or P02 (cool)
- current_temperature: Outlet temperature
- fan_modes: [normal, eco, night, test] (maps to P07)
- preset_modes: [none, eco, boost]
- temperature_unit: °C
- min_temp: 10°C (heating) / 12°C (cooling)
- max_temp: 55°C (heating) / 30°C (cooling)
- target_temp_step: 0.5°C
```

**Keep all existing entities** for:
- Advanced configuration (economic curves, differentials, DHW)
- Users who prefer granular control
- Parameters not suitable for climate abstraction

**Benefits**:
1. **User-friendly**: Simple climate card for basic control
2. **Powerful**: Advanced users can still access everything via number/select entities
3. **Compatible**: Works with HA automations, voice control, climate-based integrations
4. **Flexible**: Users choose their preferred interface

## Implementation Considerations

### 1. Mode Management

When climate entity changes hvac_mode:
- Need to intelligently choose P06 Unit Mode value
- If user has DHW enabled separately, preserve it
- Example logic:
  - `heat` + DHW active → P06 = 3 (Heating + DHW)
  - `heat` + DHW inactive → P06 = 1 (Heating Only)
  - `cool` + DHW active → P06 = 4 (Cooling + DHW)
  - `cool` + DHW inactive → P06 = 2 (Cooling Only)

### 2. Temperature Differential

Climate entity doesn't have a "differential" attribute.
- Expose P03/P05 (temp diff) as separate number entities
- Document in climate entity description: "Temperature differential controlled via P03/P05 number entities"

### 3. Economic Mode Integration

When preset_mode = "eco":
- Could enable G09 (automatic mode control)
- Or just set fan_mode to Economic
- Document that economic curve points (E01-E24) are set via number entities

### 4. DHW Control

**Option A**: Separate switch
- Keep DHW separate (use existing number entity for DHW setpoint)
- Climate only controls space heating/cooling

**Option B**: DHW as preset_mode
- Add `dhw` preset mode
- When enabled, changes P06 to include +DHW
- Still need number entity for DHW temperature

**Recommended**: Option A - keep DHW separate

## Files to Modify

To implement Option 1:

1. **Create new file**: `custom_components/sprsun_modbus/climate.py`
   - Implement `SPRSUNClimate(CoordinatorEntity, ClimateEntity)`
   - Map hvac_modes to P06 values
   - Handle setpoint reading/writing
   - Implement fan_mode mapping

2. **Update**: `custom_components/sprsun_modbus/const.py`
   - Add `"climate"` to PLATFORMS list

3. **Update**: `custom_components/sprsun_modbus/__init__.py`
   - No changes needed (climate platform auto-loaded)

4. **Update docs**: Add climate entity documentation

## Example Climate Implementation Outline

```python
class SPRSUNClimate(CoordinatorEntity, ClimateEntity):
    \"\"\"SPRSUN Heat Pump Climate Entity.\"\"\"
    
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.PRESET_MODE
    )
    
    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.HEAT,
        HVACMode.COOL,
        HVACMode.HEAT_COOL,  # Auto mode
    ]
    
    _attr_fan_modes = ["normal", "eco", "night", "test"]
    _attr_preset_modes = [PRESET_NONE, PRESET_ECO, PRESET_BOOST]
    
    @property
    def hvac_mode(self) -> HVACMode:
        \"\"\"Return current HVAC mode based on power and unit mode.\"\"\"
        # Read from coordinator.data
        # Map P06 + power state to hvac_mode
        
    @property
    def current_temperature(self) -> float:
        \"\"\"Return outlet temperature.\"\"\"
        return self.coordinator.data.get("outlet_temp")
    
    @property
    def target_temperature(self) -> float:
        \"\"\"Return target based on current mode.\"\"\"
        # Return P01 if heating, P02 if cooling
        
    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        \"\"\"Set HVAC mode (maps to power switch + P06).\"\"\"
        # Write to coordinator via write_register
        
    async def async_set_temperature(self, **kwargs) -> None:
        \"\"\"Set target temperature (writes to P01 or P02).\"\"\"
        # Write to appropriate register based on current mode
```

## Decision Matrix

| Feature | No Climate | Single Climate | Multiple Climates |
|---------|-----------|----------------|-------------------|
| Voice Control | ❌ | ✅ | ⚠️ Confusing |
| HA Climate Card | ❌ | ✅ | ⚠️ Multiple cards |
| Simple UI | ❌ | ✅ | ❌ |
| Full Control | ✅ | ⚠️ Need numbers too | ⚠️ Need numbers too |
| DHW Control | ✅ Number | ⚠️ Separate | ✅ Dedicated entity |
| User Learning | ❌ High | ✅ Low | ⚠️ Medium |
| Implementation | ✅ Done | ⚠️ Medium effort | ❌ Complex |

## Final Recommendation

**Implement Single Climate Entity (Option 1)** as an OPTIONAL convenience layer:

- Provides standard thermostat interface for 90% of use cases
- Keeps all existing number/select/switch entities for advanced control
- Users can choose to hide climate entity if they prefer granular control
- Makes the integration more accessible to non-technical users
- Enables voice control and standard HA automations

The climate entity serves as a "simplified facade" while power users retain full access to all parameters via the existing entities. This is the best of both worlds approach.
