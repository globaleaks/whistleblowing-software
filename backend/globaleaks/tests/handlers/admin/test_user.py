# -*- coding: utf-8 -*-
from globaleaks.db import refresh_memory_variables

from globaleaks.handlers.admin import receiver
from globaleaks.handlers.admin import user
from globaleaks.handlers.admin import tenant

from globaleaks.models import User
from globaleaks.tests import helpers
from globaleaks.tests.handlers.admin.test_tenant import get_dummy_tenant_desc
from twisted.internet.defer import inlineCallbacks

class TestAdminCollection(helpers.TestCollectionHandler):
    _handler = user.UsersCollection
    _test_desc = {
      'model': User,
      'create': user.create,
      'data': {
          'role': 'admin',
          'name': u'Mario Rossi',
          'mail_address': 'admin@theguardian.com',
          'language': 'en'
      }
    }

    def get_dummy_request(self):
        data = helpers.TestCollectionHandler.get_dummy_request(self)
        data['pgp_key_remove'] = False
        data['old_password'] = ''
        return data


class TestAdminInstance(helpers.TestInstanceHandler):
    _handler = user.UserInstance
    _test_desc = {
      'model': User,
      'create': user.create,
      'data': {
          'role': 'admin',
          'mail_address': 'admin@theguardian.com',
          'language': 'en'
      }
    }

    def get_dummy_request(self):
        data = helpers.TestInstanceHandler.get_dummy_request(self)
        data['pgp_key_remove'] = False
        data['old_password'] = ''
        return data


class TestReceiverCollection(TestAdminCollection):
    _test_desc = {
      'model': User,
      'create': user.create,
      'data': {
          'name': u'Mario Rossi',
          'mail_address': 'receiver@theguardian.com',
          'language': 'en'
      }
    }


class TestReceiverInstance(TestAdminInstance):
    _test_desc = {
      'model': User,
      'create': user.create,
      'data': {
          'name': u'Mario Rossi',
          'mail_address': 'receiver@theguardian.com',
          'language': 'en'
      }
    }


class TestCustodianCollection(TestAdminCollection):
    _test_desc = {
      'model': User,
      'create': user.create,
      'data': {
          'role': 'custodian',
          'name': u'Mario Rossi',
          'mail_address': 'custodian@theguardian.com',
          'language': 'en'
      }
    }


class TestCustodianInstance(TestAdminCollection):
    _test_desc = {
      'model': User,
      'create': user.create,
      'data': {
          'role': 'custodian',
          'mail_address': 'custodian@theguardian.com',
          'language': 'en'
      }
    }

class UserTenantTestBaseClass(helpers.TestHandlerWithPopulatedDB):
    _handler = user.UserTenantCollection

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)

        for r in (yield receiver.get_receiver_list(1, 'en')):
            if r['pgp_key_fingerprint'] == u'BFB3C82D1B5F6A94BDAC55C6E70460ABF9A4C8C1':
                self.rcvr_id = r['id']

        t = yield tenant.create(get_dummy_tenant_desc())
        yield refresh_memory_variables([4])

class TestUserTenantCollection(UserTenantTestBaseClass):
    _handler = user.UserTenantCollection

    @inlineCallbacks
    def test_get(self):
        yield user.create_usertenant_assoication(self.rcvr_id, 4)
        handler = self.request(role='admin')
        response = yield handler.get(self.rcvr_id)
        self.assertEqual(response[0]['user_id'], self.rcvr_id)
        self.assertEqual(response[0]['tenant_id'], 4)

    @inlineCallbacks
    def test_post(self):
        request_data = {
            'tenant_id': 4
        }
        handler = self.request(request_data, role='admin')
        response = yield handler.post(self.rcvr_id)

        response = yield handler.get(self.rcvr_id)
        self.assertEqual(response[0]['user_id'], self.rcvr_id)
        self.assertEqual(response[0]['tenant_id'], 4)

class TestUserTenantInstance(UserTenantTestBaseClass):
    _handler = user.UserTenantInstance

    @inlineCallbacks
    def test_delete(self):
        yield user.create_usertenant_assoication(self.rcvr_id, 4)
        handler = self.request(role='admin')
        response = yield handler.delete(self.rcvr_id, 4)

        self._handler = user.UserTenantCollection
        handler = self.request(role='admin')
        response = yield handler.get(self.rcvr_id)
        self.assertEqual(len(response), 0)
