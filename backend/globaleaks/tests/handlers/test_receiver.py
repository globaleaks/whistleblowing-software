# -*- coding: utf-8 -*-
import unittest
import random
from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers
from globaleaks.handlers import receiver, admin
from globaleaks.rest.errors import InvalidInputFormat


class TestReceiverInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = receiver.ReceiverInstance

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='receiver')

        rcvrs = yield admin.get_receiver_list('en')
        for rcvr in rcvrs:
            handler = self.request(role='receiver')
            handler.current_user.user_id = rcvr['id']

            yield handler.get()

    @inlineCallbacks
    def test_put_data_obtained_with_get(self):
        handler = self.request(role='receiver')

        rcvrs = yield admin.get_receiver_list('en')
        for rcvr in rcvrs:
            handler = self.request(role='receiver')
            handler.current_user.user_id = rcvr['id']

            yield handler.get()

            handler = self.request(self.responses[0], role='receiver')
            handler.current_user.user_id = rcvr['id']
            yield handler.put()

    @inlineCallbacks
    def test_put_with_remove_pgp_flag_true(self):
        handler = self.request(role='receiver')

        rcvrs = yield admin.get_receiver_list('en')
        for rcvr in rcvrs:
            handler = self.request(role='receiver')
            handler.current_user.user_id = rcvr['id']

            yield handler.get()

            self.responses[0]['pgp_key_remove'] = True

            handler = self.request(self.responses[0], role='receiver')
            handler.current_user.user_id = rcvr['id']
            yield handler.put()

    @inlineCallbacks
    def test_ping_mail_change(self):
        handler = self.request(role='receiver')

        rcvrs = yield admin.get_receiver_list('en')
        for rcvr in rcvrs:
            handler = self.request(role='receiver')
            handler.current_user.user_id = rcvr['id']

            yield handler.get()

            self.responses[0]['ping_mail_address'] = 'ortomio@x.com'

            handler = self.request(self.responses[0], role='receiver')
            handler.current_user.user_id = rcvr['id']
            yield handler.put()

class TestTipsCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = receiver.TipsCollection

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='receiver')
        handler.current_user.user_id = self.dummyReceiver_1['id']
        yield handler.get()


class TestTipsOperations(helpers.TestHandlerWithPopulatedDB):
    _handler = receiver.TipsOperations

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

    @inlineCallbacks
    def test_get(self):

        for _ in xrange(random.randint(3,5)):
            yield self.perform_full_submission_actions()

        handler = self.request(role='receiver')
        handler.current_user.user_id = self.dummyReceiver_1['id']

        yield handler.get()

        self.assertTrue(isinstance(self.responses[0], dict))
        self.assertTrue(len(self.responses[0].keys()) > 3)


    @inlineCallbacks
    # @unittest.skip("No idea how check success")
    def test_put_postpone(self):

        for _ in xrange(random.randint(3,5)):
            yield self.perform_full_submission_actions()

        handler = self.request(role='receiver')
        handler.current_user.user_id = self.dummyReceiver_1['id']

        yield handler.get()
        self.assertTrue(isinstance(self.responses[0], dict))
        self.assertTrue(len(self.responses[0].keys()) > 3)

        data_request = {
            'operation': 'postpone',
            'rtips': self.responses[0].keys()
        }
        import pprint
        pprint.pprint(data_request)

        handler = self.request(data_request, role='receiver')
        yield handler.put()
        # How can be checked that actually works ? 



    @inlineCallbacks
    def test_put_delete(self):

        for _ in xrange(random.randint(3,5)):
            yield self.perform_full_submission_actions()

        handler = self.request(role='receiver')
        handler.current_user.user_id = self.dummyReceiver_1['id']

        yield handler.get()

        import pprint
        pprint.pprint(self.responses)
        pprint.pprint(self.responses[0].keys())

        yield handler.get()
        import pprint
        pprint.pprint(self.responses)
        pprint.pprint(self.responses[0].keys())

        data_request = {
            'operation': 'delete',
            'rtips': self.responses[0].keys()
        }
        handler = self.request(data_request, role='receiver')
        yield handler.put()


    @inlineCallbacks
    def test_put_empty_rtips(self):
        handler = self.request(role='receiver')
        handler.current_user.user_id = self.dummyReceiver_1['id']

        data_request = {
            'operation': 'delete',
            'rtips': []
        }
        handler = self.request(data_request, role='receiver')
        yield self.assertFailure(handler.put(), InvalidInputFormat)


