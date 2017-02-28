import gzip
import json
import os
import ssl
import time
from StringIO import StringIO
import tempfile
import urllib2
import SimpleHTTPServer
import SocketServer
import signal

from twisted.internet import threads, reactor
from twisted.internet.defer import inlineCallbacks, Deferred
from twisted.internet.protocol import ProcessProtocol

from globaleaks.models.config import PrivateFactory, load_tls_dict
from globaleaks.utils.sock import reserve_port_for_ip
from globaleaks.orm import transact
from globaleaks.workers import supervisor, process
from globaleaks.workers.https_worker import HTTPSProcess

from globaleaks.tests import helpers
from globaleaks.tests.utils import test_tls

@transact
def toggle_https(store, enabled):
    PrivateFactory(store).set_val('https_enabled', enabled)

class TestProcessSupervisor(helpers.TestGL):
    @inlineCallbacks
    def setUp(self):
        super(TestProcessSupervisor, self).setUp()
        yield test_tls.commit_valid_config()

    @inlineCallbacks
    def test_init_with_no_launch(self):
        yield toggle_https(enabled=False)
        sock, fail = reserve_port_for_ip('127.0.0.1', 43434)
        self.assertIsNone(fail)

        ip, port = '127.0.0.1', 43435

        p_s = supervisor.ProcessSupervisor([sock], ip, port)
        yield p_s.maybe_launch_https_workers()

        self.assertFalse(p_s.is_running())

        yield p_s.shutdown()

        self.assertFalse(p_s.shutting_down)
        self.assertFalse(p_s.is_running())


    @inlineCallbacks
    def test_init_with_launch(self):
        yield toggle_https(enabled=True)
        sock, fail = reserve_port_for_ip('localhost', 43434)
        self.assertIsNone(fail)

        ip, port = '127.0.0.1', 43435

        p_s = supervisor.ProcessSupervisor([sock], ip, port)
        yield p_s.maybe_launch_https_workers()

        self.assertTrue(p_s.is_running())

        yield p_s.shutdown()

        self.assertFalse(p_s.shutting_down)
        self.assertFalse(p_s.is_running())


@transact
def wrap_db_tx(store, f, *args, **kwargs):
    return f(store, *args, **kwargs)

class TestSubprocessRun(helpers.TestGL):

    @inlineCallbacks
    def setUp(self):
        super(TestSubprocessRun, self).setUp()

        with open('hello.txt', 'w') as f:
            f.write('Hello, world!\n')

        https_sock, _ = reserve_port_for_ip('127.0.0.1', 9443)
        self.https_socks = [https_sock]
        ssl._https_verify_certificates(enable=False)
        yield test_tls.commit_valid_config()

    @inlineCallbacks
    def test_https_process(self):
        valid_cfg = {
            'proxy_ip': '127.0.0.1',
            'proxy_port': 43434,
            'tls_socket_fds': [sock.fileno() for sock in self.https_socks],
            'debug': False,
        }
        db_cfg = yield wrap_db_tx(load_tls_dict)
        valid_cfg.update(db_cfg)

        tmp = tempfile.TemporaryFile()
        tmp.write(json.dumps(valid_cfg))
        tmp.seek(0,0)
        tmp_fd = tmp.fileno()

        self.http_process = HTTPSProcess(fd=tmp_fd)

        # Connect to service ensure that it responds with a 502
        yield threads.deferToThread(self.fetch_resource_with_fail)

        # Start the HTTP server proxy requests will be forwarded to.
        self.pp = SimpleServerPP()
        reactor.spawnProcess(self.pp, 'python', args=['python', '-m', 'SimpleHTTPServer', '43434'])
        yield self.pp.start_defer

        # Check that requests are routed successfully
        yield threads.deferToThread(self.fetch_resource)
        yield threads.deferToThread(self.fetch_resource_with_gzip)

    def fetch_resource_with_fail(self):
        try:
            req = urllib2.urlopen('https://127.0.0.1:9443')
            self.fail('Request had to throw a 502')
        except urllib2.HTTPError as e:
            self.assertEqual(e.code, 502)
            return

    def fetch_resource(self):
        urllib2.urlopen('https://127.0.0.1:9443/')

    def fetch_resource_with_gzip(self):
        request = urllib2.Request('https://127.0.0.1:9443/hello.txt')
        request.add_header('Accept-encoding', 'gzip')
        response = urllib2.urlopen(request)
        is_gzipped = response.info().get('Content-Encoding') == 'gzip'
        self.assertTrue(is_gzipped)

        s = response.read()
        buf = StringIO(s)
        f = gzip.GzipFile(fileobj=buf)
        data = f.read()

        self.assertEqual(data, 'Hello, world!\n')

    def tearDown(self):
        for sock in self.https_socks:
            sock.close()

        if hasattr(self, 'http_process'):
            self.http_process.shutdown()
        if hasattr(self, 'pp'):
            self.pp.transport.loseConnection()
            self.pp.transport.signalProcess('KILL')

        helpers.TestGL.tearDown(self)


class SimpleServerPP(ProcessProtocol):
    def __init__(self):
        self.start_defer = Deferred()
        process.set_pdeathsig(signal.SIGINT)

    def connectionMade(self):
        self.start_defer.callback(None)
        # You might think that you can accept connections at this point,
        # but actually the subprocess is not ready.
        time.sleep(1)
        pass

    def processEnded(self, reason):
        pass
