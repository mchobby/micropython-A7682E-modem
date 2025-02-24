# Voice call service
#
#
class Voice:
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
        return self.sim.send_command('AT+CLCC')

    def call_volume(self, level):
        return self.sim.send_command(f'AT+CLVL={level}')