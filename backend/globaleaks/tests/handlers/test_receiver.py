# -*- coding: utf-8 -*-
import unittest
import random
from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers
from globaleaks.handlers import receiver, admin
from globaleaks.rest import errors


class TestReceiverInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = receiver.ReceiverInstance

    @inlineCallbacks
    def test_get(self):
        rcvr = (yield admin.receiver.get_receiver_list('en'))[0]
        # respondes should be resetted in order to have index 0
        # be the current receiver in the loop
        self.responses = []

        handler = self.request(user_id = rcvr['id'], role='receiver')

        yield handler.get()

    @inlineCallbacks
    def test_put_data_obtained_with_get(self):
        rcvr = (yield admin.receiver.get_receiver_list('en'))[0]
        # respondes should be resetted in order to have index 0
        # be the current receiver in the loop
        self.responses = []

        handler = self.request(user_id = rcvr['id'], role='receiver')

        yield handler.get()

        handler = self.request(self.responses[0], user_id = rcvr['id'], role='receiver')
        yield handler.put()

    @inlineCallbacks
    def test_put_with_remove_pgp_flag_true(self):
        rcvr = (yield admin.receiver.get_receiver_list('en'))[0]
        # respondes should be resetted in order to have index 0
        # be the current receiver in the loop
        self.responses = []

        handler = self.request(user_id = rcvr['id'], role='receiver')

        yield handler.get()

        self.responses[0]['pgp_key_remove'] = True

        handler = self.request(self.responses[0], user_id = rcvr['id'], role='receiver')
        yield handler.put()

    @inlineCallbacks
    def test_ping_mail_change(self):
        rcvr = (yield admin.receiver.get_receiver_list('en'))[0]
        # respondes should be resetted in order to have index 0
        # be the current receiver in the loop
        self.responses = []

        handler = self.request(user_id = rcvr['id'], role='receiver')

        yield handler.get()

        self.responses[0]['ping_mail_address'] = 'ortomio@x.com'

        handler = self.request(self.responses[0], user_id = rcvr['id'], role='receiver')
        yield handler.put()

    @inlineCallbacks
    def test_handler_update_key(self):
        rcvr = (yield admin.receiver.get_receiver_list('en'))[0]
        # respondes should be resetted in order to have index 0
        # be the current receiver in the loop
        self.responses = []

        handler = self.request(user_id = rcvr['id'], role='receiver')

        yield handler.get()

        # check key is initialized at start
        self.assertEqual(self.responses[0]['pgp_key_status'], u'disabled')
        self.assertIsNone(self.responses[0]['pgp_key_fingerprint'])
        self.assertIsNone(self.responses[0]['pgp_key_public'])
        self.assertIsNone(self.responses[0]['pgp_key_info'])
        self.assertEqual(self.responses[0]['pgp_key_expiration'], '1970-01-01T00:00:00Z')

        self.responses[0]['pgp_key_public'] = unicode(helpers.VALID_PGP_KEY1)
        self.responses[0]['pgp_key_status'] = u'disabled' # Test, this field is ignored and set
        self.responses[0]['pgp_key_remove'] = False
        handler = self.request(self.responses[0], user_id=rcvr['id'], role='receiver')
        yield handler.put() # key update 1

        # check update 1
        self.assertEqual(self.responses[1]['pgp_key_fingerprint'],
            u'CF4A22020873A76D1DCB68D32B25551568E49345')
        self.assertEqual(self.responses[1]['pgp_key_status'], u'enabled')

        self.responses[1]['pgp_key_public'] = unicode(helpers.VALID_PGP_KEY2)
        self.responses[1]['pgp_key_remove'] = False
        handler = self.request(self.responses[1], user_id=rcvr['id'], role='receiver')
        yield handler.put() # key update 2

        # check update 2
        self.assertEqual(self.responses[2]['pgp_key_fingerprint'], u'7106D296DA80BCF21A3D93056097CE44FED083C9')

        self.responses[2]['pgp_key_remove'] = True
        handler = self.request(self.responses[2], user_id=rcvr['id'], role='receiver')
        yield handler.put() # removal

        # check removal
        self.assertEqual(self.responses[3]['pgp_key_status'], u'disabled')
        self.assertIsNone(self.responses[3]['pgp_key_fingerprint'])
        self.assertIsNone(self.responses[3]['pgp_key_public'])
        self.assertIsNone(self.responses[3]['pgp_key_info'])
        self.assertEqual(self.responses[3]['pgp_key_expiration'], '1970-01-01T00:00:00Z')


    @inlineCallbacks
    def test_load_malformed_key(self):
        rcvr = (yield admin.receiver.get_receiver_list('en'))[0]
        # respondes should be resetted in order to have index 0
        # be the current receiver in the loop
        self.responses = []

        handler = self.request(user_id = rcvr['id'], role='receiver')

        yield handler.get()

        self.responses[0]['pgp_key_public'] = unicode(helpers.VALID_PGP_KEY1).replace('A', 'B')
        self.responses[0]['pgp_key_status'] = u'disabled' # Test, this field is ignored and set
        self.responses[0]['pgp_key_remove'] = False
        handler = self.request(self.responses[0], user_id=rcvr['id'], role='receiver')
        yield self.assertFailure(handler.put(), errors.PGPKeyInvalid)


class TestTipsCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = receiver.TipsCollection

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

    @inlineCallbacks
    def test_get(self):
        handler = self.request(user_id=self.dummyReceiver_1['id'], role='receiver')
        yield handler.get()

    @inlineCallbacks
    def test_serialisation_receivertiplist(self):
        handler = self.request(user_id = self.dummyReceiver_1['id'], role='receiver')

        yield handler.get()

        expected_keys = ['creation_date', 'context_name', 'id', 'file_counter', 'questionnaire_hash', 'preview_schema', 'expiration_date', 'message_counter', 'access_counter', 'label', 'tor2web', 'comment_counter', 'last_access', 'preview']
        for receivertiplist_key in self.responses[0][0].keys():
            self.assertTrue(receivertiplist_key in expected_keys, "Missing %s key")
            expected_keys.remove(receivertiplist_key)

        self.assertTrue(len(expected_keys) == 0, "A key(s) has been removed from handler: %s" % expected_keys)

class TestTipsOperations(helpers.TestHandlerWithPopulatedDB):
    _handler = receiver.TipsOperations

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

    @inlineCallbacks
    def test_put_postpone(self):
        for _ in xrange(3):
            yield self.perform_full_submission_actions()

        rtips = yield receiver.get_receivertip_list(self.dummyReceiver_1['id'], 'en')
        rtips_ids = [rtip['id'] for rtip in rtips]

        postpone_map = {}
        for rtip in rtips:
            postpone_map[rtip['id']] = rtip['expiration_date']

        data_request = {
            'operation': 'postpone',
            'rtips': rtips_ids
        }

        handler = self.request(data_request, user_id = self.dummyReceiver_1['id'], role='receiver')
        yield handler.put()

        rtips = yield receiver.get_receivertip_list(self.dummyReceiver_1['id'], 'en')

        for rtip in rtips:
            self.assertNotEqual(postpone_map[rtip['id']], rtip['expiration_date'])

    @inlineCallbacks
    def test_put_delete(self):
        for _ in xrange(3):
            yield self.perform_full_submission_actions()

        handler = self.request(user_id = self.dummyReceiver_1['id'], role='receiver')

        rtips = yield receiver.get_receivertip_list(self.dummyReceiver_1['id'], 'en')
        rtips_ids = [rtip['id'] for rtip in rtips]

        data_request = {
            'operation': 'delete',
            'rtips': rtips_ids
        }

        handler = self.request(data_request, user_id = self.dummyReceiver_1['id'], role='receiver')
        yield handler.put()

        rtips = yield receiver.get_receivertip_list(self.dummyReceiver_1['id'], 'en')

        self.assertEqual(len(rtips), 0)

