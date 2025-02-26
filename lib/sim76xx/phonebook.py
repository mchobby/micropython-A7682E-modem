# Phonebook interface
#
# Usually support 4 storage type (see doc about AT+CPBS Select Phonebook Storage)
#  - SM : SIM phonebook (default)
#  - ON : SIM own number list
#  - FD : SIM fix dialing phonebook
#  - AP : Application phonebook (for active USIM application)
#
from .core import SIMComError, CommandError
import collections

class PhonebookError( SIMComError ):
    pass

# ntype is the format of phone number
BookEntry = collections.namedtuple('BookEntry', ['index','name','number','ntype'] ) 

class Phonebook:
    SIM = "SM" # Storage = SIM 
    OWN = "ON" # Storage = OWN
    FIX = "FD" # Storage = Fix Dialing

    def __init__(self, sim):
        self.sim = sim
        # Get PhoneBook entry parameters
        _s = sim.send_command("AT+CPBW=?") # +CPBW: (1-250),40,(129,145,161,177),14 
        _s = _s[0].split('CPBW: ')[1].split(',(') # -> (1-250),40   -and-    129,145,161,177),14
        
        self.phone_len = int(_s[0].split(',')[1]) # 40
        self.index_min = int( _s[0].split(',')[0].split('-')[0].replace('(','') )
        self.index_max = int( _s[0].split(',')[0].split('-')[1].replace(')','') )
        self.name_len = int(_s[1].split('),')[1] ) # 14
        # Default alphabet (IRA) is 7 bits encoding scheme. Obvioulsy we should be able to encode 14 chars.
        # By experience, it seems that A7682E internally requires 2 bytes encoding per letter!
        self.name_len = self.name_len // 2
        # Select the SIM PhoneBook
        self.open( self.SIM )


    def open(self, storage ):
        # Select a storage and return a list
        return self.sim.send_command(f'AT+CPBS="{storage}"', 9000 )

    @property
    def stat( self ):
        # returns ( used, total )
        _s = self.sim.send_command('AT+CPBS?', 9000 )
        return ( int(_s[0].split(",")[1]) , int(_s[0].split(",")[2]) )

    def write(self, index, name, number):
        # Write an entry
        if len(name)>self.name_len:
            raise PhonebookError( f'{name} name exceed max len of {self.name_len}' )
        if len(number)>self.phone_len:
            raise PhonebookError( f'Phone {number} exceed max len of {self.phone_len}' )
        if not(self.index_min <= index <= self.index_max):
            raise PhonebookError( f'index {index} ouside of range {self.index_min}-{self.index_max}' )
        self.sim.send_command(f'AT+CPBW={index},"{number}",129,"{name}"') 


    def read(self, index):
        # Return a named typle with initialized datas (or "None" datas when not found)
        try:
            _s=self.sim.send_command(f'AT+CPBR={index}')
            _s=_s[0].split(": ")[1].split(",")
            return BookEntry( int(_s[0]), _s[3].replace('"',''), _s[1].replace('"',''), int(_s[2])  )
        except CommandError as err:
            if 'not found' in str(err):
                return BookEntry( index, None, None, None )
            else:
                raise

    def list(self):
        # Return a list of used index
        _l = []
        for index in range( self.index_min, self.index_max+1):
            try:
                _s=self.sim.send_command(f'AT+CPBR={index}')
                _l.append(index)
            except CommandError as err:
                if 'not found' in str(err):
                    pass
                else:
                    raise
        return _l
        

    def delete(self, index):
        return self.sim.send_command(f'AT+CPBW={index}')

