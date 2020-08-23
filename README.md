
# Xiaomi Mi Robot Vacuum - Domoticz Python plugin

*This plugin uses the [Python-miio](https://github.com/rytilahti/python-miio) library.*

*[Python-miio] require Python 3.5*

*See this [link](https://www.domoticz.com/wiki/Using_Python_plugins) for more information on the Domoticz plugins.*

## How it works

Plugin provides: Status, Control, Fan Level, Battery, Care status devices, Zone Control, Target Control

**Status**: show current status in readable layout of switch. Status updates by polls 
(interval) and when you click Control device (for instant status change). since ```0.1.5``` Battery Level added to status

**Control**: for sending commands.

**Fan Level**: for adjusting suction power. (MiHome app related: Quiet=38, Balanced=60, Turbo=77, Max=90)

**Battery**: since ```0.1.5``` removed

**Care**: since ```0.1.0``` new 5 devices (care status + reset tool)

**Zone Control**

**Target Control** 

## Installation

Before installation plugin check the `python3`, `python3-dev`, `pip3` is installed for Domoticz plugin system:

```sudo apt-get install python3 python3-dev python3-pip```

Make sure you have libffi and openssl headers installed, you can do this on Debian-based systems (like Rasperry Pi) with:

```sudo apt-get install libffi-dev libssl-dev```.

Also do note that the setuptools version is too old for installing some requirements, so before trying to install this package you should update the setuptools with:

```sudo pip3 install -U setuptools```.


Then go to plugins folder and clone repository:
```
cd domoticz/plugins
git clone https://github.com/mariusz-pazur/domoticz-mirobot-plugin.git
cd domoticz-mirobot-plugin
virtualenv -p python3 .env
source .env/bin/activate
pip3 install gevent msgpack python-miio
deactivate

```

Need some prepare of **MIIO Server** to run as service:
1. Open and edit miio_server.sh by vi/nano:
```
cd ~/miio/
nano ~/miio/miio_server.sh

# 1. Check and update absolute path to miio_server.py
# 2. Update IP and TOKEN for robot
# 3. Optional. Change MIIO server host-port bindings if need it

# file miio_server.sh
DAEMON_USER=root
DAEMON=/home/pi/miio/miio_server.py
DAEMON_ARGS="192.168.1.12 476e6b70343055483230644c53707a12"
DAEMON_ARGS="$DAEMON_ARGS --host 127.0.0.1 --port 22222"
#
```

2. Check path to python3 ```which python3```. By default is ```/usr/bin/python3```. 
If your path different than default, update miio_server.py first line with your path.
```
#!/usr/bin/python3
```

3. For run as system service:
```
sudo chmod +x miio_server.py
sudo chmod +x miio_server.sh

# check your path here:
sudo ln -s /home/pi/miio/miio_server.sh /etc/init.d/miio_server

# add to startup
sudo update-rc.d miio_server defaults
sudo systemctl daemon-reload

# if you want to remove from startup
sudo update-rc.d -f miio_server remove
```

4. Run server and test script:
```
sudo service miio_server start
sudo chmod +x test.py
sudo ./test.py

# to stop miio server service
sudo service miio_server stop
```

Also you can run MIIO Server manually and look log output:
```
sudo ./miio_server.py 192.168.1.12 476e6b70343055483230644c53707a12 --host 127.0.0.1 --port 22222

# then you can run test
sudo ./test.py
```

If server and test is ok, time to restart the Domoticz:
```
sudo service domoticz.sh restart
```

Now go to **Setup** -> **Hardware** in your Domoticz interface and add type with name **Xiaomi Mi Robot Vacuum**.

| Field | Information|
| ----- | ---------- |
| Data Timeout | Keep Disabled |
| MIIOServer IP Address: | by default 127.0.0.1 |
| MIIOServer Port: | by default 22222 |
| Zones: | JSON eg ```{"10":["bedroom",[[23700,24900,30300,28700,1]]], "20":["kitchen", [[17800,27800,22400,31000,1]]]}``` Level, Zone name, 4 Zone coordinates, times to repeat  |
| Targets: | JSON eg ```{"10":["Target",[21700,27400]]}``` Level, Target name, Target coordinates  |
| Update interval | In seconds, this determines with which interval the plugin polls the status of Vacuum. Suggested is no lower then 5 sec due timeout in python-mirobo lib, but you can try any.  |
| Fan Level Type | ```Standard``` - standard set of buttons (values supported by MiHome); ```Slider``` - allow to set custom values, up to 100 (in standard Max=90) (values not supported by MiHome) |
| Debug | When set to true the plugin shows additional information in the Domoticz log |

## How to find zone cordinates

Check the [instruction](https://www.npmjs.com/package/homebridge-xiaomi-roborock-vacuum-zones)

After clicking on the Add button the new devices are available in **Setup** -> **Devices**.

If you want to change ```Fan Level Type``` just disable hardware, update type and enable again. Old device can be deleted manually in Devices menu.

## How to update plugin

```
cd domoticz/plugins/xiaomi-mirobot
git pull
```

Restart the Domoticz service
```
sudo service domoticz.sh restart
```

## Screenshots


![RR_Status](https://user-images.githubusercontent.com/25368137/54459874-f98e2200-4778-11e9-8d3f-ad9770937111.jpg)
![control_unit](https://user-images.githubusercontent.com/93999/29568435-13645e10-8759-11e7-92d8-5fe130912c78.png)
![RR_Zone](https://user-images.githubusercontent.com/25368137/54459902-1165a600-4779-11e9-88d2-675f60848e22.jpg)
![RR_Target](https://user-images.githubusercontent.com/25368137/54459912-1a567780-4779-11e9-9e1d-c41657def6ca.jpg)

![fan_level](https://user-images.githubusercontent.com/93999/29668575-6906ea22-88e9-11e7-8508-8f0ff48e2f78.png)
![fan_level2](https://user-images.githubusercontent.com/93999/29713051-86cd023c-89a5-11e7-83cc-5953b8cbbfa5.png)

![care1](https://user-images.githubusercontent.com/93999/32418537-08d3c918-c27d-11e7-89e9-10daf79bcdb4.png)
![care2](https://user-images.githubusercontent.com/93999/32418538-08ef7e10-c27d-11e7-9ff8-8dfff1c20377.png)




### How to obtain device Token

Check the [instruction](https://github.com/rytilahti/python-miio#finding-the-token)
