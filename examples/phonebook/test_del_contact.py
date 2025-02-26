# Open the Phonebook and delete a contact by index
#
# See Project: https://github.com/mchobby/micropython-A7682E-modem
#
from machine import UART, Pin
from sim76xx import *
from sim76xx.phonebook import Phonebook
import time

# Pico 
pwr = Pin( Pin.board.GP26, Pin.OUT, value=False )
uart = UART( 0, tx=Pin.board.GP0, rx=Pin.board.GP1, baudrate=115200, bits=8, parity=None, stop=1, timeout=500)
sim = SIM76XX( uart=uart, pwr_pin=pwr, uart_training=True, pincode="6778" )

# Starting SIMCom module
print( "Power up")
sim.power_up()

# Waiting for Network registration
print( "Wait Network registration")
while not sim.is_registered:
	print( " waiting")
	time.sleep(1)
print( "registered!" )

book = Phonebook( sim )
book.open( storage=Phonebook.SIM ) # SIM is open by default

print( "delete contact 2")
book.delete( 2 )

# print( "delete contact 5")
# book.delete( 5 )
#
# Unexisting will raise CommandError exception
#   CommandError: AT+CPBW=5 : +CME ERROR: unknown error

print( "Done!" )