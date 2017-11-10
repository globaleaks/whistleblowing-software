# -*- coding: utf-8 -*-
from globaleaks.jobs.exit_nodes_refresh import ExitNodesRefresh
from globaleaks.state import State
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks

class TestExitNodesRefresh(helpers.TestGL):
    def setUp(self):
        State.tor_exit_set.clear()

    def tearDown(self):
        State.tor_exit_set.clear()

    @inlineCallbacks
    def test_refresh_works(self):
        # NOTE this test will fail without an internet connection
        self.assertEqual(len(State.tor_exit_set), 0)

        State.tenant_cache[1].anonymize_outgoing_connections = False

        # TODO mocking the check-status endpoint will help us detect changes
        # to the exit set structure
        yield ExitNodesRefresh().operation()

        self.assertTrue(len(State.tor_exit_set) > 700)
