 # Status Control are part of the Core features.
 #
 # They have been extracted from core.py to lighten the Core
 #
from micropython import const
from maps import map


 # Access Technology to mobile Network
ACT_GSM    = const(0) # GSM
ACT_GSMC   = const(1) # GSM Compact
ACT_UMTS   = const(2) # UTRAN
ACT_EGPRS  = const(3) # GSM w/EGPRS
# UTRAN is UMTS networks (3G)
ACT_HSDPA  = const(4) # UTRAN w/HSDPA 
ACT_HSUPA  = const(5) # UTRAN w/HSUPA
ACT_HSDPA_HSUPA = const(6) # UTRAN w/HSDPA and HSUPA
# Evolved Universal Terrestrial Radio Access Network
ACT_EUTRAN      = const(7) # EUTRAN
ACT_HSPA_PLSU   = const(8) # UTRAN HSPA+

ACCESS_TECHNOLOGY = {ACT_GSM : "GSM", ACT_GSMC : "GSM Compact", ACT_UMTS : "UTRAN", ACT_EGPRS : "GSM w/EGPRS", \
	ACT_HSDPA : "UTRAN w/HSDPA", ACT_HSUPA : "UTRAN w/HSUPA", ACT_HSDPA_HSUPA : "UTRAN w/HSDPA and HSUPA", \
	ACT_EUTRAN : "EUTRAN", ACT_HSPA_PLSU : "UTRAN HSPA+" }


NETMODE_NO_SERVICE = const(0)
NETMODE_GSM   = const(1)
NETMODE_GPRS  = const(2)
NETMODE_EDGE  = const(3)
NETMODE_WCDMA = const(4)
NETMODE_HSDPA = const(5)
NETMODE_HSUPA = const(6)
NETMODE_HSPA  = const(7) # HSDPA and HSUPA, WCDMA
NETMODE_LTE   = const(8)

NETWORK_MODE = { NETMODE_NO_SERVICE : "no service", NETMODE_GSM : "GSM", NETMODE_GPRS : "GPRS", NETMODE_EDGE : "EDGE", \
	NETMODE_WCDMA : "WCDMA", NETMODE_HSDPA : "HSDPA", NETMODE_HSUPA : "HSUPA", NETMODE_HSPA : "HSPA", NETMODE_LTE : "LTE" }

class NetworkScan:
	__slots__ = ['status','operator_long','operator','operator_num','act'] 

	STATUS_UNKNOWN = 0
	STATUS_AVAILABLE = 1
	STATUS_CURRENT = 2
	STATUS_FORBIDDEN = 3

	def __init__( self ):
		self.status = NetworkScan.STATUS_UNKNOWN
		self.operator_long = ''
		self.operator = ''
		self.operator_num = -1
		self.act = ACT_GSM 

	def load_from( self, quad ):
		# load information from the quadruplet/quintuplet of information 
		# [ 2,"Orange B","Orange B","20610",0 ]
		self.status = int( quad[0] )
		self.operator_long = quad[1].replace('\"', '')
		self.operator = quad[2].replace('\"', '')
		self.operator_num = int( quad[3].replace('\"','') )
		self.act = int( quad[4] )

	def status_text( self, value ):
		return ('unknown','available','current','forbidden')[value]

	def __repr__( self ):
		return '<NetworkScan operator:%s (%s , %i), status: %i (%s), act: %i (%s)>' % (self.operator,self.operator_long, self.operator_num, \
			self.status, self.status_text(self.status), self.act, ACCESS_TECHNOLOGY[self.act] )

class Control:
	def __init__( self, sim ):
		self.sim = sim

	@property
	def voltage(self):
		_r = self.sim.send_command('AT+CBC')
		return float( _r[0].split(' ')[1].replace('V','') )


	@property
	def cpu_temp(self):
		_r = self.sim.send_command('AT+CPMUTEMP')
		return float( _r[0].split(' ')[1] )


	@property
	def network_info( self ):
		""" (Operator_name, Access_technology) or none """
		_r = self.sim.send_command( 'AT+COPS?', 60000 ) # Operator selection
		if len(_r)<=0 :
			return None

		# +COPS: 0,2,"20610",3
		data = _r[0].split(",")
		if data[1]=="2": # Numeric operator --> Retreive it from COPN 
			# Operator number is double quoted "20610"
			_oper = data[2]
			_r = self.sim.send_command( 'AT+COPN', 60000, lambda s : _oper in s ) # Use a filter
			if len(_r)==0:
				_oper = 'unknown'
			else: # Parsing the result from  +COPN: "20813","Contact"
				_oper = _r[0].split(',')[1].replace('\"','')
		else: # alphanumeric operator --> take it from COPS response
			_oper = data[2].replace('\"','') # strip quote
			
		# Do we have an Access_technology in the response ?
		if len(data)>3:
			_act = int(data[3]) # See ACT_ constants
		else:
			_act = 0

		return ( _oper, _act )

	@property
	def network_mode( self ):
		""" Current network mode (like GSM, GPRS, EDGE, HSDPA, ... LTE) """
		_r = self.sim.send_command( "AT+CNSMOD?" , 9000 )
		return int( _r[0].split(': ')[1].split(',')[1] ) # see NETMODE_xxx

	@property
	def network_rssi( self ):
		""" Quality of connexion in dBm or 99 (not known) """
		_r = self.sim.send_command( "AT+CSQ" , 9000 )
		val = int( _r.text.split(' ')[1].split(',')[0] ) # +CSQ: 31,99 

		if val==0:
			return -113
		elif val==1:
			return -111
		elif val==2:
			return -109
		elif val <= 30 :
			return int(map( val, 2, 30, -109, -53 ))
		elif val == 31:
			return -51
		elif val == 99:
			return 99 # not known or not detectable
		return 99

	@property
	def sim_serial( self ):
		"""  SIM Card serial number (20 digit) also named IIC ID """
		_r = self.sim.send_command( "AT+CICCID" , 9000 )
		return _r[0].split(' ')[1]

	@property
	def imei( self ):
		"""  IMEI : International Mobile station Equipment Identity (15 digits) """
		_r = self.sim.send_command( "AT+CGSN" )
		return _r[0]


	def scan_networks( self ):
		_r = self.sim.send_command( "AT+COPS=?" , 45000 )
		_r = _r[0].split(': ')[1].split(',,')[0].split('),')
		result = []
		for entry in _r: # (2,"Orange B","Orange B","20610",0)
			item = NetworkScan()
			item.load_from( entry.replace('(','').replace(')','').split(",") )
			result.append( item )

		return result