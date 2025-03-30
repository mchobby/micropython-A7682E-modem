import time
from .core import debug, Timeout

class GPRS:
    def __init__(self, sim):
        self.sim = sim

    def set_apn(self, apn, user='', password=''):
        # Set the PDP (Packet Data Protocol) for the APN (Access Point Name)
        self.sim.send_command(f'AT+CGDCONT=1,"IP","{apn}"') # for cid=1 set IP (support IPV6 or IPV4V6)
        if user and password:
            self.sim.send_command(f'AT+CGAUTH=1,1,"{user}","{password}"')

    def enable(self):
        # Packet Domain activated
        self.sim.send_command('AT+CGATT=1')
        # PDP (Packet Data Protocol) Context activate for cid=1
        self.sim.send_command('AT+CGACT=1,1') # enable,cid

    def disable(self):
        self.sim.send_command('AT+CGACT=0,1')
        self.sim.send_command('AT+CGATT=0')

    @property
    def ip(self):
        #return self.sim.send_command('AT+CIFSR')

        # Will return '+CGPADDR: 1,10.190.7.165'
        _r = self.sim.send_command('AT+CGPADDR=1' ) # cid
        for line in _r:
            if line.startswith( '+CGPADDR:' ):
                return line.split(',')[1] # Ignore the cid
        return '?.?.?.?'

    def write(self, data):
        # will send a buffer
        debug( '--(GPRS)--> %s' % data )
        self.sim.uart.write(data)

    def read(self , len=None):
        # Will return a buffer
        if len==None:
            _d = self.sim.uart.read()
        else:
            _d = self.sim.uart.read( len )
        debug( '<--(GPRS)-- %s' % _d )
        return _d

    def readline(self, timeout=3000):
        # Read a line until timeout
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < timeout:
            s = self.sim.uart.readline()
            debug( '<==(GPRS)== %s' % s )
            if s==None:
                continue # Next round until time out
            s = s.decode('ASCII').replace('\r','').replace('\n','')
            return s 

        raise Timeout( 'GPRS.readline()', timeout )
