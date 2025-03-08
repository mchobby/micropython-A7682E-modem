""" Capture DTMF Tone and/or send DTMF tone over a voice call """

# This class also register in the URC Notification loop and manage its own notification storage
# So the following methods must ne declared:
#	- clear() : clear notifications
#	- is_urc( s ) : True when s contains an URC I'm intended to 
#	- append( s ) : The URC I should manage and store instead of core.Notifications
class DTMF:

	def __init__(self, sim):
		self.sim = sim
		self._rx_dtmf = '' # key-pressed remotely
		self._has_new = False
		self.set_duration( 600 ) # Set max duration for Tone sending
		self.sim.notifs.register( self ) # I want to be notified of URCs

	def set_duration( self, duration ):
		""" Tone duration """
		assert 300<= duration <=600, "Invalid duration in 1/10 ms (300 to 600)"
		self.sim.send_command( f"AT+VTD={duration}" )

	# --- Notifications Interface -------------------------
	def clear( self ):
		# Called by Notifications ! 
		self._rx_dtmf = '' # key-pressed remotely
		self._has_new = False


	def is_urc( self, s ):
		# Called by Notifications ! 
		# Check if it is an URC for DTMF class
		return  s.startswith( "+RXDTMF:" )

	def append( self, s ):
		# Received "Dual Tone Multi-Frequence" are stored separately
		# Not handled as Notification but registered into separate variable
		self._rx_dtmf += s.split( ": " )[1] 
		self._has_new = True

	# --- DTMF related ------------------------------------

	@property
	def received( self ):
		# DTMF received during a voice call.
		# Could capture 0 to 9, A..D, * and #
		self._has_new = False 
		return self._rx_dtmf

	@property
	def has_new( self ):
		# return True when new DTMF received (and clear the flag)
		_v = self._has_new
		self._has_new = False 
		return _v
	

	def send_tone( self, c, duration=600 ):
		# One DTMF letter 0..9,*,#,A..D and duration (300..600)
		assert len(c)==1 and (c in "0123456789*#ABCD"), "Invalid tone character"
		assert 300<= duration <=600, "Invalid duration in 1/10 ms (300 to 600)"
		self.sim.send_command( f"AT+VTS={c},{duration}" )

	def send_dtmf( self, s ):
		for c in s:
			assert c in "0123456789*#ABCD", "Invalid char %s in DTMF string %s" % (c, s)
		self.sim.send_command( f'AT+VTS="{s}"' )