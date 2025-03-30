# Test the HTTP GET
#
# See Project: https://github.com/mchobby/micropython-A7682E-modem
#
# Remark: 
#   When "AT+HTTPINIT : ERROR" occurs, only a Power Cycle can solve it.
#   Please, report a better solution if you find it.
#
from machine import UART, Pin
from sim76xx import *
from sim76xx.http import HTTP
import time

URL = 'http://shop.mchobby.be'

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

http = HTTP( sim )
http.set_apn( "orange" ) # No password for this operator in Belgium
print( "Enable HTTP")
print( "  led will flash quickly..." )
http.enable()

print( "Getting URL %s (HTTP ONLY)" % (URL,))
response = http.get( URL )
print( "Status :", http.status_code )
print( "response length :", http.response_len )
print( "---- Notification messages ----")
while True:
	sim.update()
	if sim.notifs.any():
		print( sim.notifs.pop() )
	else:
		break
print( "---- Response ----")
# Reponse content is read by chunck to spare memory
# Each chunck is returned as bytes()
_data = response.read()
while _data:
	print( _data.decode('ASCII') )
	_data = response.read()

print( "-"*40 )

http.disable()
print( "That's all Folks!")