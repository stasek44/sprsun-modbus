| **<br>**                                      |                         |       |            |       |                                                                   |                                                          |
| --------------------------------------------- | ----------------------- | ----- | ---------- | ----- | ----------------------------------------------------------------- | -------------------------------------------------------- |
| **<br>**                                      | DATA(EN)                | add   | modbus add | byte  | data type                                                         | NOTE                                                     |
| **User parameters**                           | Mode setP               | 0     | 40001      | 1     | int                                                               | 0:Cooling ;1:Heating ;2:DHW ;3:Cooling+DHW;4:Heating+DHW |
| Heat SetP                                     | 1                       | 40002 | 1          | REAL  | 10.0~CoolHeatMng.heat_set_max（CoolHeatMng.heat_set_max:-99~100）   |
| Cool SetP                                     | 2                       | 40003 | 1          | REAL  | CoolHeatMng.cool_set_min~40.0（CoolHeatMng.cool_set_min:-99-100.0） |
| Hotwater SetP                                 | 3                       | 40004 | 1          | REAL  | 10-CoolHeatMng.heat_set_max（CoolHeatMng.heat_set_max:-99.0~100）   |
| hotwater_start_diff                           | 4                       | 40005 | 1          | REAL  | 1.0~15.0                                                          |
| hotwater_stop_diff                            | 5                       | 40006 | 1          | REAL  | 0.0~5.0                                                           |
| heat/cool start_Diff                          | 6                       | 40007 | 1          | REAL  | 1.0~15.0                                                          |
| heat/cool stop_Diff                           | 7                       | 40008 | 1          | REAL  | 0.0~5.0                                                           |
| **Engineering parameters**                    | Heater type             | 323   | 40324      | 1     | INT                                                               | 0:disalbe 1：hotwater 2：heating 3：all 4:independent       |
| Pump Mode                                     | 11                      | 40012 | 1          | int   | 0:normal ;1:demand; 2:ineterval                                   |
| Fan Mode                                      | 12                      | 40013 | 1          | int   | 0:daytime; 1:night; 2:ECO mode; 3T:presure                        |
| E/H comp.delay                                | 13                      | 40014 | 1          | UINT  | 0-999                                                             |
| Ext.temp.setp.                                | 14                      | 40015 | 1          | real  | \-30.0~20.0                                                       |
| **Status query**                              | Unit On/OFF             | 0     | 10001      | 1     | BOOL                                                              | 0:OFF 1:ON                                               |
| Inlet Temp.                                   | 188                     | 40189 | 1          | REAL  | 0:OFF 2:ON                                                        |
| Outlet Temp.                                  | 189                     | 40190 | 1          | REAL  | 0:OFF 3:ON                                                        |
| Amb.Temp.                                     | 190                     | 40191 | 1          | REAL  | 0:OFF 4:ON                                                        |
| Disch.gas Temp.                               | 191                     | 40192 | 1          | REAL  | 0:OFF 5:ON                                                        |
| Suct.gas Temp.                                | 192                     | 40193 | 1          | REAL  | 0:OFF 6:ON                                                        |
| Disch.press                                   | 193                     | 40194 | 1          | REAL  | 0:OFF 7:ON                                                        |
| Suct.press                                    | 194                     | 40195 | 1          | REAL  | 0:OFF 8:ON                                                        |
| hotwater temp                                 | 195                     | 40196 | 1          | REAL  | 0:OFF 9:ON                                                        |
| Coil Temp.                                    | 196                     | 40197 | 1          | REAL  | 0:OFF 10:ON                                                       |
| Flow switch                                   | 1                       | 10002 | 1          | BOOL  | 0:OFF 11:ON                                                       |
| A/C linkage switch                            | 3                       | 10004 | 1          | BOOL  | 0:OFF 12:ON                                                       |
| SG_Signal                                     | 4                       | 10005 | 1          | BOOL  | 0:OFF 13:ON                                                       |
| EVU_Signal                                    | 187                     | 10188 | 1          | BOOL  | 0:OFF 14:ON                                                       |
| Outputs.DoutVal_1                             | 5                       | 10006 | 1          | BOOL  | 0:NO 1:OFF                                                        |
| Outputs.DoutVal_9                             | 12                      | 10013 | 1          | BOOL  | 0:NO 1:OFF                                                        |
| Four way valve On/OFF status                  | 7                       | 10008 | 1          | BOOL  | 0:NO 1:OFF                                                        |
| Pump On/OFF status                            | 8                       | 10009 | 1          | BOOL  | 0:NO 1:OFF                                                        |
| Three way valve On/OFF status                 | 9                       | 10010 | 1          | BOOL  | 0:NO 1:OFF                                                        |
| Crank.heater On/OFF status                    | 10                      | 10011 | 1          | BOOL  | 0:NO 1:OFF                                                        |
| chassis heater On/OFF status                  | 11                      | 10012 | 1          | BOOL  | 0:NO 1:OFF                                                        |
| Fan output(%)                                 | 197                     | 40198 | 1          | REAL  |                                                                   |
| Pump out(%)                                   | 198                     | 40199 | 1          | REAL  |                                                                   |
| Fan2 RPM                                      | 200                     | 40201 | 1          | INT   |                                                                   |
| Fan1 RPM                                      | 202                     | 40203 | 1          | INT   |                                                                   |
| COMP.RPM                                      | 205                     | 40206 | 1          | REAL  |                                                                   |
| EEV1 Steps                                    | 207                     | 40208 | 1          | INT   |                                                                   |
| unit run mode                                 | 215                     | 40216 | 1          | INT   | 0：Cooling 1：Heating 2：DHW                                         |
| Comp On/OFF status                            | 179                     | 10180 | 1          | BOOL  |                                                                   |
| Fan On/OFF status                             | 180                     | 10181 | 1          | BOOL  |                                                                   |
| GeneralMng.CurrVer.X                          | 325                     | 40326 | 1          | INT   |                                                                   |
| GeneralMng.CurrVer.Y                          | 326                     | 40327 | 1          | INT   |                                                                   |
| GeneralMng.CurrVer.Z                          | 327                     | 40328 | 1          | INT   |                                                                   |
| GeneralMng.UnitType_A                         | 328                     | 40329 | 1          | INT   |                                                                   |
| GeneralMng.UnitType_B                         | 329                     | 40330 | 1          | INT   |                                                                   |
| BLDC_POwer                                    | 333                     | 40334 | 1          | real  |                                                                   |
| BLDC_Var                                      | 334                     | 40335 | 1          | int   |                                                                   |
| BLDC_Curret                                   | 335                     | 40336 | 1          | real  |                                                                   |
| WorkingHours.Pump                             | 364                     | 40365 | 2          | UDINT |                                                                   |
| WorkingHours.Comp                             | 366                     | 40367 | 2          | UDINT |                                                                   |
| WorkingHours.Fan                              | 368                     | 40369 | 2          | UDINT |                                                                   |
| WorkingHours.Three way valve                  | 370                     | 40371 | 2          | UDINT |                                                                   |
| Water Flow Value                              | 372                     | 40373 | 2          | real  | L/h                                                               |
| Unit Power                                    | 387                     | 40388 | 2          | real  | W                                                                 |
| Unit_COP                                      | 389                     | 40390 | 1          | real  |                                                                   |
| **time setting**                              | Year                    | 182   | 40183      | 1     | UINT                                                              | 0~99                                                     |
| Month                                         | 183                     | 40184 | 1          | UINT  | 0~12                                                              |
| Day                                           | 184                     | 40185 | 1          | UINT  | 0~31                                                              |
| Hour                                          | 185                     | 40186 | 1          | UINT  | 0~23                                                              |
| Minute                                        | 186                     | 40187 | 1          | UINT  | 0~59                                                              |
| Week                                          | 187                     | 40188 | 1          | UINT  | 1~7                                                               |
| timezone on/off enable                        | 38                      | 00039 | 1          | bool  |                                                                   |
| timezone setpoing enable                      | 39                      | 00040 | 1          | bool  |                                                                   |
| save time                                     | 43                      | 00044 | 1          | bool  |                                                                   |
| **Timing on/off settings**                    | Timezone1 Mon. ON: hour | 218   | 40219      | 1     | INT                                                               | 0-23                                                     |
| Timezone1 Mon. ON: minute                     | 219                     | 40220 | 1          | INT   | 0-59                                                              |
| Timezone1 Tue. ON: hour                       | 220                     | 40221 | 1          | INT   | 0-23                                                              |
| Timezone1 Tue. ON: minute                     | 221                     | 40222 | 1          | INT   | 0-59                                                              |
| Timezone1 Wed. ON: hour                       | 222                     | 40223 | 1          | INT   | 0-23                                                              |
| Timezone1 Wed. ON: minute                     | 223                     | 40224 | 1          | INT   | 0-59                                                              |
| Timezone1 Thu. ON: hour                       | 224                     | 40225 | 1          | INT   | 0-23                                                              |
| Timezone1 Thu. ON: minute                     | 225                     | 40226 | 1          | INT   | 0-59                                                              |
| Timezone1 Fri. ON: hour                       | 226                     | 40227 | 1          | INT   | 0-23                                                              |
| Timezone1 Fri. ON: minute                     | 227                     | 40228 | 1          | INT   | 0-59                                                              |
| Timezone1 Sat. ON: hour                       | 228                     | 40229 | 1          | INT   | 0-23                                                              |
| Timezone1 Sat. ON: minute                     | 229                     | 40230 | 1          | INT   | 0-59                                                              |
| Timezone1 Sun. ON: hour                       | 230                     | 40231 | 1          | INT   | 0-23                                                              |
| Timezone1 Sun. ON: minute                     | 231                     | 40232 | 1          | INT   | 0-59                                                              |
| Timezone1 Mon. OFF: hour                      | 232                     | 40233 | 1          | INT   | 0-23                                                              |
| Timezone1 Mon. OFF: minute                    | 233                     | 40234 | 1          | INT   | 0-59                                                              |
| Timezone1 Tue. OFF: hour                      | 234                     | 40235 | 1          | INT   | 0-23                                                              |
| Timezone1 Tue. OFF: minute                    | 235                     | 40236 | 1          | INT   | 0-59                                                              |
| Timezone1 Wed. OFF: hour                      | 236                     | 40237 | 1          | INT   | 0-23                                                              |
| Timezone1 Wed. OFF: minute                    | 237                     | 40238 | 1          | INT   | 0-59                                                              |
| Timezone1 Thu. OFF: hour                      | 238                     | 40239 | 1          | INT   | 0-23                                                              |
| Timezone1 Thu. OFF: minute                    | 239                     | 40240 | 1          | INT   | 0-59                                                              |
| Timezone1 Fri. OFF: hour                      | 240                     | 40241 | 1          | INT   | 0-23                                                              |
| Timezone1 Fri. OFF: minute                    | 241                     | 40242 | 1          | INT   | 0-59                                                              |
| Timezone1 Sat. OFF: hour                      | 242                     | 40243 | 1          | INT   | 0-23                                                              |
| Timezone1 Sat. OFF: minute                    | 243                     | 40244 | 1          | INT   | 0-59                                                              |
| Timezone1 Sun. OFF: hour                      | 244                     | 40245 | 1          | INT   | 0-23                                                              |
| Timezone1 Sun. OFF: minute                    | 245                     | 40246 | 1          | INT   | 0-59                                                              |
| Timezone2 Mon. ON: hour                       | 432                     | 40433 | 1          | INT   | 0-23                                                              |
| Timezone2 Mon. ON: minute                     | 433                     | 40434 | 1          | INT   | 0-59                                                              |
| Timezone2 Tue. ON: hour                       | 434                     | 40435 | 1          | INT   | 0-23                                                              |
| Timezone2 Tue. ON: minute                     | 435                     | 40436 | 1          | INT   | 0-59                                                              |
| Timezone2 Wed. ON: hour                       | 436                     | 40437 | 1          | INT   | 0-23                                                              |
| Timezone2 Wed. ON: minute                     | 437                     | 40438 | 1          | INT   | 0-59                                                              |
| Timezone2 Thu. ON: hour                       | 438                     | 40439 | 1          | INT   | 0-23                                                              |
| Timezone2 Thu. ON: minute                     | 439                     | 40440 | 1          | INT   | 0-59                                                              |
| Timezone2 Fri. ON: hour                       | 440                     | 40441 | 1          | INT   | 0-23                                                              |
| Timezone2 Fri. ON: minute                     | 441                     | 40442 | 1          | INT   | 0-59                                                              |
| Timezone2 Sat. ON: hour                       | 442                     | 40443 | 1          | INT   | 0-23                                                              |
| Timezone2 Sat. ON: minute                     | 443                     | 40444 | 1          | INT   | 0-59                                                              |
| Timezone2 Sun. ON: hour                       | 444                     | 40445 | 1          | INT   | 0-23                                                              |
| Timezone2 Sun. ON: minute                     | 445                     | 40446 | 1          | INT   | 0-59                                                              |
| Timezone2 Mon. OFF: hour                      | 446                     | 40447 | 1          | INT   | 0-23                                                              |
| Timezone2 Mon. OFF: minute                    | 447                     | 40448 | 1          | INT   | 0-59                                                              |
| Timezone2 Tue. OFF: hour                      | 448                     | 40449 | 1          | INT   | 0-23                                                              |
| Timezone2 Tue. OFF: minute                    | 449                     | 40450 | 1          | INT   | 0-59                                                              |
| Timezone2 Wed. OFF: hour                      | 450                     | 40451 | 1          | INT   | 0-23                                                              |
| Timezone2 Wed. OFF: minute                    | 451                     | 40452 | 1          | INT   | 0-59                                                              |
| Timezone2 Thu. OFF: hour                      | 452                     | 40453 | 1          | INT   | 0-23                                                              |
| Timezone2 Thu. OFF: minute                    | 453                     | 40454 | 1          | INT   | 0-59                                                              |
| Timezone2 Fri. OFF: hour                      | 454                     | 40455 | 1          | INT   | 0-23                                                              |
| Timezone2 Fri. OFF: minute                    | 455                     | 40456 | 1          | INT   | 0-59                                                              |
| Timezone2 Sat. OFF: hour                      | 456                     | 40457 | 1          | INT   | 0-23                                                              |
| Timezone2 Sat. OFF: minute                    | 457                     | 40458 | 1          | INT   | 0-59                                                              |
| Timezone2 Sun. OFF: hour                      | 458                     | 40459 | 1          | INT   | 0-23                                                              |
| Timezone2 Sun. OFF: minute                    | 459                     | 40460 | 1          | INT   | 0-59                                                              |
| **time zone**                                 | TimezoneMng.TempHr1     | 246   | 40247      | 1     | INT                                                               | 0-23                                                     |
| TimezoneMng.TempMin1                          | 247                     | 40248 | 1          | INT   | 0-59                                                              |
| TimezoneMng.S_Set_Temp1                       | 248                     | 40249 | 1          | REAL  | \-99.0~99.0                                                       |
| TimezoneMng.W_Set_Temp1                       | 249                     | 40250 | 1          | REAL  | \-99.0~99.0                                                       |
| TimezoneMng.TempHr2                           | 250                     | 40251 | 1          | INT   | 0-95                                                              |
| TimezoneMng.TempMin2                          | 251                     | 40252 | 1          | INT   | 0-131                                                             |
| TimezoneMng.S_Set_Temp2                       | 252                     | 40253 | 1          | REAL  | \-99.0~99.0                                                       |
| TimezoneMng.W_Set_Temp2                       | 253                     | 40254 | 1          | REAL  | \-99.0~99.0                                                       |
| TimezoneMng.TempHr3                           | 254                     | 40255 | 1          | INT   | 0-167                                                             |
| TimezoneMng.TempMin3                          | 255                     | 40256 | 1          | INT   | 0-203                                                             |
| TimezoneMng.S_Set_Temp3                       | 256                     | 40257 | 1          | REAL  | \-99.0~99.0                                                       |
| TimezoneMng.W_Set_Temp3                       | 257                     | 40258 | 1          | REAL  | \-99.0~99.0                                                       |
| TimezoneMng.TempHr4                           | 258                     | 40259 | 1          | INT   | 0-239                                                             |
| TimezoneMng.TempMin4                          | 259                     | 40260 | 1          | INT   | 0-275                                                             |
| TimezoneMng.S_Set_Temp4                       | 260                     | 40261 | 1          | REAL  | \-99.0~99.0                                                       |
| TimezoneMng.W_Set_Temp4                       | 261                     | 40262 | 1          | REAL  | \-99.0~99.0                                                       |
| **Error code**                                | Too many mem writings   | 13    | 10014      | 1     | BOOL                                                              | AL001                                                    |
| Retain mem write error                        | 14                      | 10015 | 1          | BOOL  | AL002                                                             |
| Inlet probe error                             | 15                      | 10016 | 1          | BOOL  | AL003                                                             |
| Outlet probe error                            | 16                      | 10017 | 1          | BOOL  | AL004                                                             |
| Ambient probe error                           | 17                      | 10018 | 1          | BOOL  | AL005                                                             |
| Condenser coil temp                           | 18                      | 10019 | 1          | BOOL  | AL006                                                             |
| Water flow switch                             | 19                      | 10020 | 1          | BOOL  | AL007                                                             |
| Phase sequ.prot.alarm                         | 20                      | 10021 | 1          | BOOL  | AL008                                                             |
| Unit work hour warning                        | 21                      | 10022 | 1          | BOOL  | AL009                                                             |
| Pump work hour warning                        | 22                      | 10023 | 1          | BOOL  | AL010                                                             |
| Comp.work hour warning                        | 23                      | 10024 | 1          | BOOL  | AL011                                                             |
| Cond.fan work hourWarn                        | 24                      | 10025 | 1          | BOOL  | AL012                                                             |
| Low superheat - Vlv.A                         | 25                      | 10026 | 1          | BOOL  | AL013                                                             |
| Low superheat - Vlv.B                         | 26                      | 10027 | 1          | BOOL  | AL014                                                             |
| LOP - Vlv.A                                   | 27                      | 10028 | 1          | BOOL  | AL015                                                             |
| LOP - Vlv.B                                   | 28                      | 10029 | 1          | BOOL  | AL016                                                             |
| MOP - Vlv.A                                   | 29                      | 10030 | 1          | BOOL  | AL017                                                             |
| MOP - Vlv.B                                   | 30                      | 10031 | 1          | BOOL  | AL018                                                             |
| Motor error - Vlv.A                           | 31                      | 10032 | 1          | BOOL  | AL019                                                             |
| Motor error - Vlv.B                           | 32                      | 10033 | 1          | BOOL  | AL020                                                             |
| Low suct.temp. - Vlv.A                        | 33                      | 10034 | 1          | BOOL  | AL021                                                             |
| Low suct.temp. - Vlv.B                        | 34                      | 10035 | 1          | BOOL  | AL022                                                             |
| High condens.temp.EVD                         | 35                      | 10036 | 1          | BOOL  | AL023                                                             |
| Probe S1 error EVD                            | 36                      | 10037 | 1          | BOOL  | AL024                                                             |
| Probe S2 error EVD                            | 37                      | 10038 | 1          | BOOL  | AL025                                                             |
| Probe S3 error EVD                            | 38                      | 10039 | 1          | BOOL  | AL026                                                             |
| Probe S4 error EVD                            | 39                      | 10040 | 1          | BOOL  | AL027                                                             |
| Battery discharge EVD                         | 40                      | 10041 | 1          | BOOL  | AL028                                                             |
| EEPROM alarm EVD                              | 41                      | 10042 | 1          | BOOL  | AL029                                                             |
| Incomplete closing EVD                        | 42                      | 10043 | 1          | BOOL  | AL030                                                             |
| Emergency closing EVD                         | 43                      | 10044 | 1          | BOOL  | AL031                                                             |
| FW not compatible EVD                         | 44                      | 10045 | 1          | BOOL  | AL032                                                             |
| Config. error EVD                             | 45                      | 10046 | 1          | BOOL  | AL033                                                             |
| EVD Driver offline                            | 46                      | 10047 | 1          | BOOL  | AL034                                                             |
| BLDC-alarm:High startup DeltaP                | 47                      | 10048 | 1          | BOOL  | AL035                                                             |
| BLDC-alarm:Compressor shut off                | 48                      | 10049 | 1          | BOOL  | AL036                                                             |
| BLDC-alarm:Out of Envelope                    | 49                      | 10050 | 1          | BOOL  | AL037                                                             |
| BLDC-alarm:Starting fail wait                 | 50                      | 10051 | 1          | BOOL  | AL038                                                             |
| BLDC-alarm:Starting fail exceeded             | 51                      | 10052 | 1          | BOOL  | AL039                                                             |
| BLDC-alarm:Low delta pressure                 | 52                      | 10053 | 1          | BOOL  | AL040                                                             |
| BLDC-alarm:High discarge gas temp             | 53                      | 10054 | 1          | BOOL  | AL041                                                             |
| Envelope-alarm:High compressor ratio          | 54                      | 10055 | 1          | BOOL  | AL042                                                             |
| Envelope-alarm:High discharge press.          | 55                      | 10056 | 1          | BOOL  | AL043                                                             |
| Envelope-alarm:High current                   | 56                      | 10057 | 1          | BOOL  | AL044                                                             |
| Envelope-alarm:High suction pressure          | 57                      | 10058 | 1          | BOOL  | AL045                                                             |
| Envelope-alarm:Low compressor ratio           | 58                      | 10059 | 1          | BOOL  | AL046                                                             |
| Envelope-alarm:Low pressure diff.             | 59                      | 10060 | 1          | BOOL  | AL047                                                             |
| Envelope-alarm:Low discharge pressure         | 60                      | 10061 | 1          | BOOL  | AL048                                                             |
| Envelope-alarm:Low suction pressure           | 61                      | 10062 | 1          | BOOL  | AL049                                                             |
| Envelope-alarm:High discharge temp.           | 62                      | 10063 | 1          | BOOL  | AL050                                                             |
| Power+ alarm:01-Overcurrent                   | 63                      | 10064 | 1          | BOOL  | AL051                                                             |
| Power+ alarm:02-Motor overload                | 64                      | 10065 | 1          | BOOL  | AL052                                                             |
| Power+ alarm:03-DCbus overvoltage             | 65                      | 10066 | 1          | BOOL  | AL053                                                             |
| Power+ alarm:04-DCbus undervoltage            | 66                      | 10067 | 1          | BOOL  | AL054                                                             |
| Power+ alarm:05-Drive overtemp.               | 67                      | 10068 | 1          | BOOL  | AL055                                                             |
| Power+ alarm:06-Drive undertemp.              | 68                      | 10069 | 1          | BOOL  | AL056                                                             |
| Power+ alarm:07-Overcurrent HW                | 69                      | 10070 | 1          | BOOL  | AL057                                                             |
| Power+ alarm:08-Motor overtemp.               | 70                      | 10071 | 1          | BOOL  | AL058                                                             |
| Power+ alarm:09-IGBT module error             | 71                      | 10072 | 1          | BOOL  | AL059                                                             |
| Power+ alarm:10-CPU error                     | 72                      | 10073 | 1          | BOOL  | AL060                                                             |
| Power+ alarm:11-Parameter default             | 73                      | 10074 | 1          | BOOL  | AL061                                                             |
| Power+ alarm:12-DCbus ripple                  | 74                      | 10075 | 1          | BOOL  | AL062                                                             |
| Power+ alarm:13-Data comm. Fault              | 75                      | 10076 | 1          | BOOL  | AL063                                                             |
| Power+ alarm:14-Thermistor fault              | 76                      | 10077 | 1          | BOOL  | AL064                                                             |
| Power+ alarm:15-Autotuning fault              | 77                      | 10078 | 1          | BOOL  | AL065                                                             |
| Power+ alarm:16-Drive disabled                | 78                      | 10079 | 1          | BOOL  | AL066                                                             |
| Power+ alarm:17-Motor phase fault             | 79                      | 10080 | 1          | BOOL  | AL067                                                             |
| Power+ alarm:18-Internal fan fault            | 80                      | 10081 | 1          | BOOL  | AL068                                                             |
| Power+ alarm:19-Speed fault                   | 81                      | 10082 | 1          | BOOL  | AL069                                                             |
| Power+ alarm:20-PFC module error              | 82                      | 10083 | 1          | BOOL  | AL070                                                             |
| Power+ alarm:21-PFC overvoltage               | 83                      | 10084 | 1          | BOOL  | AL071                                                             |
| Power+ alarm:22-PFC undervoltage              | 84                      | 10085 | 1          | BOOL  | AL072                                                             |
| Power+ alarm:23-STO DetectionError            | 85                      | 10086 | 1          | BOOL  | AL073                                                             |
| Power+ alarm:24-STO DetectionError            | 86                      | 10087 | 1          | BOOL  | AL074                                                             |
| Power+ alarm:25-Ground fault                  | 87                      | 10088 | 1          | BOOL  | AL075                                                             |
| Power+ alarm:26-Internal error 1              | 88                      | 10089 | 1          | BOOL  | AL076                                                             |
| Power+ alarm:27-Internal error 2              | 89                      | 10090 | 1          | BOOL  | AL077                                                             |
| Power+ alarm:28-Drive overload                | 90                      | 10091 | 1          | BOOL  | AL078                                                             |
| Power+ alarm:29-uC safety fault               | 91                      | 10092 | 1          | BOOL  | AL079                                                             |
| Power+ alarm:98-Unexpected restart            | 92                      | 10093 | 1          | BOOL  | AL080                                                             |
| Power+ alarm:99-Unexpected stop               | 93                      | 10094 | 1          | BOOL  | AL081                                                             |
| Power+ safety alarm:01-Current meas.fault     | 94                      | 10095 | 1          | BOOL  | AL082                                                             |
| Power+ safety alarm:02-Current unbalanced     | 95                      | 10096 | 1          | BOOL  | AL083                                                             |
| Power+ safety alarm:03-Over current           | 96                      | 10097 | 1          | BOOL  | AL084                                                             |
| Power+ safety alarm:04-STO alarm              | 97                      | 10098 | 1          | BOOL  | AL085                                                             |
| Power+ safety alarm:05-STO hardware alarm     | 98                      | 10099 | 1          | BOOL  | AL086                                                             |
| Power+ safety alarm:06-PowerSupply missing    | 99                      | 10100 | 1          | BOOL  | AL087                                                             |
| Power+ safety alarm:07-HW fault cmd.buffer    | 100                     | 10101 | 1          | BOOL  | AL088                                                             |
| Power+ safety alarm:08-HW fault heater c.     | 101                     | 10102 | 1          | BOOL  | AL089                                                             |
| Power+ safety alarm:09-Data comm. Fault       | 102                     | 10103 | 1          | BOOL  | AL090                                                             |
| Power+ safety alarm:10-Compr. stall detect    | 103                     | 10104 | 1          | BOOL  | AL091                                                             |
| Power+ safety alarm:11-DCbus over current     | 104                     | 10105 | 1          | BOOL  | AL092                                                             |
| Power+ safety alarm:12-HWF DCbus current      | 105                     | 10106 | 1          | BOOL  | AL093                                                             |
| Power+ safety alarm:13-DCbus voltage          | 106                     | 10107 | 1          | BOOL  | AL094                                                             |
| Power+ safety alarm:14-HWF DCbus voltage      | 107                     | 10108 | 1          | BOOL  | AL095                                                             |
| Power+ safety alarm:15-Input voltage          | 108                     | 10109 | 1          | BOOL  | AL096                                                             |
| Power+ safety alarm:16-HWF input voltage      | 109                     | 10110 | 1          | BOOL  | AL097                                                             |
| Power+ safety alarm:17-DCbus power alarm      | 110                     | 10111 | 1          | BOOL  | AL098                                                             |
| Power+ safety alarm:18-HWF power mismatch     | 111                     | 10112 | 1          | BOOL  | AL099                                                             |
| Power+ safety alarm:19-NTC over temp.         | 112                     | 10113 | 1          | BOOL  | AL100                                                             |
| Power+ safety alarm:20-NTC under temp.        | 113                     | 10114 | 1          | BOOL  | AL101                                                             |
| Power+ safety alarm:21-NTC fault              | 114                     | 10115 | 1          | BOOL  | AL102                                                             |
| Power+ safety alarm:22-HWF sync fault         | 115                     | 10116 | 1          | BOOL  | AL103                                                             |
| Power+ safety alarm:23-Invalid parameter      | 116                     | 10117 | 1          | BOOL  | AL104                                                             |
| Power+ safety alarm:24-FW fault               | 117                     | 10118 | 1          | BOOL  | AL105                                                             |
| Power+ safety alarm:25-HW fault               | 118                     | 10119 | 1          | BOOL  | AL106                                                             |
| Power+ safety alarm:26-reseved                | 119                     | 10120 | 1          | BOOL  | AL107                                                             |
| Power+ safety alarm:27-reseved                | 120                     | 10121 | 1          | BOOL  | AL108                                                             |
| Power+ safety alarm:28-reseved                | 121                     | 10122 | 1          | BOOL  | AL109                                                             |
| Power+ safety alarm:29-reseved                | 122                     | 10123 | 1          | BOOL  | AL110                                                             |
| Power+ safety alarm:30-reseved                | 123                     | 10124 | 1          | BOOL  | AL111                                                             |
| Power+ safety alarm:31-reseved                | 124                     | 10125 | 1          | BOOL  | AL112                                                             |
| Power+ safety alarm:32-reseved                | 125                     | 10126 | 1          | BOOL  | AL113                                                             |
| Power+ alarm:Power+ offline                   | 126                     | 10127 | 1          | BOOL  | AL114                                                             |
| EEV alarm:Low superheat                       | 127                     | 10128 | 1          | BOOL  | AL115                                                             |
| EEV alarm:LOP                                 | 128                     | 10129 | 1          | BOOL  | AL116                                                             |
| EEV alarm:MOP                                 | 129                     | 10130 | 1          | BOOL  | AL117                                                             |
| EEV alarm:High condens.temp.                  | 130                     | 10131 | 1          | BOOL  | AL118                                                             |
| EEV alarm:Low suction temp.                   | 131                     | 10132 | 1          | BOOL  | AL119                                                             |
| EEV alarm:Motor error                         | 132                     | 10133 | 1          | BOOL  | AL120                                                             |
| EEV alarm:Self Tuning                         | 133                     | 10134 | 1          | BOOL  | AL121                                                             |
| EEV alarm:Emergency closing                   | 134                     | 10135 | 1          | BOOL  | AL122                                                             |
| EEV alarm:Temperature delta                   | 135                     | 10136 | 1          | BOOL  | AL123                                                             |
| EEV alarm:Pressure delta                      | 136                     | 10137 | 1          | BOOL  | AL124                                                             |
| EEV alarm:Param.range error                   | 137                     | 10138 | 1          | BOOL  | AL125                                                             |
| EEV alarm:ServicePosit% err                   | 138                     | 10139 | 1          | BOOL  | AL126                                                             |
| EEV alarm:ValveID pin error                   | 139                     | 10140 | 1          | BOOL  | AL127                                                             |
| Low press alarm                               | 140                     | 10141 | 1          | BOOL  | AL128                                                             |
| High press alarm                              | 141                     | 10142 | 1          | BOOL  | AL129                                                             |
| Disc.temp.probe error                         | 142                     | 10143 | 1          | BOOL  | AL130                                                             |
| Suct.temp.probe error                         | 143                     | 10144 | 1          | BOOL  | AL131                                                             |
| Disc.press.probe error                        | 144                     | 10145 | 1          | BOOL  | AL132                                                             |
| Suct.press.probe error                        | 145                     | 10146 | 1          | BOOL  | AL133                                                             |
| Tank temp.probe error                         | 146                     | 10147 | 1          | BOOL  | AL134                                                             |
| EVI SuctT.probe error                         | 147                     | 10148 | 1          | BOOL  | AL135                                                             |
| EVI SuctP.probe error                         | 148                     | 10149 | 1          | BOOL  | AL136                                                             |
| Flow switch alarm                             | 149                     | 10150 | 1          | BOOL  | AL137                                                             |
| High temp. alarm                              | 150                     | 10151 | 1          | BOOL  | AL138                                                             |
| Low temp. alarm                               | 151                     | 10152 | 1          | BOOL  | AL139                                                             |
| Temp.delta alarm                              | 152                     | 10153 | 1          | BOOL  | AL140                                                             |
| EVI alarm:Param.range error                   | 153                     | 10154 | 1          | BOOL  | AL141                                                             |
| EVI alarm:Low superheat                       | 154                     | 10155 | 1          | BOOL  | AL142                                                             |
| EVI alarm:LOP                                 | 155                     | 10156 | 1          | BOOL  | AL143                                                             |
| EVI alarm:MOP                                 | 156                     | 10157 | 1          | BOOL  | AL144                                                             |
| EVI alarm:High condens.temp.                  | 157                     | 10158 | 1          | BOOL  | AL145                                                             |
| EVI alarm:Low suction temp.                   | 158                     | 10159 | 1          | BOOL  | AL146                                                             |
| EVI alarm:Motor error                         | 159                     | 10160 | 1          | BOOL  | AL147                                                             |
| EVI alarm:Self Tuning                         | 160                     | 10161 | 1          | BOOL  | AL148                                                             |
| EVI alarm:Emergency closing                   | 161                     | 10162 | 1          | BOOL  | AL149                                                             |
| EVI alarm:ServicePosit% err                   | 162                     | 10163 | 1          | BOOL  | AL150                                                             |
| EVI alarm:ValveID pin error                   | 163                     | 10164 | 1          | BOOL  | AL151                                                             |
| Supply power error                            | 164                     | 10165 | 1          | BOOL  | AL152                                                             |
| Fan1 fault                                    | 165                     | 10166 | 1          | BOOL  | AL153                                                             |
| Fan2 fault                                    | 166                     | 10167 | 1          | BOOL  | AL154                                                             |
| Fans Offline                                  | 167                     | 10168 | 1          | BOOL  | AL155                                                             |
| Slave1 Offline                                | 168                     | 10169 | 1          | BOOL  | AL165                                                             |
| Master Offline                                | 169                     | 10170 | 1          | BOOL  | AL166                                                             |
| Slave2 Offline                                | 170                     | 10171 | 1          | BOOL  | AL167                                                             |
| Slave3 Offline                                | 171                     | 10172 | 1          | BOOL  | AL168                                                             |
| Slave4 Offline                                | 172                     | 10173 | 1          | BOOL  | AL169                                                             |
| Slave5 Offline                                | 173                     | 10174 | 1          | BOOL  | AL170                                                             |
| Slave6 Offline                                | 174                     | 10175 | 1          | BOOL  | AL171                                                             |
| Slave7 Offline                                | 175                     | 10176 | 1          | BOOL  | AL172                                                             |
| Slave8 Offline                                | 176                     | 10177 | 1          | BOOL  | AL173                                                             |
| Slave9 Offline                                | 177                     | 10178 | 1          | BOOL  | AL174                                                             |
| Al_Offline_ElectricMeter.Active               | 188                     | 10189 | 1          | BOOL  | AL177                                                             |
| **Anti-legionella**                           | Anti-legionella funtion | 109   | 00110      | 1     | Coil                                                              | 0：disable 1：enable                                       |
| Anti-legionella temp.setp.                    | 471                     | 40472 | 2          | real  | 30-70                                                             |
| Weekday of running antileg.                   | 473                     | 40474 | 1          | UNIT  | 1~7                                                               |
| Timeband of runnig antileg.- hours (start)    | 474                     | 40475 | 1          | UNIT  | 0-23                                                              |
| Timeband of runnig antileg. - minutes (start) | 475                     | 40476 | 1          | UNIT  | 0-59                                                              |
| Timeband of runnig antileg. - hours (end)     | 476                     | 40477 | 1          | UNIT  | 0-23                                                              |
| Timeband of runnig antileg. - minutes (end)   | 477                     | 40478 | 1          | UNIT  | 0-59                                                              |
| Manual defrosting                             | 105                     | 00106 | 1          | Coil  | 0：disable 1：enable                                                |
| **SG ready**                                  | En_SG_Function          | 63    | 00064      | 1     | BOOL                                                              | 0：disable 2：enable                                       |
| En_SG_HotwaterHeater                          | 64                      | 00065 | 1          | BOOL  | 0：disable 3：enable                                                |
| Hotwater Heater_In_Pipe or water tank         | 65                      | 00066 | 1          | BOOL  | 0：water tank 1：PIPE                                               |
| SG_Mode                                       | 355                     | 40356 | 1          | int   | 0=NORMAL，1=SG-，2=SG+，3=SG++                                       |
| SG_Mode Change_HoldTime                       | 356                     | 40357 | 1          | int   | 0~600秒                                                            |
| SG_Mode_W_Tank SetP                           | 357                     | 40358 | 1          | real  | 56.0~70.0℃                                                        |
| SG_CoolSetP_Diff_1                            | 358                     | 40359 | 1          | real  | 0.0~10.0℃                                                         |
| SG_HeatSetP_Diff_1                            | 359                     | 40360 | 1          | real  | 0.0~10.0℃                                                         |
| SG_W_TankSetP_Diff_1                          | 360                     | 40361 | 1          | real  | 设0.0~10.0℃                                                        |
| SG_CoolSetP_Diff_2                            | 361                     | 40362 | 1          | real  | 0.0~10.0℃                                                         |
| SG_HeatSetP_Diff_2                            | 362                     | 40363 | 1          | real  | 0.0~10.0℃                                                         |
| SG_W_TankSetP_Diff_2                          | 363                     | 40364 | 1          | real  | 0.0~10.0℃                                                         |
| **Electric Meter**                            | Enable_ElectricMeter    | 67    | 00068      | 1     | BOOL                                                              | 0：disable 1：enable                                       |
| ElectricMeter_Reset                           | 68                      | 00069 | 1          | BOOL  |                                                                   |
| PhaseVoltage_A                                | 376                     | 40377 | 1          | real  | V                                                                 |
| PhaseVoltage_B                                | 377                     | 40378 | 1          | real  | V                                                                 |
| PhaseVoltage_C                                | 378                     | 40379 | 1          | real  | V                                                                 |
| PhaseCurrent_A                                | 379                     | 40380 | 1          | real  | A                                                                 |
| PhaseCurrent_B                                | 380                     | 40381 | 1          | real  | A                                                                 |
| PhaseCurrent_C                                | 381                     | 40382 | 1          | real  | A                                                                 |
| Power_W                                       | 382                     | 40383 | 2          | real  | W                                                                 |
| Total power consumption                       | 384                     | 40385 | 2          | real  | Kw.h                                                              |
| Record_PowerConsumption[1]                    | 401                     | 40402 | 2          | REAL  | Kw.h                                                              |
| Record_PowerConsumption[2]                    | 403                     | 40404 | 2          | REAL  | Kw.h                                                              |
| Record_PowerConsumption[3]                    | 405                     | 40406 | 2          | REAL  | Kw.h                                                              |
| Record_PowerConsumption[4]                    | 407                     | 40408 | 2          | REAL  | Kw.h                                                              |
| Record_PowerConsumption[5]                    | 409                     | 40410 | 2          | REAL  | Kw.h                                                              |
| Record_PowerConsumption[6]                    | 411                     | 40412 | 2          | REAL  | Kw.h                                                              |
| Record_PowerConsumption[7]                    | 413                     | 40414 | 2          | REAL  | Kw.h                                                              |