#
#       Xiaomi Mi Robot Vacuum Plugin
#       Author: mrin, 2017, avgays, 2019
#
"""
<plugin key="xiaomi-mi-robot-vacuum" name="Xiaomi Mi Robot Vacuum" author="mrin/avgays" version="0.1.5" wikilink="https://github.com/avgays/domoticz-mirobot-plugin" externallink="">
    <params>
        <param field="Address" label="MIIOServer IP Address" width="200px" required="true" default="127.0.0.1"/>
        <param field="Port" label="MIIOServer Port" width="60px" required="true" default="22222"/>
        <param field="Mode3" label="Zones" width="600px" required="false" default="{}"/>
        <param field="Mode6" label="Targets" width="600px" required="true" default="{}"/>
        <param field="Mode1" label="Rooms" width="600px" required="true" default="{}"/>

        <param field="Mode2" label="Update interval (sec)" width="30px" required="true" default="15"/>
        <param field="Mode5" label="Fan Level Type" width="300px">
            <options>
                <option label="Standard (Quiet, Balanced, Turbo, Max)" value="selector" default="true"/>
                <option label="Slider" value="dimmer"/>
            </options>
        </param>
        <param field="Mode4" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug" default="true"/>
                <option label="False" value="Normal"/>
            </options>
        </param>
    </params>
</plugin>
"""


import os
import sys

#module_paths = [x[0] for x in os.walk( os.path.join(os.path.dirname(__file__), '.', '.env/lib/') ) if x[0].endswith('site-packages') ]
#for mp in module_paths:
#    sys.path.append(mp)
sys.path.append('/usr/local/lib/python3.5')
import Domoticz
import msgpack
import json
import base64
from datetime import datetime
from datetime import timedelta

# init gettext for i18n
import gettext
#curLang='fr'
curLang= os.environ['LANG']
lang = gettext.translation ('base', localedir='locales', languages= [curLang], fallback=True)
lang.install()
_ = lang.gettext

class BasePlugin:
    controlOptions = {
        "LevelActions": "||||||",
        "LevelNames": "Off|Clean|Home|Spot|Pause|Stop|Find",
        "LevelOffHidden": "true",
        "SelectorStyle": "0"
    }
    fanOptions = {
        "LevelActions": "|||||",
        "LevelNames": "Off|Quiet|Balanced|Turbo|Max|Wet",
        "LevelOffHidden": "true",
        "SelectorStyle": "0"
    }
    careOptions = {
        "LevelActions": "||||",
        "LevelNames": "Off|Main Brush|Side Brush|Filter|Sensor",
        "LevelOffHidden": "true",
        "SelectorStyle": "0"
    }
    zoneOptions = {
        "LevelActions": "",
        "LevelNames": "Off",
        "LevelOffHidden": "true",
        "SelectorStyle": "0"
    }
    targetOptions = {
        "LevelActions": "",
        "LevelNames": "Off",
        "LevelOffHidden": "true",
        "SelectorStyle": "0"
    }
    roomOptions = {
        "LevelActions": "",
        "LevelNames": "Off",
        "LevelOffHidden": "true",
        "SelectorStyle": "0"
    }
    myzones={}
    mytargets={}
    myrooms={}
    battery=0
    customSensorOptions = {"Custom": "1;%"}

    iconName = 'xiaomi-mi-robot-vacuum-icon'
    mainIconName = 'xiaomi-mi-robot-vacuum-main'
    targetIconName = 'xiaomi-mi-robot-vacuum-target'
    zoneIconName = 'xiaomi-mi-robot-vacuum-zone'
    sensorsIconName = 'xiaomi-mi-robot-vacuum-sensors'
    mbrushIconName = 'xiaomi-mi-robot-vacuum-mbrush'
    brushIconName = 'xiaomi-mi-robot-vacuum-brush'
    filterIconName = 'xiaomi-mi-robot-vacuum-filter'
    chargeIconName = 'xiaomi-mi-robot-vacuum-charge'
    roomIconName = 'xiaomi-mi-robot-vacuum-zone'

    statusUnit = 1
    controlUnit = 2
    fanDimmerUnit = 3
    fanSelectorUnit = 4
#    batteryUnit = 5
    cMainBrushUnit = 6
    cSideBrushUnit = 7
    cSensorsUnit = 8
    cFilterUnit = 9
    cResetControlUnit = 10
    zoneControlUnit = 11
    targetControlUnit = 12
    roomControlUnit = 13

    # statuses by protocol
    # https://github.com/marcelrv/XiaomiRobotVacuumProtocol/blob/master/StatusMessage.md
    states = {
        0:  _('Unknown 0'),
        1:  _('Initiating'),
        2:  _('Sleeping'),
        3:  _('Waiting'),
        4:  _('Unknown 4'),
        5:  _('Cleaning'),
        6:  _('Back to home'),
        7:  _('Manual mode'),
        8:  _('Charging'),
        9:  _('Charging Error'),
        10: _('Paused'),
        11: _('Spot cleaning'),
        12: _('In Error'),
        13: _('Shutting down'),
        14: _('Updating'),
        15: _('Docking'),
        16: _('Go To'),
        17: _('Zone cleaning'),
        18: _('Room cleaning'),
        100:_('Full'),
        200:_('Docking')
    }


    def __init__(self):
        self.heartBeatCnt = 0
        self.subHost = None
        self.subPort = None
        self.tcpConn = None
        self.unpacker = msgpack.Unpacker()

    def onStart(self):
        if Parameters['Mode4'] == 'Debug':
            Domoticz.Debugging(1)
            DumpConfigToLog()
        try:
            self.myzones = json.loads(Parameters['Mode3'])
        except Exception:
            self.myzones={}
        Domoticz.Debug("Got zones: %s" % self.myzones)

        try:
            self.mytargets = json.loads(Parameters['Mode6'])
        except Exception:
            self.mytargets={}
        Domoticz.Debug("Got targets: %s" % self.mytargets)

        try:
            self.myrooms = json.loads(Parameters['Mode1'])
        except Exception:
            self.myrooms={}
        Domoticz.Debug("Got rooms: %s" % self.myrooms)

        self.heartBeatCnt = 0
        self.subHost = Parameters['Address']
        self.subPort = Parameters['Port']

        self.tcpConn = Domoticz.Connection(Name='MIIOServer', Transport='TCP/IP', Protocol='None',
                                           Address=self.subHost, Port=self.subPort)


        if self.iconName not in Images: Domoticz.Image('icons.zip').Create()
        iconID = Images[self.iconName].ID

        if self.mainIconName not in Images: Domoticz.Image('xiaomi-mi-robot-vacuum-main.zip').Create()
        mainIconID = Images[self.mainIconName].ID

        if self.targetIconName not in Images: Domoticz.Image('xiaomi-mi-robot-vacuum-target.zip').Create()
        targetIconID = Images[self.targetIconName].ID

        if self.zoneIconName not in Images: Domoticz.Image('xiaomi-mi-robot-vacuum-zone.zip').Create()
        zoneIconID = Images[self.zoneIconName].ID

        if self.sensorsIconName not in Images: Domoticz.Image('xiaomi-mi-robot-vacuum-sensors.zip').Create()
        sensorsIconID = Images[self.sensorsIconName].ID

        if self.mbrushIconName not in Images: Domoticz.Image('xiaomi-mi-robot-vacuum-mbrush.zip').Create()
        mbrushIconID = Images[self.mbrushIconName].ID

        if self.brushIconName not in Images: Domoticz.Image('xiaomi-mi-robot-vacuum-brush.zip').Create()
        brushIconID = Images[self.brushIconName].ID

        if self.filterIconName not in Images: Domoticz.Image('xiaomi-mi-robot-vacuum-filter.zip').Create()
        filterIconID = Images[self.filterIconName].ID

        if self.chargeIconName not in Images: Domoticz.Image('xiaomi-mi-robot-vacuum-charge.zip').Create()
        chargeIconID = Images[self.chargeIconName].ID


        if self.statusUnit not in Devices:
            Domoticz.Device(Name='Status', Unit=self.statusUnit, Type=17,  Switchtype=17, Image=mainIconID).Create()

        if self.controlUnit not in Devices:
            Domoticz.Device(Name='Control', Unit=self.controlUnit, TypeName='Selector Switch',
                            Image=mainIconID, Options=self.controlOptions).Create()

        if self.fanDimmerUnit not in Devices and Parameters['Mode5'] == 'dimmer':
            Domoticz.Device(Name='Fan Level', Unit=self.fanDimmerUnit, Type=244, Subtype=73, Switchtype=7,
                            Image=mainIconID).Create()
        elif self.fanSelectorUnit not in Devices and Parameters['Mode5'] == 'selector':
            Domoticz.Device(Name='Fan Level', Unit=self.fanSelectorUnit, TypeName='Selector Switch',
                                Image=mainIconID, Options=self.fanOptions).Create()

#        if self.batteryUnit not in Devices:
#            Domoticz.Device(Name='Battery', Unit=self.batteryUnit, TypeName='Custom', Image=chargeIconID,
#                            Options=self.customSensorOptions).Create()

        if self.cMainBrushUnit not in Devices:
            Domoticz.Device(Name='Care Main Brush', Unit=self.cMainBrushUnit, TypeName='Custom', Image=mbrushIconID,
                            Options=self.customSensorOptions).Create()

        if self.cSideBrushUnit not in Devices:
            Domoticz.Device(Name='Care Side Brush', Unit=self.cSideBrushUnit, TypeName='Custom', Image=brushIconID,
                            Options=self.customSensorOptions).Create()

        if self.cSensorsUnit not in Devices:
            Domoticz.Device(Name='Care Sensors ', Unit=self.cSensorsUnit, TypeName='Custom', Image=sensorsIconID,
                            Options=self.customSensorOptions).Create()

        if self.cFilterUnit not in Devices:
            Domoticz.Device(Name='Care Filter', Unit=self.cFilterUnit, TypeName='Custom', Image=filterIconID,
                            Options=self.customSensorOptions).Create()

        if self.cResetControlUnit not in Devices:
            Domoticz.Device(Name='Care Reset Control', Unit=self.cResetControlUnit, TypeName='Selector Switch', Image=mainIconID,
                            Options=self.careOptions).Create()
        if self.zoneControlUnit not in Devices:
            i=1
            while i <= len(self.myzones):
                Options=str(i*10)
                self.zoneOptions["LevelActions"] += "|"
                self.zoneOptions["LevelNames"] += "|" + str(self.myzones[Options][0])
                i += 1
            Domoticz.Log("Zone names: %s" % self.zoneOptions["LevelNames"] )
            Domoticz.Device(Name='Zone Control', Unit=self.zoneControlUnit, TypeName='Selector Switch', Image=zoneIconID,
                            Options=self.zoneOptions).Create()

        if self.targetControlUnit not in Devices:
            i=1
            while i <= len(self.mytargets):
                Options=str(i*10)
                self.targetOptions["LevelActions"] += "|"
                self.targetOptions["LevelNames"] += "|" + str(self.mytargets[Options][0])
                i += 1
            Domoticz.Log("Target names: %s" % self.targetOptions["LevelNames"] )
            Domoticz.Device(Name='Target Control', Unit=self.targetControlUnit, TypeName='Selector Switch', Image=targetIconID,
                            Options=self.targetOptions).Create()

        if self.roomControlUnit not in Devices:
            i=1
            while i <= len(self.myrooms):
                Options=str(i*10)
                self.roomOptions["LevelActions"] += "|"
                self.roomOptions["LevelNames"] += "|" + str(self.myrooms[Options][0])
                i += 1
            Domoticz.Log("Room names: %s" % self.roomOptions["LevelNames"] )
            Domoticz.Device(Name='Room Control', Unit=self.roomControlUnit, TypeName='Selector Switch', Image=zoneIconID,
                            Options=self.roomOptions).Create()

        Domoticz.Heartbeat(int(Parameters['Mode2']))


    def onStop(self):
        pass

    def onConnect(self, Connection, Status, Description):
        Domoticz.Status("MIIOServer connection status is [%s] [%s]" % (Status, Description))

    def onMessage(self, Connection, Data):
        try:
            self.unpacker.feed(Data)
            for result in self.unpacker:

                Domoticz.Debug("Got: %s" % result)

                if 'exception' in result: return

                if result['cmd'] == 'status':
                    now = datetime.now()
                    self.battery=int(result['battery'])
                    if (result['state_code'] == 8) and (self.battery == 100) : result['state_code']=200
                    UpdateDevice(self.statusUnit,
                                 (1 if result['state_code'] in [5, 6, 11, 14, 16, 17, 18] else 0), # ON is Cleaning, Back to home, Spot cleaning, Go To, Zone cleaning, Room cleaning
                                 self.states.get(result['state_code'], 'Undefined') + _('. Charge ') + str(self.battery) + '%',
                                 self.battery)

                    if (result['state_code'] != 17) and (Devices[self.zoneControlUnit].nValue != 0):
                        if (datetime.now() - datetime.strptime(Devices[self.zoneControlUnit].LastUpdate, "%Y-%m-%d %H:%M:%S")).seconds > 29:
                            #Domoticz.Status('Убока зоны %s завершена, площадь %s кв.м., время %s минут  ' % (self.myzones[str(Devices[self.zoneControlUnit].sValue)][0], result['clean_area'], (result['clean_seconds']/60) ))
                            #Domoticz.Status(_('%s area cleaning completed, area %s sq.m., time %s minutes') % (self.myzones[str(Devices[self.zoneControlUnit].sValue)][0], result['clean_area'], (result['clean_seconds']/60) ))
                            UpdateDevice(self.zoneControlUnit, 0, 'Off')


                    if result['state_code'] != 16 and (Devices[self.targetControlUnit].nValue != 0):
                        UpdateDevice(self.targetControlUnit, 0, 'Off')
#                        Domoticz.Log('Target LastUpdate: %s' % Devices[self.targetControlUnit].LastUpdate)

#                    UpdateDevice(self.batteryUnit, result['battery'], str(result['battery']), result['battery'],
#                                 AlwaysUpdate=(self.heartBeatCnt % 100 == 0))
                    if result['state_code'] != 18 and (Devices[self.roomControlUnit].nValue != 0):
                        UpdateDevice(self.roomControlUnit, 0, 'Off')

                    if Parameters['Mode5'] == 'dimmer':
                        UpdateDevice(self.fanDimmerUnit, 2, str(result['fan_level'])) # nValue=2 for show percentage, instead ON/OFF state
                    else:
                        level = {38: 10, 60: 20, 77: 30, 100: 40, 105: 50}.get(result['fan_level'], None)
                        if level: UpdateDevice(self.fanSelectorUnit, 1, str(level))

                elif result['cmd'] == 'consumable_status':

                    mainBrush = cPercent(result['main_brush'], 300)
                    sideBrush = cPercent(result['side_brush'], 200)
                    filter = cPercent(result['filter'], 150)
                    sensors = cPercent(result['sensor'], 30)

                    UpdateDevice(self.cMainBrushUnit, mainBrush, str(mainBrush), AlwaysUpdate=True)
                    UpdateDevice(self.cSideBrushUnit, sideBrush, str(sideBrush), AlwaysUpdate=True)
                    UpdateDevice(self.cFilterUnit, filter, str(filter), AlwaysUpdate=True)
                    UpdateDevice(self.cSensorsUnit, sensors, str(sensors), AlwaysUpdate=True)

        except msgpack.UnpackException as e:
            Domoticz.Error('Unpacker exception [%s]' % str(e))

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Command '" + str(Command) + "', Level: " + str(Level))

        if self.statusUnit not in Devices:
            Domoticz.Error('Status device is required')
            return

        sDevice = Devices[self.statusUnit]

        if self.statusUnit == Unit:
            if 'On' == Command and self.isOFF:
                if self.apiRequest('start'): UpdateDevice(Unit, 1, self.states[5]) # Cleaning

            elif 'Off' == Command and self.isON:
                if sDevice.sValue == self.states[11] and self.apiRequest('pause'): # Stop if Spot cleaning
                    UpdateDevice(Unit, 0, self.states[3]) # Waiting
                elif self.apiRequest('home'):
                    UpdateDevice(Unit, 1, self.states[6]) # Back to home

        elif self.controlUnit == Unit:

            if Level == 10: # Clean
                if self.apiRequest('start') and self.isOFF:
                    UpdateDevice(self.statusUnit, 1, self.states[5])  # Cleaning

            elif Level == 20: # Home
                if self.apiRequest('home') and sDevice.sValue in [
                    self.states[5], self.states[3], self.states[10]]: # Cleaning, Waiting, Paused
                    UpdateDevice(self.statusUnit, 1, self.states[6])  # Back to home

            elif Level == 30: # Spot
                if self.apiRequest('spot') and self.isOFF and sDevice.sValue != self.states[8]: # Spot cleaning will not start if Charging
                    UpdateDevice(self.statusUnit, 1, self.states[11])  # Spot cleaning

            elif Level == 40: # Pause
                if self.apiRequest('pause') and self.isON:
                    if sDevice.sValue == self.states[11]: # For Spot cleaning - Pause treats as Stop
                        UpdateDevice(self.statusUnit, 0, self.states[3])  # Waiting
                    else:
                        UpdateDevice(self.statusUnit, 0, self.states[10])  # Paused

            elif Level == 50: # Stop
                if self.apiRequest('stop') and self.isON and sDevice.sValue not in [self.states[11], self.states[6]]: # Stop doesn't work for Spot cleaning, Back to home
                    UpdateDevice(self.statusUnit, 0, self.states[3]) # Waiting

            elif Level == 60: # Find
                self.apiRequest('find')

        elif self.fanDimmerUnit == Unit and Parameters['Mode5'] == 'dimmer':
            Level = 1 if Level == 0 else 100 if Level > 105 else Level
            if self.apiRequest('set_fan_level', Level): UpdateDevice(self.fanDimmerUnit, 2, str(Level))

        elif self.fanSelectorUnit == Unit and Parameters['Mode5'] == 'selector':
            num_level = {10: 38, 20: 60, 30: 77, 40: 90, 50:105}.get(Level, None)
            if num_level and self.apiRequest('set_fan_level', num_level): UpdateDevice(self.fanSelectorUnit, 1, str(Level))

        elif self.cResetControlUnit == Unit:

            if Level == 10: # Reset Main Brush
                if self.apiRequest('care_reset_main_brush'):
                    UpdateDevice(self.cMainBrushUnit, 100, '100')

            elif Level == 20: # Reset Side Brush
                if self.apiRequest('care_reset_side_brush'):
                    UpdateDevice(self.cSideBrushUnit, 100, '100')

            elif Level == 30: # Reset Filter
                if self.apiRequest('care_reset_filter'):
                    UpdateDevice(self.cFilterUnit, 100, '100')

            elif Level == 40: # Reset Sensors
                if self.apiRequest('care_reset_sensor'):
                    UpdateDevice(self.cSensorsUnit, 100, '100')

            self.apiRequest('consumable_status')

        elif self.zoneControlUnit == Unit and self.isOFF:
            if self.apiRequest('zoned_clean', self.myzones[str(Level)][1]):
                UpdateDevice(self.zoneControlUnit, 1, str(Level))
                #Domoticz.Status("Уборка зоны %s" % (self.myzones[str(Level)][0]))
                Domoticz.Status(_("Zone cleaning %s") % (self.myzones[str(Level)][0]))

        elif self.targetControlUnit == Unit and self.isOFF:
            if self.apiRequest('goto', self.mytargets[str(Level)][1]):
                UpdateDevice(self.targetControlUnit, 1, str(Level))
                #Domoticz.Status("Перемещение в точку %s" % (self.mytargets[str(Level)][0]))
                Domoticz.Status(_("Move to point %s") % (self.mytargets[str(Level)][0]))

        elif self.roomControlUnit == Unit and self.isOFF:
            if self.apiRequest('room_clean', self.myrooms[str(Level)][1]):
                UpdateDevice(self.roomControlUnit, 1, str(Level))
                Domoticz.Status(_("Room cleaning %s") % (self.myrooms[str(Level)][0]))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Debug("MIIOServer disconnected")

    def onHeartbeat(self):
        if not self.tcpConn.Connecting() and not self.tcpConn.Connected():
            self.tcpConn.Connect()
            Domoticz.Debug("Trying connect to MIIOServer %s:%s" % (self.subHost, self.subPort))

        elif self.tcpConn.Connecting():
            Domoticz.Debug("Still connecting to MIIOServer %s:%s" % (self.subHost, self.subPort))

        elif self.tcpConn.Connected():
            if self.heartBeatCnt % 30 == 0 or self.heartBeatCnt == 0:
                self.apiRequest('consumable_status')
            self.apiRequest('status')
            self.heartBeatCnt += 1


    @property
    def isON(self):
        return Devices[self.statusUnit].nValue == 1

    @property
    def isOFF(self):
        return Devices[self.statusUnit].nValue == 0

    def apiRequest(self, cmd_name, cmd_value=None):
        if not self.tcpConn.Connected(): return False
        cmd = [cmd_name]
        if cmd_value: cmd.append(cmd_value)
        try:
            self.tcpConn.Send(msgpack.packb(cmd, use_bin_type=True))
            return True
        except msgpack.PackException as e:
            Domoticz.Error('Pack exception [%s]' % str(e))
            return False



def UpdateDevice(Unit, nValue, sValue, BatteryLevel=255, AlwaysUpdate=False):
    if Unit not in Devices: return
    if Devices[Unit].nValue != nValue\
        or Devices[Unit].sValue != sValue\
        or Devices[Unit].BatteryLevel != BatteryLevel\
        or AlwaysUpdate == True:

        Devices[Unit].Update(nValue, str(sValue), BatteryLevel=BatteryLevel)

        Domoticz.Debug("Update %s: nValue %s - sValue %s - BatteryLevel %s" % (
            Devices[Unit].Name,
            nValue,
            sValue,
            BatteryLevel
        ))


def UpdateIcon(Unit, iconID):
    if Unit not in Devices: return
    d = Devices[Unit]
    if d.Image != iconID: d.Update(d.nValue, d.sValue, Image=iconID)

def cPercent(used, max):
    return 100 - round(used / 3600 * 100 / max)


global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data, Status=None, Extra=None):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
