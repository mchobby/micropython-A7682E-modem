# A76XX_Series_AT Command Manual V1.12 - 16 AT Commands for HTTP(S) - 16.3 Command result codes
ERRORCODE_MSG = { 701: "Alert state", 702: "Unknown error", 703: "Busy", 704: "Connection closed error", 705: "Timeout", 706: "Receive/send socket data failed",
	707: "File not exists or other memory error", 708: "Invalid parameter", 709: "Network error", 710: "start a new ssl session failed", 711: "Wrong state",
	712: "Failed to create socket", 713: "Get DNS failed", 714: "Connect socket failed", 715: "Handshake failed", 716: "Close socket failed", 
	717: "No network error", 718: "Send data timeout", 719: "CA missed" }

STATUSCODE_MSG = {
	100: "Continue", 101: "Switching Protocols", 200: "OK", 201: "Created", 202: "Accepted", 203: "Non-Authoritative Information",
	204: "No Content", 205: "Reset Content", 206: "Partial Content", 300: "Multiple Choices", 301: "Moved Permanently", 302: "Found",
	303: "See Other", 304: "Not Modified", 305: "Use Proxy", 307: "Temporary Redirect", 400: "Bad Request", 401: "Unauthorized", 402: "Payment Required",
	403: "Forbidden", 404: "Not Found", 405: "Method Not Allowed", 406: "Not Acceptable", 407: "Proxy Authentication Required",  408: "Request Timeout",
	409: "Conflict", 410: "Gone", 411: "Length Required", 412: "Precondition Failed", 413: "Request Entity Too Large", 414: "Request-URI Too Large",
	415: "Unsupported Media Type", 416: "Requested range not satisfiable",
	378: "684A76XX Series_AT Command Manual_V1.12",
	417: "Expectation Failed", 500: "Internal Server Error", 501: "Not Implemented", 502: "Bad Gateway", 503: "Service Unavailable", 
	504: "Gateway timeout", 505: "HTTP Version not supported", 600: "Not HTTP PDU", 601: "Network Error", 602: "No memory", 603: "DNS Error", 
	604: "Stack Busy"  }

