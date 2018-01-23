# -*- coding: utf-8 -*-
import json
import ssl
import tempfile
import urllib2

from twisted.internet import threads, reactor
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.admin.https import load_tls_dict_list
from globaleaks.models.config import ConfigFactory
from globaleaks.orm import transact
from globaleaks.tests import helpers
from globaleaks.tests.utils import test_tls
from globaleaks.utils.sock import reserve_port_for_ip
from globaleaks.workers import supervisor
from globaleaks.workers.worker_https import HTTPSProcess


@transact
def toggle_https(session, enabled):
    ConfigFactory(session, 1, 'node').set_val(u'https_enabled', enabled)

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
def wrap_db_tx(session, f, *args, **kwargs):
    return f(session, *args, **kwargs)

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
        valid_cfg['site_cfgs'] = yield wrap_db_tx(load_tls_dict_list)

        tmp = tempfile.TemporaryFile()
        tmp.write(json.dumps(valid_cfg))
        tmp.seek(0,0)
        tmp_fd = tmp.fileno()

        self.http_process = HTTPSProcess(fd=tmp_fd)

        # Connect to service ensure that it responds with a 502
        yield threads.deferToThread(self.fetch_resource_with_fail)

        # Start the HTTP server proxy requests will be forwarded to.
        self.pp = helpers.SimpleServerPP()
        reactor.spawnProcess(self.pp, 'python', args=['python', '-m', 'SimpleHTTPServer', '43434'], usePTY=True)
        yield self.pp.start_defer

        # Check that requests are routed successfully
        yield threads.deferToThread(self.fetch_resource)

    def fetch_resource_with_fail(self):
        try:
            urllib2.urlopen('https://127.0.0.1:9443')

            self.fail('Request had to throw a 502')
        except urllib2.HTTPError as e:
            # Ensure the connection always has an HSTS header
            self.assertEqual(e.headers.get('Strict-Transport-Security'), 'max-age=31536000')
            self.assertEqual(e.code, 502)
            return

    def fetch_resource(self):
        response = urllib2.urlopen('https://127.0.0.1:9443/hello.txt')
        hdrs = response.info()
        self.assertEqual(hdrs.get('Strict-Transport-Security'), 'max-age=31536000')

        self.assertEqual(response.read(), 'Hello, world!\n')

    def tearDown(self):
        if hasattr(self, 'http_process'):
            self.http_process.shutdown()

        if hasattr(self, 'pp'):
            self.pp.transport.loseConnection()

        helpers.TestGL.tearDown(self)
