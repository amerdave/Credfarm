"""
The WiFi and NTP setup file. Put on all mPy boards.
Change <SSID> and <Password>.

"""

import esp
import network
import machine
import gc
import time
esp.osdebug(None)
from ntptime import settime
gc.collect()

def do_connect():
        sta_if = network.WLAN(network.STA_IF)
        if not sta_if.isconnected():
                print('connecting to network...')
                sta_if.active(True)
                sta_if.connect('<SSID>', '<Password>')
                while not sta_if.isconnected():
                        pass

try:
	do_connect() # Connect to WIFI
	settime()    # Use NTP to set clock
	
except:
	time.sleep(60)
	machine.reset()

