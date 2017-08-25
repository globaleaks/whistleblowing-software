# -*- coding: utf-8 -*-
import random

from globaleaks.handlers.admin import user
from globaleaks.rest import errors
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestUsersCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = user.UsersCollection

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        response = yield handler.get()

        self.assertEqual(len(response), 4)

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
    def test_put_change_name(self):
        self.dummyAdminUser['name'] = u'new unique name %d' % random.randint(1, 10000)

        handler = self.request(self.dummyAdminUser, role='admin')
        response = yield handler.put(self.dummyAdminUser['id'])
        self.assertEqual(response['name'], self.dummyAdminUser['name'])

    @inlineCallbacks
    def test_put_change_valid_password(self):
        self.dummyAdminUser['name'] = u'trick to verify the update is accepted'
        self.dummyAdminUser['password'] = u'12345678antani'

        handler = self.request(self.dummyAdminUser, role='admin')
        response = yield handler.put(self.dummyAdminUser['id'])
        self.assertEqual(response['name'], self.dummyAdminUser['name'])

    @inlineCallbacks
    def test_delete_first_admin_user_should_fail(self):
        handler = self.request(role='admin')
        yield self.assertFailure(handler.delete(self.dummyAdminUser['id']),
                                 errors.UserNotDeletable)

    @inlineCallbacks
    def test_delete_receiver(self):
        handler = self.request(role='admin')
        yield handler.delete(self.dummyReceiverUser_1['id'])
        yield self.assertFailure(handler.delete(self.dummyReceiverUser_1['id']),
                                 errors.UserIdNotFound)
