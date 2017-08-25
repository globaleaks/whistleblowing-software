from globaleaks.jobs.exit_nodes_refresh_sched import ExitNodesRefreshSchedule
from globaleaks.settings import GLSettings
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks

class TestExitNodesRefresh(helpers.TestGL):
    def setUp(self):
        GLSettings.appstate.tor_exit_set.clear()

    def tearDown(self):
        GLSettings.appstate.tor_exit_set.clear()

    @inlineCallbacks
    def test_refresh_works(self):
        # NOTE this test will fail without an internet connection
        self.assertEqual(len(GLSettings.appstate.tor_exit_set), 0)

        GLSettings.memory_copy.anonymize_outgoing_connections = False

        # TODO mocking the check-status endpoint will help us detect changes 
        # to the exit set structure
        yield ExitNodesRefreshSchedule().operation()

        self.assertTrue(len(GLSettings.appstate.tor_exit_set) > 700)
