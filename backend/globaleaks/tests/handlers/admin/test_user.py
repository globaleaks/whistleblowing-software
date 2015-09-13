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

        self.assertEqual(len(self.responses[0]), 5)


class TestUserCreate(helpers.TestHandlerWithPopulatedDB):
    _handler = user.UserCreate

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
    def test_put_change_invalid_password(self):
        self.dummyAdminUser['name'] = u'trick to verify the update is accepted'
        self.dummyAdminUser['password'] = u'toosimplepassword'

        handler = self.request(self.dummyAdminUser, role='admin')
        yield self.assertFailure(handler.put(self.dummyAdminUser['id']), InvalidInputFormat)

    @inlineCallbacks
    def test_delete(self):
        handler = self.request(self.dummyAdminUser, role='admin')
        yield handler.delete(self.dummyAdminUser['id'])
        yield self.assertFailure(handler.get(self.dummyAdminUser['id']),
                                 errors.UserIdNotFound)
