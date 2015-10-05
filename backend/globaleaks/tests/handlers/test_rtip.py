# -*- coding: utf-8 -*-
import json

from twisted.internet.defer import inlineCallbacks
from globaleaks.rest import errors
from globaleaks.tests import helpers
from globaleaks.handlers import rtip


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

            handler = self.request(role='receiver', user_id = rtip_desc['receiver_id'])
            yield handler.get(rtip_desc['rtip_id'])
            self.assertEqual(handler.get_status(), 200)

            self.responses[0]['operation'] = 'postpone'

            handler = self.request(self.responses[0], role='receiver', user_id = rtip_desc['receiver_id'])
            yield handler.put(rtip_desc['rtip_id'])
            self.assertEqual(handler.get_status(), 202)


    @inlineCallbacks
    def test_put_label(self):
        rtips_desc = yield self.get_rtips()
        for i, rtip_desc in enumerate(rtips_desc):
            self.responses = []

            handler = self.request(role='receiver', user_id = rtip_desc['receiver_id'])
            yield handler.get(rtip_desc['rtip_id'])
            self.assertEqual(handler.get_status(), 200)

            self.responses[0]['operation'] = 'label'
            assigned_label = 'ArandomLABEL %d' % i
            self.responses[0]['label'] = assigned_label

            handler = self.request(self.responses[0], role='receiver', user_id = rtip_desc['receiver_id'])
            yield handler.put(rtip_desc['rtip_id'])

            self.assertEqual(handler.get_status(), 202)
            yield handler.get(rtip_desc['rtip_id'])
            self.assertEqual(self.responses[1]['label'], assigned_label)


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
