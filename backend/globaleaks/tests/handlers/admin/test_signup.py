# -*- coding: utf-8 -*-
import copy
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers import signup
from globaleaks.handlers.admin import signup as admin_signup
from globaleaks.models import config
from globaleaks.orm import transact
from globaleaks.rest import errors
from globaleaks.tests import helpers


@transact
def enable_signup(session):
    config.ConfigFactory(session, 1, 'node').set_val(u'enable_signup', True)


class TestAdminSignup(helpers.TestHandler):
    _handler = signup.Signup

    @inlineCallbacks
    def test_get(self):
        yield enable_signup()

        for i in range(3):
            self._handler = signup.Signup
            dummySignup = copy.deepcopy(self.dummySignup)
            dummySignup['subdomain'] = 'xxx' + str(i)
            handler = self.request(dummySignup)
            yield handler.post()

            self._handler = admin_signup.SignupList
            handler = self.request(role='admin')
            r = yield handler.get()
            self.assertTrue(len(r) == i + 1)

