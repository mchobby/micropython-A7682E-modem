# Establish a Raw Communication with the SIMCom module throught the UART
#
# See Project: https://github.com/mchobby/micropython-A7682E-modem
#

from machine import UART, Pin
import time

PIN_CODE = "6789" # Sim card PinCode

pwr = Pin( Pin.board.GP26, Pin.OUT, value=False )
# Pico 
uart = UART( 0, tx=Pin.board.GP0, rx=Pin.board.GP1, baudrate=115200, bits=8, parity=None, stop=1, timeout=500)

# Start SIM800 module by pulsing PWRKEY low for for 1 sec
print( 'POWER UP' )
pwr.value( True )
time.sleep(1)
pwr.value( False )
time.sleep(3)

# Send 3 AT command to stuluate autobaud detection
print( 'Training auto-baud detect' )
for i in range(3):
	uart.write( "AT"+chr(13)+chr(10) )
	time.sleep_ms(300) # Wait for OK
# Pump the OK response
s = uart.readline()
while s:
	s = uart.readline()


def send_command( uart, command ):
	print( '--> %s' % command )
	uart.write( command.encode('ASCII') )
	uart.write( bytes([13,10]) )

def read_result( uart ):
	""" read from uart until timeout or until OK """
	s = uart.readline()
	while s:
		print( '<-- %s' % s )
		if 'OK' in s:
			return True # OK received
		s = uart.readline()
	return False # Timeout received

def send_then_read( command, infinite=False ):
	global uart
	send_command( uart, command )
	r = read_result( uart )
	if r or infinite:
		print( 'OK received :-)' )

send_then_read("ATE0") # Echo off 
send_then_read("AT+CLCK=\"SC\",2") # Lock SIM card, Query Status
send_then_read( "AT+CGMI" )
send_then_read( "AT+CGMM" )
send_then_read( "AT+CPIN?" )
send_then_read( "AT+CPIN=%s" % PIN_CODE )
send_then_read("AT+CLCK=\"SC\",2") # Lock SIM card, Query Status
send_then_read( "AT+CNET" )

