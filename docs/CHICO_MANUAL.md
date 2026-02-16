# Function Description of Full DC Frequency Converter

## 1. Main Interface (Simple Graphic)

① **Heating / Cooling temperature display**:
   - Displays the current cooling real-time temperature in blue fonts
   - Displays the current real-time heating temperature in orange font
   - In the upper left corner of the temperature display, when there is ❄ or 🔥 icon, it indicates that the unit is running the cooling or heating mode

② **Displays the fan mode of the current unit**:
   - ☀ indicates day mode
   - 🌙 indicates night mode
   - 💰 indicates economic mode
   - 🔧 indicates test mode

③ **Hot water temperature display**:
   - Displays the current hot water temperature in red font
   - In the upper left corner of the temperature display, when there is 💧 icon, it indicates that the unit is running the hot water mode

④ **Simple graph and dynamic graph switching**: Click the icon to switch between simple graph and dynamic graph

⑤ Click to check the current fault alarms and historical fault alarms

⑥ **The display of heat pump status on the right below corner**: The running status of heat pump is displayed here

⑦ **Timing setting**: Click to enter into timing setting; in red when there is a timing, in white when there is no timing

⑧ **System parameter setting**: Click this icon to enter the setting interface

⑨ **Mode setting**: Click this icon to enter the mode setting interface

⑩ **Power on and off**: Click the icon to operate the power on and off. Shows red when it is turned on, and shows white when it is turned off

## 2. Dynamic Graph

① **Hot water tank temperature**

② **Hot water setting temperature**: Click here to enter the temperature setting

③ **Current working mode**:
   - ❄ is Cooling mode
   - 🔥 is heating mode

④ **Current cooling/heating temperature**: When the current mode is cooling mode, display the current cooling temperature. When the current temperature is in heating mode, the current heating temperature is displayed

⑤ **Cooling/heating setting temperature**: Click here to enter the temperature setting

⑥ **Click the unit icon** to set the power on/off

## 3. Turn ON/OFF

Click to set the unit on/off. If the icon is in white color, it means that the current unit is off. And if icon is in red color, it means that current unit is on.

## 4. Mode Switch

Click to set the unit mode. After selecting the required mode, click ✓ to confirm, and click ✗ to Cancel and exit the page.

## 5. Temperature Setting

Click the ①② position of the real-time temperature to enter the temperature setting interface.

Set the temperature and hysteresis of each mode in the temperature setting interface:

- **Cooling setp.**: Cooling stop temperature setting
- **Heating setp.**: Heating stop temperature setting
- **Temp. Diff.**: When running heating/cooling mode, the difference between the unit's shutdown temperature and the set temperature after reaching the setting temperature
- **Hotwater setp.**: Hot water tank temperature stop temperature setting
- **Temp. Diff.**: When running hot water mode, the difference between the unit's shutdown temperature and the set temperature after reaching the setting temperature

## 6. Timer Setting

Press the ⏰ button to pop up the timing control interface, and set the timing in the timing control interface.

**Timing period is not enabled/enabled**: The switch is left when not enabled, and the switch is right when enabled

- **ON**: Set for the timing power-on time
- **OFF**: Set for timing off time
- **Timeband1/2/3**: Means that there are three timings that can be set, and each timing can set different hot water, heating and cooling temperatures

## 7. Parameters Query and Setting

Press 🔧 to Main Menu as below:

### ① User Parameters

Press for user parameter setting:

- **P01 Heating setp.**: Heating shutdown temperature
- **P02 Cooling setp.**: Cooling shutdown temperature
- **P03 Temp. Diff.**: The difference between the unit's shutdown temperature and the setting temperature after reaching the setting temperature
- **P04 Hotwater setp.**: Hotwater heating shutdown temperature
- **P05 Temp. Diff.**: When the machine is operating hot water mode, the difference between the unit's shutdown temperature and the set temperature after reaching the setting temperature
- **P06 Unit mode**: Modes choice of heat pumps
- **P07 Fan mode**: Modes choice of fans. Day Mode, Economic Mode, Testing Mode and Night Mode are optional
  - **Daytime** - Day mode, the compressor outputs according to the maximum capacity
  - **Pressure** - Test mode, the heat pump outputs according to the test capacity
  - **ECO mode** - Economic mode, the heat pump can automatically output capacity as required according to the ambient temperature
  - **Night mode** - The heat pump has low output capacity from 8 pm to 8 am, and high output at other times
  - **Test mode** - Factory debug mode for performance

### ② Parameter Query

Click to check the operating parameters.

When a single unit is running, the 1# Unit icon is to the right, click 1# unit to query the operating parameters of the 1# unit; if there is a linkage network, you can click 2#, 3#...8# to query the operating parameters of the corresponding unit, and the software version number. If the unit icon is displayed gray, the unit is not connected.

### ③ Temperature Curves

Press this to check the curves of heating temperature, outlet water temperature, and hot water tank temperature changing with running time.

### ④ Engineering Parameters

Click here and enter the password to set the engineering parameter. This password is only provided for the construction contractor, if needed, please contact our engineers, it can be operated after receiving our authorization.

**ECO Mode Settings**:
Click to enter the setting of relevant parameter on ECO mode.

**High Temperature Sterilization Mode**:
Click to enter relevant parameter settings for high temperature sterilization mode:

- **Enable antilegionella**: Disable or enable sterilization function, right is enable
- **Temp. Setpoint**: Sterilization temperature setting
- **Weekday**: Sterilization work days, once a week
- **TIMER**: Sterilization time point, once a week

**Language Selection**:
Press to enter the language selection interface.

**Project Parameters**:
Press to access the relevant settings of project parameters:

- **Two/Three function**: Click "two" and "three" to select whether the current unit is double supply or triple supply
- **DC Pump work**: The working mode of the inverter water pump can be selected as demand, always on, intermittently on
- **Start internal**: The interval time for the start of the inverter water pump in intermittent mode
- **Delta temp. set**: The inverter water pump controls the current temperature difference between the incoming and outgoing water
- **Heating heater Ext.**: Start-up ambient temperature of heating electric heater
- **Comp. Delay**: Heating electric heater start delay
- **Hotwater heater Ext.**: Start-up ambient temperature of hot water electric heater
- **Comp. Delay**: Hot water electric heater start delay

#### Notice:

(1) At present, the factory wiring is to connect the heating electric heater (OUT4) and the hot water electric heater (OUT12) at the terminal, so in actual use, pay attention to the location of the electric heater. If you use our matching heat pump kits, you can use it directly.

(2) If you use external electric heater by yourself, you need to use pipeline electric heater and install it in the specified water flow path, as shown in the following figure.

**Enable Switch** (Automatic Cooling/Heating):

With this function, the heat pump can do heating/cooling automatically based on the ambient temperature setting:

- **Enable Switch - No**: Turn off the automatic cooling/heating mode which is based on the ambient temperature; Original setting is Disable before delivery
- **Enable Switch - Yes**: Turn on the automatic cooling/heating mode which is based on the ambient temperature
- **AmbTemp Switch setp.**: Switch the ambient temperature setting point of the cooling/heating mode
  - When the ambient temperature is lower than the set point-hysteresis, the unit will automatically switch to heating or hot water + heating
  - When the ambient temperature is higher than the set point + hysteresis, the unit will automatically switch to cooling or hot water + refrigeration
  - When the ambient temperature is higher than the set point-hysteresis and lower than the set point + hysteresis maintains the current mode
- **Amb Temp.diff**: The difference between the ambient temperature switching mode and the set temperature

**Number of Unit**:
When the units are networked and the operating parameters of multiple units need to be queried, select the corresponding number of units.

**Fault reset**:
Reset current fault.

### ⑤ Factory Parameters

Press here and enter the password to query and set the factory parameters, this password needs to contact the technical engineer, and the operation can only be done after authorization.

## 8. Current/Historical Alarm Query

The flashing ⚠ icon in the upper right corner indicates that there is an alarm. Press this icon to pop up the current alarm interface.

- Press 🗑️ to show a dialog box for whether to delete historical alarms, press "YES" to delete historical alarms, and press "NO" to cancel the operation
- Press 🔄 to switch between current alarm and historical alarm
- Press ← to return to main menu

## 9. Cascade

### Module Cascade Operation Instructions:

**9.1** Connect each module with the matching quick connection cable as shown in the figure below. The display is connected to the 1# host, and the slave does not need to be connected to the display.

**9.2** Each unit needs to set the unit number, the host is set to 1, and the other units are set to 2, 3, 4...n in turn. If two or more units have the same unit number, they cannot communicate normally, please restart set up.

**9.3** The unit number setting using the 2-4 bits of the DIP switch SW1 on the main board, the location is as shown in the figure below.

**9.4** The unit number setting method is as follows:

| Unit | SW1-2 | SW1-3 | SW1-4 |
|------|-------|-------|-------|
| #1   | OFF   | OFF   | OFF   |
| #2   | OFF   | OFF   | ON    |
| #3   | OFF   | ON    | OFF   |
| #4   | OFF   | ON    | ON    |
| #5   | ON    | OFF   | OFF   |
| #6   | ON    | OFF   | ON    |
| #7   | ON    | ON    | OFF   |
| #8   | ON    | ON    | ON    |

For example, 1# and 2# are set as shown below.

**9.5** Open the screen as shown in the following figure. Set the G12 Number of Unit parameter to the number of units connected online. If there are 4 units, set it to 4, and if there are 8 units, set it to 8. The maximum setting number is 8.

**9.6** After all the above operations are completed, you can start up and debug the unit. If all units are connected normally, the circle behind the unit will be green, as shown in the figure below. Click each unit number to view the operating parameters of each unit.

## 10. WIFI Module Connection

### 1. Accessories Required for Module Connection

- Signal line
- Power supply connecting line
- WIFI module

**Connection Note**: 
When connecting the signal line, pay attention to the position of the red line and the white line. The red end is connected to the A of the connection line, and the other end is connected to the A of the main control board; the white end is connected to the B of the connection line, and the other end is connected to the B of the main control board communication.

The power plug is connected to the 230V power supply. The black and white line of the power cable is connected to the + of the connecting line, and the black line is connected to the - of the connecting line. If the connection is reversed, the module cannot supply power.

### APP Add Equipment

When it is used for the first time, the WIFI module needs to be equipped with a network to use it. The network configuration steps are as follows:

#### Step 1: Register

After downloading the APP, enter the APP landing page. Click the new user to register with the mobile phone number or email. After successful registration, enter the user name and password and click to log in. (App download needs to scan the QR code below, and then choose to open in the browser to download)

- QR code Registration interface
- Mobile Registration
- Email Registration

#### Step 2: Add Devices on the LAN

Modules that have not been connected to the network require the LAN to add devices. After entering my device, click the icon in the upper left corner to enter the add device page, the above box will display the name of the WIFI currently connected to the phone, enter the WIFI password, first gently press the raised button of the connection line, and then click add device, until it shows that the connection is successful, then click the arrow, you can see the currently connected APP is displayed in the list.

Click the button of the module, then its green light will flash to enter the distribution network mode.

#### Scanning the QR Code to Add Devices

For the modules which have binding APP, you can scan the QR code to add devices. If the module has been connected to the network, it will be automatically connected to the network after power-up. Moreover for modules binding APP previously, click the icon on the left side of the APP device list to display its QR code. If others want to bind this module, click the icon directly and then scan the QR code.

#### Explanation

1) The device list displays the device associated with this user, and shows the device's online and offline status. When the device is offline, the device icon is gray, and the device is online color.

2) The switch on the right side of each device row indicates whether the device is currently turned on.

3) The user can disassociate with the device or modify the device name. When swiping to the left, the delete and edit buttons appear on the right side of the device row. Click Edit to modify the device name, and click Delete to disassociate the device.

4) When adding a device to the local area network, the App will connect the device to the local area network through the local area network WiFi connected to the mobile phone. If you want to connect the device to the specified WiFi, please select the WiFi in the wireless LAN set in the mobile phone before returning to this page.

5) The App must follow the privacy and safe use of mobile phones, so before entering this page to add a device, the App will ask the user if they agree to access the user's location. If it is not allowed, the App will not be able to complete the LAN addition of the device.

6) The WiFi icon on the page shows the name of the local area network WiFi connected to the mobile phone. In the input box under the WiFi name, the user needs to fill in the WiFi connection password. The user can click on the eye icon to confirm that the password is filled in correctly.

7) Short press the module's network distribution button, and confirm whether the device has entered the connectable state. The device's connection indicator flashes at a high speed to indicate that it has entered the network ready state), and then click the add device button, and the App will automatically add and bind the device. Click the question mark icon in the lower right corner of the password input box, you can see detailed help instructions.

8) The process of adding a device includes the connection and adding process of the device. The connection process refers to the device connecting to the local area network, and the addition process refers to adding the device to the user's device list. After the device is successfully added, the user can use the device. The process information for adding a device is as follows:
   - Start connecting devices
   - The device connection succeeds or fails
   - Start adding devices
   - The device is successfully added or failed

### Use of APP

#### 1.1. Device Homepage

**Explanation:**

1) Click a device in the device list to enter this page.

2) The background color of the bubble indicates the current operating state of the device:
   - a. Gray indicates that the device is in the shutdown state, at this time, you can change the working mode, set the mode temperature, set the timing, or you can press the key to switch on and off
   - b. Multicolor indicates that the device is turned on, each working mode corresponds to a different color, orange indicates heating mode, red indicates hot water mode, and blue indicates cooling mode
   - c. When the device is in the power-on state, you can set the mode temperature, set the timer, press the key to switch on and off, but you can not set the working mode (that is, the working mode can only be set when the device is off)

3) The bubble shows the current temperature of the device.

4) Below the bubble is the set temperature of the device in the current operating mode. Click the +, - buttons on the left and right sides of the set temperature, and each time the current setting value is transmitted plus 1 or minus 1, it is set to the device.

Set the status category to fault alarm. When the device alarms, the alarm reason will be displayed next to the alarm icon. When a fault alarm occurs in the device, the area related to the fault alarm code will be displayed in green in this area. Click this area to jump to the detailed fault alarm page in the specific area.

Immediately below the fault alarm area, the current working mode, heat pump, fan, and compressor ON status are displayed in sequence (there is a corresponding blue icon when it is turned on, and it is not displayed when it is turned off).

The slider at the bottom is used to set the temperature in the current mode. Slide the slider left and right to set the allowable temperature value in the current working mode.

There are three buttons at the bottom, from left to right: working mode, device power on and off, device timing.

Click the working mode to see the mode selection menu, you can set the working mode of the device (black is the current setting mode of the device).

Click the device on/off, and set the on/off command to the device.

Click the device timing to see the timing setting menu, adjust the enable button on the right to the right, then the group timing is valid, and the current timing is invalid when it is on the left.

#### Device Details

**Explanation:**

Click the menu in the upper right corner of the device main page to enter this page.

**Users with manufacturer privileges** can see all the functions of the device, with the following labels:
- User parameters
- Parameter query
- Economic mode
- Engineering parameters
- Main expansion valve settings
- Auxiliary expansion valve settings
- Defrost settings
- Fan settings
- Other parameter reading
- Parameter settings
- Frequency settings
- Timing settings
- Faults

**Users with user rights** can see some device functions:
- User parameters
- Parameter query
- Economic mode
- Engineering parameters
- Faults
