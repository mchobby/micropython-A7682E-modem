# Exploring the possitbilities of Status Control (part of Core functionnalities)
#
# See Project: https://github.com/mchobby/micropython-A7682E-modem
#

from machine import UART, Pin
from sim76xx import *
from sim76xx.control import *
import time

p = Pin( Pin.board.GP26, Pin.OUT, value=False )
uart = UART( 0, tx=Pin.board.GP0, rx=Pin.board.GP1, baudrate=115200, bits=8, parity=None, stop=1, timeout=500)
sim = SIM76XX( uart=uart, pwr_pin=p, uart_training=True, pincode="6778" )

# Starting SIMCom module
sim.power_up()
# Waiting for Network registration
while not sim.is_registered:
	time.sleep(1)

# Getting information about network
ctrl = Control( sim )

print( "Voltage : %f V" % ctrl.voltage )

print( "Temperature : %f °C" % ctrl.cpu_temp )

oper,act = ctrl.network_info
print( 'Network Operator :', oper )
print( 'Access Technology :', ACCESS_TECHNOLOGY[act] )

print( 'Network Mode :', NETWORK_MODE[ctrl.network_mode] )

print( 'Network RSSI : %i dBm' % ctrl.network_rssi )

print( "SIM Serial :", ctrl.sim_serial )

print( "IMEI :", ctrl.imei )

networks = ctrl.scan_networks()
for entry in networks:
	print( entry )
