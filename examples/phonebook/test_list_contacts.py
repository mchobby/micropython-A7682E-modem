# Open the Phonebook and list the contacts it contains
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

print( "Lists the contacts...")
indexes = book.list()
print( "contact ids:",indexes )

for index in indexes:
	print( book.read(index) )

# Will return output like:
#   BookEntry(index=1, name='Dominiq', number='476543211', ntype=129)
#   BookEntry(index=2, name='Didi', number='+32333112233', ntype=145)
#   BookEntry(index=4, name='Marion', number='+33123110011', ntype=145)
#   ...
