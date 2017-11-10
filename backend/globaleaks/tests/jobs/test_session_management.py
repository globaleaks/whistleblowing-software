# -*- coding: utf-8 -*-
from globaleaks.handlers.base import Sessions, new_session
from globaleaks.jobs import session_management
from globaleaks.settings import Settings
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestSessionManagement(helpers.TestGL):
    @inlineCallbacks
    def test_session_management(self):
        new_session(1, 'admin', 'admin', 'enabled')  # 1!
        new_session(1, 'admin', 'admin', 'enabled')  # 2!
        new_session(1, 'admin', 'admin', 'enabled')  # 3!

        self.assertEqual(len(Sessions), 3)

        self.test_reactor.pump([1] * (Settings.authentication_lifetime - 1))

        self.assertEqual(len(Sessions), 3)

        self.test_reactor.advance(1)

        self.assertEqual(len(Sessions), 0)

        yield session_management.SessionManagement().run()
