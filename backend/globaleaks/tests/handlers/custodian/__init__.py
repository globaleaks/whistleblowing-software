# -*- coding: utf-8 -*-
from globaleaks.handlers import custodian, rtip
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestIdentityAccessRequestInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = custodian.IdentityAccessRequestInstance

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

        dummyRTips = yield self.get_rtips()
        self.iars = []

        for rtip_desc in dummyRTips:
            iar = yield rtip.create_identityaccessrequest(1,
                                                       rtip_desc['receiver_id'],
                                                       rtip_desc['id'],
                                                       {'request_motivation': 'request motivation'})
            self.iars.append(iar['id'])

    @inlineCallbacks
    def test_put_identityaccessrequest_response(self):
        reply = {
          'reply':  'authorized',
          'reply_motivation': 'oh yeah!'
        }

        handler = self.request(reply, user_id=self.dummyCustodian['id'], role='custodian')

        yield handler.put(self.iars[0])


class TestIdentityAccessRequestsCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = custodian.IdentityAccessRequestsCollection

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

    def test_get(self):
        handler = self.request(user_id=self.dummyCustodian['id'], role='custodian')
        return handler.get()
