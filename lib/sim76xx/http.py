""" Get or POST HTTP content """
from .gprs import GPRS
from .core import SIMComError

# HTTP Content Type
TEXT_HTML = 'text/html' # see rfc7231 section-3.1.1.5 @  https://www.rfc-editor.org/rfc/rfc7231#section-3.1.1.5

# HTTP REQUEST METHOD 
METHOD_GET = 0
METHOD_POST = 1
METHOD_HEAD = 2
METHOD_DELETE = 3
METHOD_PUT = 4

class HttpError( SIMComError ):
    pass

class HttpResponse:
    # Allows to read the response per chunks (eg:128 bytes)
    def __init__(self, owner, response_len, chunk_size ):
        self.owner = owner # Owner is the HTTP object
        self._len = response_len
        self._offset = 0
        self._chunk = chunk_size

    def _http_read( self, offset, len ):
        # perform a read with direct access on serial interface
        # Return: bytes
        self.owner.write( f'AT+HTTPREAD={offset},{len}\r\n' )
        # We must have an OK as response
        s = self.owner.readline()
        while not(s == 'OK'):
            s = self.owner.readline()
            if 'ERROR' in s:
                raise HttpError( '_http_read() got an error' )
        # We must also have a "+HTTPREAD:" just before the response
        s = self.owner.readline()
        while not('+HTTPREAD:' in s):
            s = self.owner.readline()
            if 'ERROR' in s:
                raise HttpError( '_http_read() got an error (2)' )
        # Now we have the content to be read
        _d = self.owner.read( len )
        # We must have another "+HTTPREAD:" just the response
        s = self.owner.readline()
        while not('+HTTPREAD:' in s):
            s = self.owner.readline()
            if 'ERROR' in s:
                raise HttpError( '_http_read() got an error (2)' )
        return _d 

    def read( self ):
        # Will returns a chunck of bytes() (or None when all reads)
        #print( "len", self._len,"offset", self._offset)
        remain_to_read = self._len - self._offset
        if remain_to_read == 0:
            # No more to read
            return None
        elif remain_to_read > self._chunk:
            # Read a full chunck
            _d = self._http_read( self._offset, self._chunk )
            self._offset += self._chunk            
            return _d
        else:
            _d = self._http_read( self._offset, remain_to_read )
            self._offset += remain_to_read
            return _d


class HTTP( GPRS ):
    def __init__(self, sim):
        super().__init__( sim )
        self._sslcfg_id = None # HTTPS Context
        self.connect_timeout = 30 # 20 to 120 seconds
        self.receive_timeout = 120 # 20 to 120 seconds
        self.status_code = 0 # Http Status Code & Http Error Code. See 16. AT commands for HTTP(s), 16.3 Command result codes
        self.response_len = 0  # HTTP response len (eg: by doing Get)
        self.sim.notifs.register( self ) # I want to be notified of URCs

    def enable(self, with_ssl=False ):
        super().enable() # Activate GPRS
        self.sim.send_command('AT+HTTPINIT')
        if with_ssl: 
            self._sslcfg_id = 0 # Configure the SSL context #0
            self._configure_ssl( sslcfg_id=self._sslcfg_id )

    def disable(self):
        self.sim.send_command('AT+HTTPTERM')
        super().disable() # deactivate GPRS
        

    def raise_http_error( self, status_code ):
        # Lazy Ressource Load
        _mod = __import__( 'sim76xx.httpmsg' )

        _ERRORCODE_MSG  = eval( '_mod.httpmsg.ERRORCODE_MSG', {'_mod':_mod} )
        if _ERRORCODE_MSG==None:
            raise HttpError( f'HTTP Error {status_code}' )
        if status_code in _ERRORCODE_MSG:
            raise HttpError( 'HTTP Error %s : %s' % (status_code, _ERRORCODE_MSG[status_code]) )

        _STATUSCODE_MSG = eval( '_mod.httpmsg.STATUSCODE_MSG', {'_mod':_mod} )
        if status_code in _STATUSCODE_MSG:
            raise HttpError( 'HTTP Error %s : %s' % (status_code, _STATUSCODE_MSG[status_code]) )


    # --- Notifications Interface -------------------------
    def clear( self ):
        # Called by Notifications ! 
        pass


    def is_urc( self, s ):
        # Called by Notifications ! 
        # Check if it is an URC for DTMF class
        return  s.startswith( "+HTTPACTION:" ) or s.startswith('+HTTPREAD: LEN,') or s.startswith("HTTPHEAD:")

    def append( self, s ):
        # Received "+HTTPACTION:" content
        # Not handled as Notification but registered into separate variable
        
        # get() may returns: "+HTTPACTION: 0,713,0" with method, status/error_code, data_len
        if s.startswith( "+HTTPACTION:" ):
            vals = s.split( ": " )[1].split(',') 
            self.status_code = int(vals[1]) 
            self.response_len = int(vals[2])
            if self.status_code >= 400:
                self.raise_http_error( self.status_code )
        elif s.startswith('+HTTPREAD: LEN,'):
            vals = s.split(',')
            self.response_len = int(vals[1]) # Get response len
        

    # --- Toolbox ----------------------------------------

    def _url(self, url):
        # Set the URL
        if 'https:' in url.lower(): 
            if self._sslcfg_id==None :
                raise HttpError( 'No HTTPS context configured!')
            else:
                #print( "Activating SSL parameter")
                self.sim.send_command(f'AT+HTTPPARA="SSLCFG",{self._sslcfg_id}')    
        self.status_code = 0
        self.response_len = 0
        self.sim.send_command(f'AT+HTTPPARA="URL","{url}"')
     
    def _configure_ssl( self, sslcfg_id ):
        """ Configure the SSL for HTTPS access (no verify server and client """
        #print( self.sim.send_command("AT+CSSLCFG=?") )
        # Set the SSL version of the first SSL context
        self.sim.send_command(f'AT+CSSLCFG="sslversion",{sslcfg_id},4' )

        # Set the authentication mode(not verify server) for SSL context
        self.sim.send_command(f'AT+CSSLCFG="authmode",{sslcfg_id},0' )

        # Enable reporting +CCHSEND result
        self.sim.send_command('AT+CCHSET=1')

        # start SSL service, activate PDP context
        self.sim.send_command('AT+CCHSTART')

        # Set the first SSL context to be used in the SSL connection
        self.sim.send_command(f'AT+CCHSSLCFG={sslcfg_id},0')



    # --- HTTP CORE --------------------------------------
    def get(self, url, content_type=TEXT_HTML, chunck_size=128 ):
        # Returns an io stream
        self._url( url )
        self.sim.send_command(f'AT+HTTPPARA="CONNECTTO",{self.connect_timeout}')
        self.sim.send_command(f'AT+HTTPPARA="RECVTO",{self.receive_timeout}')
        self.sim.send_command(f'AT+HTTPPARA="CONTENT","text/plain"')
        self.sim.send_command(f'AT+HTTPPARA="ACCEPT","*/*"')
        # self.sim.send_command(f'AT+HTTPPARA="USERDATA","the_user_data"') # Customize the header information
        
        # may returns URC: "+HTTPACTION: 0,713,0" with method, error_code, data_len
        self.sim.send_command(f'AT+HTTPACTION={METHOD_GET}', timeout=120_000 )

        # Reading the Header will capture status & length 
        self.sim.send_command('AT+HTTPHEAD')

        # URC should have been populated the response_len
        return HttpResponse( self, self.response_len, chunck_size )

    def post(self, data):
        # Returns an io stream
        self.sim.send_command(f'AT+HTTPDATA={len(data)},10000')
        self.write(data) # GPRS.write()
        self.sim.send_command('AT+HTTPACTION=1')
        return self.sim.uart

        