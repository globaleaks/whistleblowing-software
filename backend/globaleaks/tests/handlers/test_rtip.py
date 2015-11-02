# -*- coding: utf-8 -*-
import json

from twisted.internet.defer import inlineCallbacks
from globaleaks.rest import errors
from globaleaks.tests import helpers
from globaleaks.handlers import rtip
from globaleaks.settings import GLSettings


class TestRTipInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = rtip.RTipInstance

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

    @inlineCallbacks
    def test_get(self):
        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver', user_id = rtip_desc['receiver_id'])

            yield handler.get(rtip_desc['rtip_id'])

    @inlineCallbacks
    def test_put_postpone(self):
        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            self.responses = []

            operation = {
              'operation': 'postpone',
              'args': {}
            }

            handler = self.request(operation, role='receiver', user_id = rtip_desc['receiver_id'])
            yield handler.put(rtip_desc['rtip_id'])
            self.assertEqual(handler.get_status(), 202)

            handler = self.request(role='receiver', user_id = rtip_desc['receiver_id'])
            yield handler.get(rtip_desc['rtip_id'])
            self.assertEqual(handler.get_status(), 200)



    @inlineCallbacks
    def switch_enabler(self, key):
        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            self.responses = []

            operation = {
                'operation': 'set',
                'args': {
                  'key': key,
                  'value': True
                }
            }

            handler = self.request(operation, role='receiver', user_id = rtip_desc['receiver_id'])
            yield handler.put(rtip_desc['rtip_id'])
            self.assertEqual(handler.get_status(), 202)

            yield handler.get(rtip_desc['rtip_id'])
            self.assertEqual(self.responses[0][key], True)

            operation = {
                'operation': 'set',
                'args': {
                  'key': key,
                  'value': False
                }
            }

            handler = self.request(operation, role='receiver', user_id = rtip_desc['receiver_id'])
            yield handler.put(rtip_desc['rtip_id'])
            self.assertEqual(handler.get_status(), 202)

            yield handler.get(rtip_desc['rtip_id'])
            self.assertEqual(self.responses[1][key], False)

            operation = {
                'operation': 'set',
                'args': {
                  'key': key,
                  'value': True
                }
            }

            handler = self.request(operation, role='receiver', user_id = rtip_desc['receiver_id'])
            yield handler.put(rtip_desc['rtip_id'])
            self.assertEqual(handler.get_status(), 202)

            yield handler.get(rtip_desc['rtip_id'])
            self.assertEqual(self.responses[2][key], True)

    @inlineCallbacks
    def test_put_enable_two_way_comments(self):
        GLSettings.memory_copy.can_grant_permissions = True
        yield self.switch_enabler('enable_two_way_comments')

    @inlineCallbacks
    def test_put_enable_two_way_messages(self):
        GLSettings.memory_copy.can_grant_permissions = True
        yield self.switch_enabler('enable_two_way_messages')

    @inlineCallbacks
    def test_put_enable_attachments(self):
        GLSettings.memory_copy.can_grant_permissions = True
        yield self.switch_enabler('enable_attachments')


    @inlineCallbacks
    def test_put_label(self):
        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            self.responses = []

            operation = {
              'operation': 'set',
              'args': {
                'key': 'label',
                'value': 'PASSANTEDIPROFESSIONE'
              }
            }

            handler = self.request(operation, role='receiver', user_id = rtip_desc['receiver_id'])
            yield handler.put(rtip_desc['rtip_id'])
            self.assertEqual(handler.get_status(), 202)

            yield handler.get(rtip_desc['rtip_id'])
            self.assertEqual(self.responses[0]['label'], operation['args']['value'])


    @inlineCallbacks
    def test_delete_delete(self):
        rtips_desc = yield self.get_rtips()
        self.assertEqual(len(rtips_desc), 2)

        # we deleete the first and then we verify that the second does not exist anymore
        handler = self.request(role='receiver', user_id = rtips_desc[0]['receiver_id'])
        yield handler.delete(rtips_desc[0]['rtip_id'])

        rtips_desc = yield self.get_rtips()

        self.assertEqual(len(rtips_desc), 0)

    @inlineCallbacks
    def test_delete_unexistent_tip_by_existent_and_logged_receiver(self):
        rtips_desc = yield self.get_rtips()

        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver', user_id = rtip_desc['receiver_id'])

            self.assertFailure(handler.delete("unexistent_tip"), errors.TipIdNotFound)

    @inlineCallbacks
    def test_delete_existent_tip_by_existent_and_logged_but_wrong_receiver(self):
        rtips_desc = yield self.get_rtips()

        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver', user_id = rtip_desc['receiver_id'])

            self.assertFailure(handler.delete("unexistent_tip"), errors.TipIdNotFound)


class TestRTipCommentCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = rtip.RTipCommentCollection

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

    @inlineCallbacks
    def test_get(self):
        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver', user_id = rtip_desc['receiver_id'])

            yield handler.get(rtip_desc['rtip_id'])

    @inlineCallbacks
    def test_post(self):
        body = {
            'content': "can you provide an evidence of what you are telling?",
        }

        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver', user_id = rtip_desc['receiver_id'], body=json.dumps(body))

            yield handler.post(rtip_desc['rtip_id'])


class TestReceiverMsgCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = rtip.ReceiverMsgCollection

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

    @inlineCallbacks
    def test_get(self):
        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver', user_id = rtip_desc['receiver_id'])

            yield handler.get(rtip_desc['rtip_id'])

    @inlineCallbacks
    def test_post(self):
        body = {
            'content': "can you provide an evidence of what you are telling?",
        }

        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver', user_id = rtip_desc['receiver_id'], body=json.dumps(body))

            yield handler.post(rtip_desc['rtip_id'])


class TestRTipReceiversCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = rtip.RTipReceiversCollection

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

    @inlineCallbacks
    def test_get(self):
        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver', user_id = rtip_desc['receiver_id'])

            yield handler.get(rtip_desc['rtip_id'])


class TestIdentityAccessRequestsCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = rtip.IdentityAccessRequestsCollection

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

    @inlineCallbacks
    def test_get(self):
        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver', user_id = rtip_desc['receiver_id'])

            yield handler.get(rtip_desc['rtip_id'])

    @inlineCallbacks
    def test_post(self):
        body = {
            'request_motivation': ''
        }

        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver', user_id = rtip_desc['receiver_id'], body=json.dumps(body))

            yield handler.post(rtip_desc['rtip_id'])
