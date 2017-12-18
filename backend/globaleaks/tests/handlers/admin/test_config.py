# -*- coding: utf-8
from globaleaks.handlers.admin import config
from globaleaks.state import State
from globaleaks.tests import helpers

from twisted.internet import defer, reactor


class TestHostnameConfig(helpers.TestHandler):
    _handler = config.AdminConfigHandler

    @defer.inlineCallbacks
    def test_put(self):
        State.tenant_cache[1].anonymize_outgoing_connections = False

        # Add a file to the tmp dir
        with open('./robots.txt', 'w') as f:
            f.write("User-agent: *\n" +
                    "Allow: /\n"+
                    "Sitemap: http://localhost/sitemap.xml")

        # Start the HTTP server proxy requests will be forwarded to.
        self.pp = helpers.SimpleServerPP()

        # An extended SimpleHTTPServer to handle the addition of the globaleaks header
        e = ""+\
        "from SimpleHTTPServer import SimpleHTTPRequestHandler as rH; "+\
        "from SimpleHTTPServer import test as t; "+\
        "of = rH.end_headers; rH.end_headers = lambda s: s.send_header('Server', 'GlobaLeaks') or of(s); "+\
        "t(HandlerClass=rH)"

        yield reactor.spawnProcess(self.pp, 'python', args=['python', '-c', e, '43434'], usePTY=True)

        yield self.pp.start_defer

        handler = self.request({'operation': 'verify_hostname', 'args': {'value': 'localhost:43434'}}, role='admin')

        yield handler.put()

    @defer.inlineCallbacks
    def tearDown(self):
        if hasattr(self, 'pp'):
            self.pp.transport.loseConnection()
            self.pp.transport.signalProcess('KILL')

        yield super(TestHostnameConfig, self).tearDown()
