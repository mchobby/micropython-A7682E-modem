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
        return _r[0].split(': ')[1].split(',')[1] # Ignore the cid

    def write(self, data):
        # will send a buffer
        self.sim.uart.write(data)

    def read(self):
        # Will return a buffer
        return self.sim.uart.read()
