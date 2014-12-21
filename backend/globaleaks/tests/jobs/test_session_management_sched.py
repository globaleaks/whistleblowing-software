# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from cyclone.util import ObjectDict as OD
from twisted.internet import task

from globaleaks.tests import helpers
from globaleaks.settings import GLSetting
from globaleaks.utils.tempobj import TempObj
from globaleaks.utils.utility import datetime_null

from globaleaks.handlers import authentication
from globaleaks.jobs import session_management_sched

class TestSessionManagementSched(helpers.TestGL):

    @inlineCallbacks
    def test_session_management_sched(self):

        authentication.GLSession('admin', 'admin', 'enabled') # 1!
        authentication.GLSession('admin', 'admin', 'enabled') # 2!
        authentication.GLSession('admin', 'admin', 'enabled') # 3!

        self.assertEqual(len(GLSetting.sessions), 3)
        authentication.reactor.advance(GLSetting.defaults.lifetimes['admin'])
        self.assertEqual(len(GLSetting.sessions), 0)

        yield session_management_sched.SessionManagementSchedule().operation()
