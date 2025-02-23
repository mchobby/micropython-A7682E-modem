# SIMCom SMS delete test
#
# Delete a stored SMS by its ID. ID may be obtain from notification or
# from the list of SMS.
#
# See Project: https://github.com/mchobby/micropython-A7682E-modem
#
from machine import UART, Pin
from sim76xx import *
from sim76xx.sms import SMS
import time

MSG_INDEX = 23

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

sms = SMS( sim )
sms_list = sms.list( SMS.ALL, max_row=None )
for item in sms_list:
	print( f"deleting {item.id}" )
	sms.delete( item.id )

print("That s all folks!")
