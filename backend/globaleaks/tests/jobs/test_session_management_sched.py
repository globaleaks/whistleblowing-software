# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers
from globaleaks.settings import GLSettings

from globaleaks.handlers.base import GLSession, GLSessions
from globaleaks.jobs import session_management_sched


class TestSessionManagementSched(helpers.TestGL):
    @inlineCallbacks
    def test_session_management_sched(self):
        GLSession('admin', 'admin', 'enabled')  # 1!
        GLSession('admin', 'admin', 'enabled')  # 2!
        GLSession('admin', 'admin', 'enabled')  # 3!

        self.assertEqual(len(GLSessions), 3)

        self.test_reactor.pump([1] * (GLSettings.authentication_lifetime - 1))

        self.assertEqual(len(GLSessions), 3)

        self.test_reactor.advance(1)

        self.assertEqual(len(GLSessions), 0)

        yield session_management_sched.SessionManagementSchedule().operation()
