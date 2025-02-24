import machine
import collections
import time


class SIMComError( Exception ):
	pass

class CommandError( SIMComError ):
	def __init__( self, command, message="ERROR" ):
		super().__init__( "%s : %s" % (command,message))
		self.command = command

class Timeout( SIMComError ): 
	def __init__( self, command, time_ms ):
		super().__init__( command, "%i ms timeout reached!" % time_ms ) 

def debug( s ):
	pass #print( s )

class Response( list ):
	def contains( self, value ):
		return any( [value in s for s in self ] )

	@property
	def text( self ):
		return ' '.join(self)

# CurrentCallState issued by the +GLCC: URC notification
#  - call_id : internal id for call
#  - dir   : direction. See constants Notifications.DIR_OUTGOING / _INCOMING
#  - state : current state of call. See constants Notifications.CALLSTATE_ACTIVE / _HELD / ...
#  - mode  : current call mode. See constant Notifications.MODE_VOICE/_DATA/_FAX/_UNKNOWN
#  - mpty  : multiparty call True/False
#  - number: phone number (a string)
#  - ntype : format/type of phone number. See constant Notifications.NTYPE_xxx
CallState = collections.namedtuple('CallState', ['call_id','dir','state','mode','mpty','number','ntype'])

# Item stored in the notification queue
#  - _type : type of notification. See Notifications.UNDEFINED/CURRENT_CALL/VOICE/SMS .
#  - soure : source of the notification (= Response string)
#  - cargo : reference to complementary information or None (EG: will contains a CallState for _type=Notifications.CURRENT_CALL)
Notif = collections.namedtuple('Notif', ['_time','_type','source','cargo'] )

class Notifications( collections.deque ):
	""" Store the Unsolicitated Result Code (URC) """
	# --- Type of notifications object -------------
	UNDEFINED = const(0)
	CURRENT_CALL = const(1) # Notification +CLCC: with caller phone number
	VOICE = const(2)  # RING, NO CARRIER, ... old style of voice call notificiation
	SMS = const(3)    # +CMTI: "SM",3 ... SMS mem,id notification 

	NOTIF_TEXT = {UNDEFINED: "Undefined", CURRENT_CALL: "CURRENT_CALL", VOICE: "VOICE", SMS: "SMS"}

	# --- CallState constants ----------------------
	DIR_OUTGOING = const(0)
	DIR_INCOMING = const(0)

	CALLSTATE_ACTIVE   = const(0)
	CALLSTATE_HELD     = const(1)
	CALLSTATE_DIALING  = const(2) # Outgoing call 
	CALLSTATE_ALERTING = const(3) # Outgoing call
	CALLSTATE_INCOMING = const(4)
	CALLSTATE_WAITING  = const(5)
	CALLSTATE_DISCONNECTED = const(6)

	MODE_VOICE  = const(0)
	MODE_DATA   = const(1)
	MODE_FAX    = const(2)
	MODE_UNKNOW = const(9)

	NTYPE_RESTRICTED    = const(128) # Restricted number (includes unknown type and format)
	NTYPE_INTERNATIONAL = const(145)
	NTYPE_NATIONAL      = const(161)
	NTYPE_SPECIFIC      = const(177) # Network specific number (eg:ISDN format)
	NTYPE_OTHER         = const(129)


	def __init__( self ):
		super().__init__( [], 20 ) # Empty list with max 20 items
		self._has_new = False
		self.is_ring = False

	def clear(self):
		for i in range( len(self) ):
			self.pop()

	def is_urc( self, s ):
		# Check if s contains an URC (Unsolicited Result Code) message
		if s.startswith( "VOICE CALL:" ) or (s=="RING") or (s=="CONNECT") or (s=="NO CARRIER"):
			return True
		if any( [ s.startswith(_this) for _this in ("+CLCC:","+CMTI:","+CRING:","+CIPEVENT:","+IPCLOSE:","+CLIENT:") ] ):
			return True
		if any( [ s.startswith(_this) for _this in ("+HTTP_PEER_CLOSED","+HTTP_NONET_EVENT", "+CFTPSNOTIFY:", "+CMQTTCONNLOST:","+CMQTTRXSTART:","+CMQTTRXTOPIC:") ] ):
			return True
		if any( [ s.startswith(_this) for _this in ("+CMQTTRXPAYLOAD:","+CMQTTRXEND:","+CCHEVENT:","+CCH_RECV_CLOSED:","+CCH_PEER_CLOSED:","+CFOTA:", "+CTVZ:" ) ] ):
			return True
		if any( [ s.startswith(_this) for _this in ("+CGREG:","+CGEV:","+CCWA:" ) ] ):
			return True
		return False

	def append( self, s ):
		# Add tuple  (time, notif_type, string)
		# print( 'Notif.append', s )
		_type = self.UNDEFINED # Type of notification
		_cargo = None
		if s=="RING":
			self.is_ring = True
			_type = VOICE
		elif (s=="CONNECT") or (s=="NO CARRIER") or s.startswith( "VOICE CALL: END" ):
			self.is_ring = False
			_type = VOICE
		elif s.startswith("+CMTI:"): # +CMTI: "SM",18
			_type = self.SMS
			_cargo = int( s.split(",")[1] ) # SMS ID
		elif s.startswith("+CLCC:"): # +CLCC: 1,1,4,0,0,"+33359260058",145
			_type = self.CURRENT_CALL
			_cargo = self._decode_GLCC( s )


		super().append( Notif(time.time(), _type, s, _cargo) )
		self._has_new = True

	def _decode_GLCC( self, s ):
		# # +CLCC: 1,1,4,0,0,"+33359260058",145
		vals = s.split(": ")[1].split(",")
		# call_id, dir, state, mode, mpty, number,ntype
		return CallState( int(vals[0]), int(vals[1]), int(vals[2]), int(vals[3]), vals[4]=='1', \
			     None if len(vals)<6 else vals[5].replace('\"',''), None if len(vals)<7 else int(vals[6]) ) 


	@property
	def has_new( self ):
		# Check if new notifications have been inserted then reset the flag!
		_r = self._has_new
		self._has_new = False
		return _r

	def pop( self ):
		# Return an entry (time,notif_type,str,cargo) # cargo main contains an information parsed from the notification
		if len(self):
			return super().pop()
		else:
			return Notif(None,None,None,None)


class SIM76XX:
	def __init__(self, uart, pwr_pin=None, uart_training=False, pincode=None ):
		self.uart = uart
		self.pwr_pin = pwr_pin
		self.pincode = pincode
		self.uart_training = uart_training
		self.pwr_time = time.time() if pwr_pin!=None else 0 # Time when the module did receive a PowerUp
		self.notifs = Notifications() # Store the unsollicitated notification (URC) received while processing responses


	def read_response( self, command, timeout=30000, filter=None, max_row=None, eor='OK' ):
		# read the response for the send_command() call
		start_time = time.ticks_ms()
		response = Response()
		#while time.ticks_diff(time.ticks_ms(), start_time) < 	:
		#	if self.uart.any():
		#		response.append(self.uart.read().decode())
		#return ''.join(response)

		# Read until timeout or OK
		while time.ticks_diff(time.ticks_ms(), start_time) < timeout:
			s = self.uart.readline()
			debug( '<-- %s' % s )
			if s==None:
				continue # Next round until time out
			s = s.decode('ASCII').replace('\r','').replace('\n','')
			if s==eor: # end of response 'OK':
				return response # OK received
			if 'ERROR' in s:
				raise CommandError( command, s )
			if self.notifs.is_urc( s ):
				self.notifs.append( s )

			if (len(s)>0) and ((filter==None) or (filter(s))): # Only add non empty lines
				if (max_row==None) or (len(response)<max_row):
					response.append(s)
		raise Timeout( command, timeout )


	def send_command(self, command, timeout=30000, filter=None, max_row=None):
		debug( '--> %s' % command )
		self.uart.write(command.encode('ASCII'))
		self.uart.write( bytes([13,10]) )
		return self.read_response( command, timeout, filter, max_row )


	def update( self ):
		# Check input on uart to pump out the unsolicitated message (URC) 
		# This covers time when no command is sent to the SIMCom module.
		#
		# Return True when some URC have been pumped
		#
		if self.uart.any()==0:
			return False

		_r = False
		s = self.uart.readline()
		while s:
			s = s.decode('ASCII').replace('\r','').replace('\n','')
			if self.notifs.is_urc( s ):
				self.notifs.append( s )
				_r = True
			s = self.uart.readline()
		return _r


	def is_alive( self ):
		""" Very basic test to check if a process resoibd ib tge UART """
		while self.uart.any():
			self.uart.read()
		self.uart.write( 'AT\r\n'.encode('ASCII') )
		time.sleep(0.5)
		_r = []
		while self.uart.any():
			_r.append( self.uart.read().decode('ASCII') )			
		return "OK\r\n" in (''.join(_r))


	def power_up( self ):
		""" Hardware Power on """
		# Check if already on
		if not( self.is_alive() ):
			# Start SIM module by pulsing PWRKEY low for for 1 sec
			if self.pwr_pin != None:
				self.pwr_pin.value( True )
				time.sleep(1)
				self.pwr_pin.value( False )
				self.pwr_time = time.time()
				time.sleep(10)

			# Send 3 AT command to stuluate autobaud detection
			if self.uart_training:
				debug( 'Training auto-baud detect' )
				for i in range(3):
					self.uart.write( "AT"+chr(13)+chr(10) )
					time.sleep_ms(300) # Wait for OK
				# Pump the OK response
				s = self.uart.readline()
				while s:
					s = self.uart.readline()

		#--- Initial setup ----
		self.send_command("ATE0") # echo off
		# Pin Code required ?
		_r = self.send_command("AT+CPIN?") 
		if _r.contains('SIM PIN'):
			if self.pincode==None:
				raise SIMComError( "pincode required!")
			_r=self.send_command("AT+CPIN=%s" % self.pincode )		
		# Do not report Phone call with  "+CLCC:"
		# _r = self.send_command("AT+CLCC=0")	


	def soft_power_on(self):
		""" Software Power On """
		self.pwr_time = time.time()
		return self.send_command('AT+CFUN=1')

	def soft_power_off(self):
		return self.send_command('AT+CPOF')

	def reset_module(self):
		return self.send_command('AT+CRESET')

	def set_power_mode(self, mode):
		return self.send_command(f'AT+CSCLK={mode}')

	def connect(self, apn, user='', password=''):
		self.send_command('AT+CGATT=1')
		self.send_command(f'AT+CSTT="{apn}","{user}","{password}"')
		self.send_command('AT+CIICR')
		return self.send_command('AT+CIFSR')

	def disconnect(self):
		return self.send_command('AT+CGATT=0')

	def flight_mode(self, enable):
		return self.send_command(f'AT+CFUN={0 if enable else 1}')

	@property
	def network_status(self):
		return self.send_command('AT+CREG?')

	@property
	def is_registered( self ):
		# check Network Status to detect if Mobile is registered on the network (or still searching for registration),
		# May raise exception when registration is denied or no network available
		_r = self.send_command('AT+CREG?').text
		if not( '+CREG:' in _r): #eg: +CREG: 0,1
			return False

		stat = int( _r.split(',')[1] )
		if stat == 3:
			raise SIMComError( 'Registration denied' )
		elif stat == 4:
			raise SIMComError( 'Registration unknown' )
		elif stat == 0:
			if (time.time() - self.pwr_time) < 300: # 5 first minutes after pwr up does not occurs exception
				return False
			else:
				raise SIMComError( 'Not searching for new operator' )
		elif stat in (1,5,6): # Home network, Roaming, SMS only
			return True
		elif stat == 2:
			return False # Searching new operator
		else:
			raise SIMComError( 'Registration status %i not supported' % stat )



