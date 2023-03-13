# -*- coding: utf-8 -*-
#
# Handler exposing viewer application
from globaleaks.handlers.staticfile import StaticFileHandler

class ViewerHandler(StaticFileHandler):
    def __init__(self, state, request):
        StaticFileHandler.__init__(self, state, request)

        if not state.settings.disable_csp:
            request.setHeader(b'Content-Security-Policy',
                              b"base-uri 'none';"
                              b"connect-src blob:;"
                              b"default-src 'none';"
                              b"form-action 'none';"
                              b"frame-ancestors 'self';"
                              b"img-src blob:;"
                              b"media-src blob:;"
                              b"script-src 'self';"
                              b"style-src 'self';")

        request.setHeader(b'Access-Control-Allow-Origin', b'null')
