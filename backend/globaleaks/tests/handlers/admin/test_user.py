# -*- coding: utf-8 -*-
from globaleaks.handlers.admin import user
from globaleaks.models import User
from globaleaks.tests import helpers

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
