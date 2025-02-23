# SIMCom notifications tests
#
# Notifications are collected while:
#  * processing commands sent to SIMCom.
#  * running the update() method on regular base.
#
# The notification are available via the SIM76XX.notifs property.
#
# See Project: https://github.com/mchobby/micropython-A7682E-modem
#
from machine import UART, Pin
from sim76xx import *
import time

pwr = Pin( Pin.board.GP26, Pin.OUT, value=False )
# Pico 
uart = UART( 0, tx=Pin.board.GP0, rx=Pin.board.GP1, baudrate=115200, bits=8, parity=None, stop=1, timeout=500)
sim = SIM76XX( uart=uart, pwr_pin=pwr, uart_training=True, pincode="6778" )

# Starting SIMCom module
print( "Power up")
sim.power_up()

# Waiting for Network registration
print( "Wait Network registration")
while not sim.is_registered:
	time.sleep(1)
print( "Registered!" )

print('Waiting for incoming messages')
while True:
	sim.update()
	if sim.notifs.has_new:
		print( "%i notifications availables" % len(sim.notifs) )
		print( list(sim.notifs) ) # List of tuples (datetime, notif_type, message, cargo)
	time.sleep(1)