# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers
from globaleaks.handlers import receiver, admin


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


class TestTipsOperations(helpers.TestGLWithPopulatedDB):
    _handler = receiver.TipsOperations

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

    @inlineCallbacks
    def test_put_postpone(self):
        handler = self.request(role='receiver')
        handler.current_user.user_id = self.dummyReceiver_1['id']

        # hack - take the receiver tip map
        a, b = yield receiver.get_receivertip_list()
        print a
        print b
        import pdb; pdb.set_trace()

        yield handler.put({
            'operation': 'postpone',
            'rtips': []
        })

    @inlineCallbacks
    def test_put_delete(self):
        handler = self.request(role='receiver')
        handler.current_user.user_id = self.dummyReceiver_1['id']
        yield handler.put({
            'operation': 'delete',
            'rtips': []
        })

