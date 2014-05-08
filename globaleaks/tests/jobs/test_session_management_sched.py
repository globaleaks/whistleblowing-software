# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

import json

from globaleaks.tests import helpers
from globaleaks.settings import GLSetting

from globaleaks.jobs import session_management_sched

class TestSessionManagementSched(helpers.TestGL):

    @inlineCallbacks
    def test_session_management_sched(self):
        yield session_management_sched.SessionManagementSchedule().operation()
