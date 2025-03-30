# HTTP Support for SimCom A7682 

As explained in the main [readme](readme.md) file, the `AT+HTTPINIT` cannot be called multiple times. 

In case error while processing a request, the 'AT+HTTPINIT' cannot be called again and the 'AT+HTTPTERM' (terminate) will also returns an error.

The only solution up to now is to Power Cycle the SimCom module (make a cold start)

## Reading response

The `HttpResponse` class is used to fetch back the content of the response.

To minimize the impact on the memory, the content is `read()` by chunck (default 128 bytes) and data is returned as `bytes()` array. Transformation to `str` requires to `decode()`the array of retreived data.

The `read()` method will returns None when all the data are fetched.

```
_data = response.read()
while _data:
	print( _data.decode('ASCII') )
	_data = response.read()
```

## GET method

The following [test_get_http.py](examples/http/test_get_http.py) will load the content of the file stored on the WebServer.

![view of the test.txt file](docs/_static/test_txt.jpg)

```
from machine import UART, Pin
from sim76xx import *
from sim76xx.http import HTTP
import time

URL = 'http://www.mchobby.be/test.txt'

# Pico 
pwr = Pin( Pin.board.GP26, Pin.OUT, value=False )
uart = UART( 0, tx=Pin.board.GP0, rx=Pin.board.GP1, baudrate=115200, bits=8, parity=None, stop=1, timeout=500)
sim = SIM76XX( uart=uart, pwr_pin=pwr, uart_training=True, pincode="6778" )

print( "Power up")
sim.power_up()
print( "Wait Network registration")
while not sim.is_registered:
	print( " waiting")
	time.sleep(1)
print( "registered!" )


sim.notifs.clear()

http = HTTP( sim )
http.set_apn( "orange" ) # No password for this operator in Belgium
print( "Enable HTTP")
print( "  led will flash quickly..." )
http.enable()

print( "Getting URL %s (HTTP ONLY)" % (URL,))
response = http.get( URL )
print( "Status :", http.status_code )
print( "response length :", http.response_len )
print( "---- Notification messages ----")
while True:
	sim.update()
	if sim.notifs.any():
		print( sim.notifs.pop() )
	else:
		break
print( "---- Response ----")
# Reponse content is read by chunck to spare memory
# Each chunck is returned as bytes()
_data = response.read()
while _data:
	print( _data.decode('ASCII') )
	_data = response.read()

print( "-"*40 )

http.disable()
print( "That's all Folks!")
```

Which produce the following results

```
$ mpremote run examples/http/test_get_http.py 
Power up
Wait Network registration
 waiting
 waiting
 waiting
 waiting
 waiting
 waiting
registered!
Enable HTTP http://www.mchobby.be/test.txt (HTTP ONLY)
  led will flash quickly...
Getting URL
Status : 200
response length : 16
---- Notification messages ----
Notif(_time=1609553894, _type=0, source='+CGEV: ME PDN ACT 1,4', cargo=None)
---- Response ----
it works fines!

----------------------------------------
That's all Folks!
```

# SSL Support

__Remark:__ the current implementation of HTTPS does product error likes "HTTP Error 715 : Handshake failed" or "HTTP Error 706 : Receive/send socket data failed".

The SSL support can be checked bu querying the `AT+CSSLCFG=?` 

For SimCom A7682, the response is the following:

```
+CSSLCFG: "sslversion",(0-9),(0-4)
+CSSLCFG: "authmode",(0-9),(0-3)
+CSSLCFG: "ignorelocaltime",(0-9),(0,1)
+CSSLCFG: "negotiatetime",(0-9),(10-300)
+CSSLCFG: "cacert",(0-9),(5-108)
+CSSLCFG: "clientcert",(0-9),(5-108)
+CSSLCFG: "clientkey",(0-9),(5-108)
+CSSLCFG: "enableSNI",(0-9),(0,1)
```
