# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.admin import receiver
from globaleaks.handlers.admin import user
from globaleaks.tests import helpers

class TestAdminCollection(helpers.TestCollectionHandler):
    _handler = user.UsersCollection
    _test_desc = {
      'model': models.User,
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
      'model': models.User,
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
      'model': models.User,
      'create': user.create,
      'data': {
          'name': u'Mario Rossi',
          'mail_address': 'receiver@theguardian.com',
          'language': 'en'
      }
    }


class TestReceiverInstance(TestAdminInstance):
    _test_desc = {
      'model': models.User,
      'create': user.create,
      'data': {
          'name': u'Mario Rossi',
          'mail_address': 'receiver@theguardian.com',
          'language': 'en'
      }
    }


class TestCustodianCollection(TestAdminCollection):
    _test_desc = {
      'model': models.User,
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
      'model': models.User,
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

        yield self.test_model_count(models.UserTenant, 0)
        yield user.create_usertenant_association(self.rcvr_id, 2)
        yield self.test_model_count(models.UserTenant, 1)


class TestUserTenantCollection(UserTenantTestBaseClass):
    _handler = user.UserTenantCollection

    @inlineCallbacks
    def test_post(self):
        request_data = {
            'tenant_id': 3
        }

        handler = self.request(request_data, role='admin')
        response = yield handler.post(self.rcvr_id)
        self.assertEqual(response['user_id'], self.rcvr_id)
        self.assertEqual(response['tenant_id'], 3)

        yield self.test_model_count(models.UserTenant, 2)


class TestUserTenantInstance(UserTenantTestBaseClass):
    _handler = user.UserTenantInstance

    @inlineCallbacks
    def test_delete(self):
        handler = self.request(role='admin')
        yield handler.delete(self.rcvr_id, 2)

        yield self.test_model_count(models.UserTenant, 0)
