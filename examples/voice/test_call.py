# SIMCom Make a voice call (max 10 sec talk) and HANG-UP
#
# See Project: https://github.com/mchobby/micropython-A7682E-modem
#
from machine import UART, Pin
from sim76xx import *
from sim76xx.voice import Voice
import time

PHONE_NR = '+3223872478'

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
	time.sleep(1)
print( "Registered!" )

print( "Create Voice call object" )
voice = Voice( sim )
print( "Calling..." )
talk_start = None # time when call was pick-up by destinatory
voice.call( PHONE_NR )

# supervise URC events
while True:
	# Getting the status() will also collect the response as URC
	#   notifications under type Notification.CALLER . 
	#   That additionnal call is overkill
	# print( voice.status )

	# Terminale the call after 10 secs
	if (talk_start != None) and (time.ticks_diff(time.ticks_ms(), talk_start)>10000):
		print("Script Hang-up the call")
		talk_start = None
		voice.hang_up()

	# Collecting URC
	sim.update()
	if sim.notifs.has_new:
		print( "%i notifications availables" % len(sim.notifs) )
		# DEBUG: Show all notifications 
		print( '-'*40 )
		print( list(sim.notifs) )

		# Pump all notifications
		_time,_type,_msg,_cargo = sim.notifs.pop()
		while _time != None: # Treat all notifications
			if _type == Notifications.CURRENT_CALL:
				# _cargo contains a CallState NamedTuple
				# 'call_id','dir','state','mode','mpty','number','ntype'
				# DEBUG: print( "_cargo :", _cargo ) 

				if (_cargo.mode == Notifications.MODE_VOICE) and (_cargo.state==Notifications.CALLSTATE_DIALING):
					print("Dialing to %s" % _cargo.number )
				if (_cargo.mode == Notifications.MODE_VOICE) and (_cargo.state==Notifications.CALLSTATE_ACTIVE):
					talk_start = time.ticks_ms()
					print("Someone on the line :)")
				if (_cargo.mode == Notifications.MODE_VOICE) and (_cargo.state==Notifications.CALLSTATE_DISCONNECTED):
					print("Call terminated")
					talk_start = None

			_time,_type,_msg,_cargo = sim.notifs.pop()
			

	time.sleep(1)