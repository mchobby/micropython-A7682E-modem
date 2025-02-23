# SIMCom SMS SEND test
#
# See Project: https://github.com/mchobby/micropython-A7682E-modem
#
from machine import UART, Pin
from sim76xx import *
from sim76xx.sms import SMS
import time

PHONE_NR = '0032496928320'

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

print( "Create SMS object" )
sms = SMS( sim )
print( "Send message to %s" % PHONE_NR )
sms.send( PHONE_NR, 'Test message' )
print( "Message sent!" )

# Not necessary when sending message but required
# when code needs to be notified of incoming SNS messages.
# See example test_onnotif_read.py
#
# while True:
#	sim.update()
#	if sim.notifs.has_new:
#		print( "%i notifications availables" % len(sim.notifs) )
#		print( list(sim.notifs) )
#	time.sleep(1)