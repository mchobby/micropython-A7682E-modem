# SIMCom read all SMS test
#
# Read a stored SMS from its ID. ID may be obtain from notification or
# from the list of SMS.
#
# See Project: https://github.com/mchobby/micropython-A7682E-modem
#
from machine import UART, Pin
from sim76xx import *
from sim76xx.sms import SMS
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

sms = SMS( sim )

print( "Reading all stored messages!" )
sms_list = sms.list( SMS.ALL, max_row=None )
for item in sms_list:
	# Read a message based on its index
	_msg = sms.read( item.id )
	_status_text = sms.STATUS_TEXT[_msg.status]
	print( f"id: {_msg.id}" )
	print( f"status: {_msg.status} ({_status_text})" )
	print( f"phone: {_msg.phone}" )
	print( "DateTime: {2}/{1}/{0} {3}:{4}:{5}".format(*time.localtime( _msg.dt ) ) )
	print( _msg.message )
	print( "-"*40 )

print( "That s all Folks!" )