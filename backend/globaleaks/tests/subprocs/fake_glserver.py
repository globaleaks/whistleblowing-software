# An extended SimpleHTTPServer to handle the addition of the globaleaks header
from SimpleHTTPServer import SimpleHTTPRequestHandler as rH
from SimpleHTTPServer import test
of = rH.end_headers; rH.end_headers = lambda s: s.send_header('Server', 'GlobaLeaks') or of(s)
test(HandlerClass=rH)
