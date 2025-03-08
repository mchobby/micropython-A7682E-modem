# SIMCom Enhanced version of examples/voice/test_answer.py
#
# SIMCom wait phone call, pick-up the call (max 20 sec talk) then HANG-UP
# DTMF tone received from caller is collect and printed on REPL
#   - * clear the received DTMFs
#   - # clear the received DTMFs and send DTMF string to caller.
#	- 1234 clear the received DTMFs and send a TONE back.
#
# See Project: https://github.com/mchobby/micropython-A7682E-modem
#
from machine import UART, Pin
from sim76xx import *
from sim76xx.voice import Voice
from sim76xx.dtmf import DTMF
import time


# Pico 
pwr = Pin( Pin.board.GP26, Pin.OUT, value=False )
uart = UART( 0, tx=Pin.board.GP0, rx=Pin.board.GP1, baudrate=115200, bits=8, parity=None, stop=1, timeout=500)
sim = SIM76XX( uart=uart, pwr_pin=pwr, uart_training=True, pincode="6778" )
dtmf = DTMF( sim ) # DTMF support while 
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
talk_start = None # time when call was pick-up by destinatory

print( "Waiting calls")

# supervise URC events
while True:
	# Getting the status() will also collect the response as URC
	#   notifications under type Notification.CALLER . 
	#   That additionnal call is overkill
	# print( voice.status )

	# Terminale the call after 10 secs
	if (talk_start != None) and (time.ticks_diff(time.ticks_ms(), talk_start)>20000):
		print("Script Hang-up the call")
		talk_start = None
		voice.hang_up()


	# Collecting URC
	sim.update()
	if sim.notifs.has_new:
		print( "%i notifications availables" % len(sim.notifs) )
		# DEBUG: Show all notifications 
		print( '-'*40 )
		#print( list(sim.notifs) )

		# Pump all notifications
		_time,_type,_msg,_cargo = sim.notifs.pop()
		while _time != None: # Treat all notifications
			if _type == Notifications.CURRENT_CALL:
				# _cargo contains a CallState NamedTuple
				# 'call_id','dir','state','mode','mpty','number','ntype'
				# DEBUG: print( "_cargo :", _cargo ) 

				if (_cargo.mode == Notifications.MODE_VOICE) and (_cargo.state==Notifications.CALLSTATE_INCOMING):
					print("Incoming call from %s" % _cargo.number )
					print("Pick-up the call")
					dtmf.clear()
					voice.answer()
					talk_start = time.ticks_ms()

				if (_cargo.mode == Notifications.MODE_VOICE) and (_cargo.state==Notifications.CALLSTATE_ACTIVE):
					print("The line is active")

				if (_cargo.mode == Notifications.MODE_VOICE) and (_cargo.state==Notifications.CALLSTATE_DISCONNECTED):
					print("Call terminated")
					talk_start = None
					dtmf.clear()

			_time,_type,_msg,_cargo = sim.notifs.pop()
	
	# Show DTMF each time we received something
	if dtmf.has_new:
		# DTMF is 0..9,*,#,A,B,C,D
		print( "Current DTMF :", dtmf.received )
		# If user press * we clear the received DTMF
		# --> Useful to enter a new value
		if '*' in dtmf.received:
			print( "Clear received DTMF" )
			dtmf.clear()
		if '1234' in dtmf.received:
			print( "send Tone" )
			dtmf.clear()
			# Note; duration below 600 can't be ear at caller phone
			dtmf.send_tone( "5", 600 ) # One DTMF letter 0..9,*,#,A..D and duration (300..600) 
			dtmf.send_tone( "6", 600 ) # One DTMF letter 0..9,*,#,A..D and duration (300..600)
			dtmf.send_tone( "5", 600 ) # One DTMF letter 0..9,*,#,A..D and duration (300..600)
		if '#' in dtmf.received:
			print( "send DTMF" )
			dtmf.clear()
			dtmf.send_dtmf( "12345" ) # DTMF letter 0..9,*,#,A..D

	time.sleep(1)