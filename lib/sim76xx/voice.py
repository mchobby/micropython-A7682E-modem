# Voice call service
#
#
from micropython import const

DIR_OUT = const(0) # Mobile OUTGOING call
DIR_IN = const(1) # Mobile INCOMING call

STATE_ACTIVE = const(0)
STATE_HELD   = const(1)
STATE_DIALING = const(2) # DIR_OUT only
STATE_ALERTING= const(3) # DIR_OUT only
STATE_INCOMING= const(4) # DIR_IN only
STATE_WAITING = const(5) # DIR_IN only
STATE_DISCONNECT = const(6)

class CallStatus:
    __slots__ = ("id","direction","state","mode", "mode", "multiparty", "phone", "addr_type", "alpha")
    def __init__(self, s ):
        values = s.split(',')
        self.id = int( values[0] )
        self.direction = int( values[1] ) # DIR_OUT, DIR_IN
        self.state = int( values[2] ) # STATE_xxx
        self.mode  = int( values[3] ) # 0=voice, 1=data, 2=fax, 9=unknown
        self.multiparty = True if values[4]=="1" else False
        if len(values)>=6:
            self.phone = values[5]  # Phone Number
            # 128=restricted number type, 145=international number, 
            # 161=national number, 177=network specific, 129=Otherwise
            self.addr_type = int(values[6]) 
        if len(values)>=8:
            self.alpha = values[7] # Alphanumeric representation in the PhoneBook


class Voice:
    """ Manage Voice Call service """
    def __init__( self, sim ):
        self.sim = sim
        self.sim.send_command("AT+CVHU=0") # ATH must drop the call in mode 0 & 2

    def call(self, number):
        return self.sim.send_command(f'ATD{number};')

    def hang_up(self):
        return self.sim.send_command('ATH')

    def answer(self):
        return self.sim.send_command('ATA')

    @property
    def status(self):
        """ returns the call status text as returned by the modem """
        return self.sim.send_command('AT+CLCC')

    @property
    def call_status( self ):
        """ get the communication status object. One entry by established communication """
        _r = []
        for line in self.sim.send_command('AT+CLCC'):
            print( line )
            if line.startswith("+CLCC:"):
                _r.append( CallStatus( line[6:].strip() ))
        return _r


    def call_volume(self, level):
        return self.sim.send_command(f'AT+CLVL={level}')