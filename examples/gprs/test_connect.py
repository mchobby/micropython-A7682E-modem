# Setup a GPRS connexion
#
# See Project: https://github.com/mchobby/micropython-A7682E-modem
#

from machine import UART, Pin
from sim76xx import *
from sim76xx.gprs import GPRS
import time

# Pico 
pwr = Pin( Pin.board.GP26, Pin.OUT, value=False )
uart = UART( 0, tx=Pin.board.GP0, rx=Pin.board.GP1, baudrate=115200, bits=8, parity=None, stop=1, timeout=500)
sim = SIM76XX( uart=uart, pwr_pin=pwr, uart_training=True, pincode="6778" )

print( "Power up")
sim.power_up()
print( "Wait Network registration")
while not sim.is_registered:
	print( " waiting")
	time.sleep(1)
print( "registered!" )


sim.notifs.clear()

gprs = GPRS( sim )
gprs.set_apn( "orange" ) # No password for this operator in Belgium
print( "Open GPRS connection")
print( "  led will flash quickly..." )
gprs.enable()

time.sleep( 4 )

print( "IP address:" , gprs.ip )

time.sleep( 5 )
print( "Close GPRS connection")
gprs.disable()

print( "Notification messages")
while True:
	sim.update()
	if sim.notifs.any():
		print( sim.notifs.pop() )
	else:
		break

print( "That's all Folks!")

 
