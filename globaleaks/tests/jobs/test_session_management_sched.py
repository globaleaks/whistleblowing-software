# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from cyclone.util import ObjectDict as OD

from globaleaks.tests import helpers
from globaleaks.settings import GLSetting
from globaleaks.utils.utility import datetime_null

from globaleaks.jobs import session_management_sched

class TestSessionManagementSched(helpers.TestGL):

    @inlineCallbacks
    def test_session_management_sched(self):

        new_session = OD(
               refreshdate=datetime_null(), # new but expired session!
               id="admin",
               role="admin",
               user_id="admin"
        )

        GLSetting.sessions['111'] = new_session
        GLSetting.sessions['222'] = new_session
        GLSetting.sessions['333'] = new_session

        yield session_management_sched.SessionManagementSchedule().operation()

        self.assertEqual(len(GLSetting.sessions), 0)
