# SIMCom SMS list test
#
# List the SMS that are stored into one of the following status:
# - RECEIVED_UNREAD, RECEIVED_READ, UNSENT, SENT, ALL
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

# Read "received unread" messages
#  Returns a list of SMSHeader objects having fields 'id','status', 'phone', 'dt', 'tzd'
#     dt contains the datetime and tzd, the TimeZone info
#  Default max_row is 20. Use None for ALL records.
print( sms.list(SMS.RECEIVED_UNREAD, max_row=None) )

# Read "received read" messages
print( sms.list(SMS.RECEIVED_READ, max_row=None) )

# Get SMS List for every status
#  Possible status are RECEIVED_UNREAD, RECEIVED_READ, UNSENT, SENT, ALL

#for status in SMS.STATUS_TEXT.keys():
#	print( "-" * 40 )
#	print( "list SMS for status %i : %s " % (status,SMS.STATUS_TEXT[status]))
#	_r = sms.list( status )
#	print( _r )