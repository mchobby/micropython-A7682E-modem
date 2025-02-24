# Short Message Service (SMS).
#
#
import time
import binascii
from .core import CommandError

class SMSError( CommandError ):
	pass

class SMSHeader:
	__slots__ = ['id','status', 'phone', 'dt', 'tzd' ] 

	def __init__( self, owner, s ): 
		def status_as_int( value ):
			for k,v in owner.STATUS_TEXT.items():
				if s==v:
					return k
			return owner.ALL # default value

		# +CMGL: 21,"REC READ","+32496928320","","25/02/16,16:53:10+4"
		_val=s.split(': ')[1].split(",")
		#print( _val )
		self.id = int(_val[0])
		self.status = status_as_int(_val[1].replace('"',''))
		self.phone  = _val[2].replace('"','')
		_date = _val[4].replace('"','')
		_time = _val[5].replace('"','')
		#print( _date[0:2], _date[3:5], _date[6:8], _time[0:2], _time[3:5], _time[6:8] )
		self.dt = time.mktime( (2000+int(_date[0:2]),int(_date[3:5]),int(_date[6:8]),int(_time[0:2]),int(_time[3:5]),int(_time[6:8]),0,0,0) )
		self.tzd = _time[8:]

	def __repr__( self ):
		return f"<SMSRow id:{self.id}, status:{self.status}, phone:{self.phone}>"


class Message( SMSHeader ):
	def __init__( self, owner, index, strlst ):
		# Missing id in the reader when read an index message
		#   +CMGR: "REC READ","+32499120327","","20/10/24,12:14:34+8"
		self.strlst = strlst
		_vals = strlst[0].split(": ")
		super().__init__(owner, f"{_vals[0]}: {index},{_vals[1]}" )

	@property
	def message(self):
		# if only on line of data -AND- dividible by 2 -AND- only hexa content MAYBE we have an UTF16 encoded string 
		#   0056006F006900630065006D006100 
		if ( len(self.strlst)==2 ) and (len(self.strlst[1])%2==0) and ( all([ ch in '0123456789ABCDEF' for ch in self.strlst[1]]) ):
			utf16 = binascii.unhexlify(self.strlst[1]) # Gives 2bytes per characters
			_bytes=bytearray(len(utf16)//2)
			for i in range( len(utf16)//2 ): # Keep seconds bytes only
				_bytes[i]=utf16[i*2+1]
			# try to decode ANSI (ASCII is limited to 0..127)
			_r = ''
			for i in range( len(utf16)//2 ):
				try:
					_r+=chr(_bytes[i])
				except:
					_r+='?'
			return _r

		# Return original content
		return '\r\n'.join(self.strlst[1:])
	

class SMS:
	MODE_PDU  = const( 0 ) # PDU is a binary mode : https://www.gsmfavorites.com/documents/sms/pdutext/
	MODE_TEXT = const( 1 )

	# For list() 
	RECEIVED_UNREAD = const( 0 ) # received unread message (i.e. new message)
	RECEIVED_READ   = const(1) # received read message
	UNSENT = const(2) # stored unsent message
	SENT   = const(3) # stored sent message
	ALL	= const(4) # all messages	

	STATUS_TEXT = {RECEIVED_UNREAD : "REC UNREAD", RECEIVED_READ : "REC READ", UNSENT : "STO UNSENT", SENT : "STO SENT", ALL : "ALL"}

	def __init__( self, sim ):
		self.sim = sim
		self.mode = None
		self.set_mode( SMS.MODE_TEXT )
		self.wait_ready()

	def set_mode( self, sms_mode ):
		self.mode = sms_mode
		return self.sim.send_command( 'AT+CMGF=%s' % sms_mode )

	def get_service_address( self ): 
		# Service Center Address also named sca. 
		# Example of response: ['+CSCA: "+32495002530",145']
		return self.sim.send_command( 'AT+CSCA?' )

	def wait_ready( self, timeout=30000 ):
		# SMS service is not available immediately after power-up.
		# So not possible so send SMS or list SMS because " +CMS ERROR: unknown error" is returned
		start = time.ticks_ms()
		while time.ticks_diff( time.ticks_ms(), start ) < timeout:
			try:
				self.list( self.UNSENT, max_row=2 )
				return # Great SMS service is ready
			except CommandError as err:
				if not("+CMS ERROR:" in str(err)):
					raise err
			time.sleep(1) # Service not ready. Make a new try
		# Timeout reached
		raise SMSError( "wait_ready()", "SMS service ready timeout!")

	def send(self, number, message):
		""" Send ASCII message (7bit). Returns storage index """
		cmd = f'AT+CMGS="{number}"\r\n'
		self.sim.uart.write( cmd.encode('ASCII') )
		# wait for the > char
		self.sim.read_response( cmd, timeout=10000, eor='> ' )
		self.sim.uart.write( message.encode('ASCII') )
		self.sim.uart.write( b'\x1A' )
		try:
			_r = self.sim.read_response( cmd )
		except CommandError as err:
			if '+CMS ERROR:' in str(err):
				raise SMSError( str(err) )
			else:
				raise err
		#print( _r )
		return int(_r[0].split(' ')[1]) # +CMGS: 165


	def read(self, index):
		_resp = self.sim.send_command(f'AT+CMGR={index}')
		return None if len(_resp)==0 else Message( self, index, _resp )

	def delete(self, index):
		return self.sim.send_command(f'AT+CMGD={index}')

	def list(self, status, max_row=20 ):
		if self.mode == SMS.MODE_TEXT:
			cmd = f'AT+CMGL="{self.STATUS_TEXT[status]}"' 
		else:
			cmd = f'AT+CMGL={str(status)}"' 
		# Filter to keeps the header only
		_rows = self.sim.send_command(cmd, timeout=9000, filter=lambda s:"+CMGL:" in s, max_row=max_row)
		return [ SMSHeader(self,_line) for _line in _rows ] # décoding NOT CHECKED for PDU mode