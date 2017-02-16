from twisted.internet.defer import inlineCallbacks

from globaleaks.models.config import PrivateFactory
from globaleaks.utils.sock import reserve_port_for_ifaces
from globaleaks.orm import transact
from globaleaks.workers import supervisor

from globaleaks.tests import helpers
from globaleaks.tests.utils import test_tls

@transact
def toggle_https(store, enabled):
    PrivateFactory(store).set_val('https_enabled', enabled)

class TestProcessSupervisor(helpers.TestHandler):

    @inlineCallbacks
    def setUp(self):
        helpers.TestHandler.setUp(self)
        yield test_tls.commit_valid_config()

    @inlineCallbacks
    def test_init_with_no_launch(self):
        yield toggle_https(enabled=False)
        socks, fails = reserve_port_for_ifaces(['127.0.0.1'], 43434)
        self.assertEquals(len(fails), 0)

        ip, port = '127.0.0.1', 43435

        p_s = supervisor.ProcessSupervisor(socks, ip, port)
        yield p_s.maybe_launch_https_workers()

        self.assertFalse(p_s.is_running())

        yield p_s.shutdown()

        self.assertFalse(p_s.shutting_down)
        self.assertFalse(p_s.is_running())


    @inlineCallbacks
    def test_init_with_launch(self):
        yield toggle_https(enabled=True)
        socks, fails = reserve_port_for_ifaces(['localhost'], 43434)
        self.assertEquals(len(fails), 0)

        ip, port = '127.0.0.1', 43435

        p_s = supervisor.ProcessSupervisor(socks, ip, port)
        yield p_s.maybe_launch_https_workers()

        self.assertTrue(p_s.is_running())

        yield p_s.shutdown()

        self.assertFalse(p_s.shutting_down)
        self.assertFalse(p_s.is_running())


    def mtest_death(self):
        pass


class TestSubprocessRun(helpers.TestHandler):
    pass

