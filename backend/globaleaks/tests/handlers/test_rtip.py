# -*- coding: utf-8 -*-
import json

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers import rtip
from globaleaks.jobs.delivery_sched import DeliverySchedule
from globaleaks.rest import errors
from globaleaks.settings import GLSettings
from globaleaks.tests import helpers
from globaleaks.utils.utility import datetime_now, ISO8601_to_datetime


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
            yield handler.get(rtip_desc['id'])

    @inlineCallbacks
    def test_put_postpone(self):
        now = datetime_now()

        yield self.force_itip_expiration()

        rtips_desc = yield self.get_rtips()

        for rtip_desc in rtips_desc:
            self.assertTrue(rtip_desc['expiration_date'] == '1970-01-01T00:00:00Z')
            operation = {
              'operation': 'postpone',
              'args': {}
            }

            handler = self.request(operation, role='receiver', user_id = rtip_desc['receiver_id'])
            yield handler.put(rtip_desc['id'])
            self.assertEqual(handler.request.code, 200)

        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtip_descs:
            self.assertTrue(ISO8601_to_datetime(rtip_desc['expiration_date']) >= now)

    @inlineCallbacks
    def test_put_postpone_never(self):
        now = datetime_now()

        yield self.force_itip_expiration()

        yield self.set_contexts_timetolive(-1)

        rtips_desc = yield self.get_rtips()

        for rtip_desc in rtips_desc:
            self.assertTrue(rtip_desc['expiration_date'] == '1970-01-01T00:00:00Z')
            operation = {
              'operation': 'postpone',
              'args': {}
            }

            handler = self.request(operation, role='receiver', user_id = rtip_desc['receiver_id'])
            yield handler.put(rtip_desc['id'])
            self.assertEqual(handler.request.code, 200)

        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtip_descs:
            self.assertTrue(rtip_desc['expiration_date'] == '3000-01-01T00:00:00Z')


    @inlineCallbacks
    def switch_enabler(self, key):
        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            operation = {
                'operation': 'set',
                'args': {
                  'key': key,
                  'value': True
                }
            }

            handler = self.request(operation, role='receiver', user_id = rtip_desc['receiver_id'])
            yield handler.put(rtip_desc['id'])
            self.assertEqual(handler.request.code, 200)

            response = yield handler.get(rtip_desc['id'])
            self.assertEqual(response[key], True)

            operation = {
                'operation': 'set',
                'args': {
                  'key': key,
                  'value': False
                }
            }

            handler = self.request(operation, role='receiver', user_id = rtip_desc['receiver_id'])
            yield handler.put(rtip_desc['id'])
            self.assertEqual(handler.request.code, 200)

            response = yield handler.get(rtip_desc['id'])
            self.assertEqual(response[key], False)

            operation = {
                'operation': 'set',
                'args': {
                  'key': key,
                  'value': True
                }
            }

            handler = self.request(operation, role='receiver', user_id = rtip_desc['receiver_id'])
            yield handler.put(rtip_desc['id'])
            self.assertEqual(handler.request.code, 200)

            response = yield handler.get(rtip_desc['id'])
            self.assertEqual(response[key], True)

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
            operation = {
              'operation': 'set',
              'args': {
                'key': 'label',
                'value': 'PASSANTEDIPROFESSIONE'
              }
            }

            handler = self.request(operation, role='receiver', user_id = rtip_desc['receiver_id'])
            yield handler.put(rtip_desc['id'])
            self.assertEqual(handler.request.code, 200)

            response = yield handler.get(rtip_desc['id'])
            self.assertEqual(response['label'], operation['args']['value'])

    @inlineCallbacks
    def test_put_silence_notify(self):
        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:

            operation = {
              'operation': 'set',
              'args': {
                'key': 'enable_notifications',
                'value': False
              }
            }

            handler = self.request(operation, role='receiver', user_id = rtip_desc['receiver_id'])
            yield handler.put(rtip_desc['id'])
            self.assertEqual(handler.request.code, 200)

            response = yield handler.get(rtip_desc['id'])
            self.assertEqual(response['enable_notifications'], operation['args']['value'])

    @inlineCallbacks
    def test_delete(self):
        rtips_desc = yield self.get_rtips()
        self.assertEqual(len(rtips_desc), self.population_of_submissions * self.population_of_recipients)

        # we delete the first and then we verify that the second does not exist anymore
        handler = self.request(role='receiver', user_id = rtips_desc[0]['receiver_id'])
        yield handler.delete(rtips_desc[0]['id'])

        rtips_desc = yield self.get_rtips()

        self.assertEqual(len(rtips_desc), self.population_of_submissions * self.population_of_recipients - self.population_of_recipients)

        yield self.test_model_count(models.SecureFileDelete, self.population_of_attachments)


    @inlineCallbacks
    def test_delete_unexistent_tip_by_existent_and_logged_receiver(self):
        rtips_desc = yield self.get_rtips()

        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver', user_id = rtip_desc['receiver_id'])
            yield self.assertFailure(handler.delete("unexistent_tip"), errors.TipIdNotFound)

    @inlineCallbacks
    def test_delete_existent_tip_by_existent_and_logged_but_wrong_receiver(self):
        rtips_desc = yield self.get_rtips()

        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver', user_id = rtip_desc['receiver_id'])
            yield self.assertFailure(handler.delete("unexistent_tip"), errors.TipIdNotFound)


class TestRTipCommentCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = rtip.RTipCommentCollection

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

    @inlineCallbacks
    def test_post(self):
        body = {
            'content': "can you provide an evidence of what you are telling?",
        }

        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver', user_id = rtip_desc['receiver_id'], body=json.dumps(body))
            yield handler.post(rtip_desc['id'])


class TestReceiverMsgCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = rtip.ReceiverMsgCollection

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

    @inlineCallbacks
    def test_post(self):
        body = {
            'content': "can you provide an evidence of what you are telling?",
        }

        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver', user_id = rtip_desc['receiver_id'], body=json.dumps(body))
            yield handler.post(rtip_desc['id'])


class TestReceiverFileDownload(helpers.TestHandlerWithPopulatedDB):
    _handler = rtip.ReceiverFileDownload

    @inlineCallbacks
    def test_get(self):
        yield self.perform_minimal_submission()
        yield DeliverySchedule().run()

        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            rfiles_desc = yield self.get_rfiles(rtip_desc['id'])
            for rfile_desc in rfiles_desc:
                handler = self.request(role='receiver', user_id = rtip_desc['receiver_id'])
                yield handler.get(rfile_desc['id'])
                self.assertNotEqual(handler.request.getResponseBody(), '')


class TestIdentityAccessRequestsCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = rtip.IdentityAccessRequestsCollection

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_minimal_submission()

    @inlineCallbacks
    def test_post(self):
        body = {
            'request_motivation': ''
        }

        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver', user_id = rtip_desc['receiver_id'], body=json.dumps(body))
            yield handler.post(rtip_desc['id'])
