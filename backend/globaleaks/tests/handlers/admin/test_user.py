# -*- coding: utf-8 -*-
import random

from twisted.internet.defer import inlineCallbacks

from globaleaks import __version__
from globaleaks.rest.errors import InvalidInputFormat
from globaleaks.tests import helpers
from globaleaks.rest import requests, errors
from globaleaks.handlers.admin import user
from globaleaks.models import User


class TestUsersCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = user.UsersCollection

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        yield handler.get()

        self.assertEqual(len(self.responses[0]), 4)

    @inlineCallbacks
    def test_post_new_admin(self):
        self.dummyAdminUser['username'] = 'beppe'

        handler = self.request(self.dummyAdminUser, role='admin')
        yield handler.post()

    @inlineCallbacks
    def test_post_new_custodian(self):
        self.dummyCustodianUser['username'] = 'beppe'

        handler = self.request(self.dummyCustodianUser, role='admin')
        yield handler.post()

    @inlineCallbacks
    def test_post_new_receiver(self):
        self.dummyReceiverUser_1['username'] = 'beppe'

        handler = self.request(self.dummyReceiverUser_1, role='admin')
        yield handler.post()


class TestUserInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = user.UserInstance

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        yield handler.get(self.dummyAdminUser['id'])
        self.assertEqual(self.responses[0]['id'], self.dummyAdminUser['id'])

    @inlineCallbacks
    def test_put_change_name(self):
        self.dummyAdminUser['name'] = u'new unique name %d' % random.randint(1, 10000)

        handler = self.request(self.dummyAdminUser, role='admin')
        yield handler.put(self.dummyAdminUser['id'])
        self.assertEqual(self.responses[0]['name'], self.dummyAdminUser['name'])

    @inlineCallbacks
    def test_put_change_valid_password(self):
        self.dummyAdminUser['name'] = u'trick to verify the update is accepted'
        self.dummyAdminUser['password'] = u'12345678antani'

        handler = self.request(self.dummyAdminUser, role='admin')
        yield handler.put(self.dummyAdminUser['id'])
        self.assertEqual(self.responses[0]['name'], self.dummyAdminUser['name'])

    @inlineCallbacks
    def test_delete_first_admin_user_should_fail(self):
        handler = self.request(role='admin')
        yield self.assertFailure(handler.delete(self.dummyAdminUser['id']),
                                 errors.UserNotDeletable)


class TestUserReset(helpers.TestHandlerWithPopulatedDB):
    _handler = user.UserInstance

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

    @inlineCallbacks
    def test_put_reinitialize(self):
        itips_desc = yield self.get_itips()
        self.assertEqual(len(itips_desc), 1)

        rtips_desc = yield self.get_rtips()
        self.assertEqual(len(rtips_desc), 2)

        self.dummyReceiverUser_1['reinitialize'] = True

        handler = self.request(self.dummyReceiverUser_1, role='admin')
        yield handler.put(self.dummyReceiverUser_1['id'])

        rtips_desc = yield self.get_rtips()
        self.assertEqual(len(rtips_desc), 1)
        self.assertEqual(rtips_desc[0]['receiver_id'], self.dummyReceiverUser_2['id'])

        self.dummyReceiverUser_2['reinitialize'] = True

        handler = self.request(self.dummyReceiverUser_2, role='admin')
        yield handler.put(self.dummyReceiverUser_2['id'])

        rtips_desc = yield self.get_rtips()
        self.assertEqual(len(rtips_desc), 0)

        itips_desc = yield self.get_itips()
        self.assertEqual(len(itips_desc), 0)


class TestUserDelete(helpers.TestHandlerWithPopulatedDB):
    _handler = user.UserInstance

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

    @inlineCallbacks
    def test_delete_receiver(self):
        itips_desc = yield self.get_itips()
        self.assertEqual(len(itips_desc), 1)

        rtips_desc = yield self.get_rtips()
        self.assertEqual(len(rtips_desc), 2)

        handler = self.request(role='admin')
        yield handler.delete(self.dummyReceiverUser_1['id'])
        yield self.assertFailure(handler.get(self.dummyReceiverUser_1['id']),
                                 errors.UserIdNotFound)

        rtips_desc = yield self.get_rtips()
        self.assertEqual(len(rtips_desc), 1)
        self.assertEqual(rtips_desc[0]['receiver_id'], self.dummyReceiverUser_2['id'])

        handler = self.request(role='admin')
        yield handler.delete(self.dummyReceiverUser_2['id'])
        yield self.assertFailure(handler.get(self.dummyReceiverUser_2['id']),
                                 errors.UserIdNotFound)

        rtips_desc = yield self.get_rtips()
        self.assertEqual(len(rtips_desc), 0)

        itips_desc = yield self.get_itips()
        self.assertEqual(len(itips_desc), 1)
