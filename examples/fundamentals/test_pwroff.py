# Startup the SIMCom Module and initial setup
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
print( "Power off")
sim.soft_power_off()

