# SIMCom Wait for new SMS to be notified by an URC (Unsolicitated 
# result code) then read & display it. Finally the code send 
# a confirmation message to the sender.
#
# Regular call to the update() method allows the SIM76XX class to 
# pump the URC notification. Notifications are accessibles throught
# the SIM76XX.notifs queue (see code.py:Notifications class). 
# The queue will only store the 20 lasts URC notifications and any
# pop() notication will free up its location. 
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


# Just wait for notifications
print( "Wait for notifications" )
while True:
	time.sleep( 1 )
	sim.update()
	if not sim.notifs.has_new:
		continue
	print( "%i notifications availables" % len(sim.notifs) )
	# print( list(sim.notifs) )
	
	# Manage the notifications
	_time, _type, _str, _cargo = sim.notifs.pop()
	while _time!=None:
		if _type == Notifications.SMS:
			print( f"SMS received @ id {_cargo}")

			# Read the message
			_msg = sms.read( _cargo )
			# print( f"  id:{_msg.id}" )
			# print( f"  status:{_msg.status}" )
			print( f"  phone:{_msg.phone}" )
			print( "  DateTime: {2}/{1}/{0} {3}:{4}:{5}".format(*time.localtime( _msg.dt ) ) )
			print( "  Message :", _msg.message )

			# Delete the message
			sms.delete(_cargo) 

			# Send a reply
			print( f"Send reply to {_msg.phone}")
			try:
				id = sms.send( _msg.phone, "%s received!" % _msg.message )
				# Not required if the phone doesn't keeps a local copy
				# sms.delete(id)
				print( "Done!" )
			except SMSError as err:
				print( 'SMS Send error!', str(err) )
		else:
			print( "other notification", (_time, _type, _str, _cargo) )

		# Next nofitication
		_time, _type, _str, _cargo = sim.notifs.pop()
