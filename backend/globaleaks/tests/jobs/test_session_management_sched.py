# -*- coding: utf-8 -*-
from globaleaks.handlers.base import GLSessions, new_session
from globaleaks.jobs import session_management_sched
from globaleaks.settings import Settings
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestSessionManagementSched(helpers.TestGL):
    @inlineCallbacks
    def test_session_management_sched(self):
        new_session('admin', 'admin', 'enabled')  # 1!
        new_session('admin', 'admin', 'enabled')  # 2!
        new_session('admin', 'admin', 'enabled')  # 3!

        self.assertEqual(len(GLSessions), 3)

        self.test_reactor.pump([1] * (Settings.authentication_lifetime - 1))

        self.assertEqual(len(GLSessions), 3)

        self.test_reactor.advance(1)

        self.assertEqual(len(GLSessions), 0)

        yield session_management_sched.SessionManagementSchedule().run()
