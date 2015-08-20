#!/usr/bin/env python
import SimpleHTTPServer
import BaseHTTPServer



if __name__ == '__main__':
    HandlerClass = SimpleHTTPServer.SimpleHTTPRequestHandler
    ServerClass = BaseHTTPServer.HTTPServer
    BaseHTTPServer.test(HandlerClass, ServerClass)

   
"""
class StatVizServer(SimpleHTTPServer):
    pass
    594     HandlerClass.protocol_version = protocol
    595     httpd = ServerClass(server_address, HandlerClass)
    596 
    597     sa = httpd.socket.getsockname()
    598     print "Serving HTTP on", sa[0], "port", sa[1], "..."
    599     httpd.serve_forever()
"""


