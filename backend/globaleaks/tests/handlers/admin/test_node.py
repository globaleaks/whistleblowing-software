# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks import __version__
from globaleaks import models
from globaleaks.handlers.admin import node, user
from globaleaks.orm import transact, tw
from globaleaks.rest.errors import InputValidationError, InvalidAuthentication
from globaleaks.tests import helpers


@transact
def set_receiver_acl_flag_true(session, rcvr_id):
    rcvr = session.query(models.User).filter_by(id=rcvr_id).first()
    rcvr.can_edit_general_settings = True


@transact
def get_config_value(session, tid, config_key):
    config_value = session.query(models.Config).filter_by(var_name=config_key, tid=tid).first()
    return config_value.value


class TestNodeInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = node.NodeInstance

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        response = yield handler.get()

        self.assertTrue(response['version'], __version__)

    @inlineCallbacks
    def test_get_receiver_general_settings_acl(self):
        """Confirm receivers can read general settings ACL"""
        yield set_receiver_acl_flag_true(self.dummyReceiver_1['id'])

        handler = self.request(user_id=self.dummyReceiver_1['id'], role='receiver')
        response = yield handler.get()

        self.assertNotIn('version', response)
        self.assertIn('header_title_homepage', response)

    @inlineCallbacks
    def test_confirm_fail_receiver_acl_cleared(self):
        handler = self.request(user_id=self.dummyReceiver_1['id'], role='receiver')
        with self.assertRaises(InvalidAuthentication):
            yield handler.get()

    @inlineCallbacks
    def test_put_update_node(self):
        self.dummyNode['multisite'] = True

        handler = self.request(self.dummyNode, role='admin')
        response = yield handler.put()

        self.assertTrue(isinstance(response, dict))
        self.assertTrue(response['version'], __version__)

        self.assertEqual(response['multisite'], True)

    @inlineCallbacks
    def test_put_update_node_invalid_lang(self):
        self.dummyNode['languages_enabled'] = ["en", "shit"]
        handler = self.request(self.dummyNode, role='admin')

        yield self.assertFailure(handler.put(), InputValidationError)

    @inlineCallbacks
    def test_put_update_node_languages(self):
        # this tests start setting en as the only enabled language and
        # ends keeping enabled only french.
        self.dummyNode['languages_enabled'] = ["en"]
        self.dummyNode['default_language'] = "en"
        handler = self.request(self.dummyNode, role='admin')
        yield handler.put()

        self.dummyNode['languages_enabled'] = ["fr"]
        self.dummyNode['default_language'] = "fr"
        handler = self.request(self.dummyNode, role='admin')
        yield handler.put()

    @inlineCallbacks
    def test_update_ignored_fields(self):
        self.dummyNode['onionservice'] = 'xxx'
        self.dummyNode['hostname'] = 'yyy'

        handler = self.request(self.dummyNode, role='admin')

        resp = yield handler.put()

        self.assertNotEqual('xxx', resp['hostname'])
        self.assertNotEqual('yyy', resp['onionservice'])

    @inlineCallbacks
    def test_receiver_general_settings_update_field(self):
        """Confirm fields out of the receiver's set updates"""

        yield set_receiver_acl_flag_true(self.dummyReceiver_1['id'])
        self.dummyNode['header_title_homepage'] = "Whistleblowing Homepage"

        handler = self.request(self.dummyNode, role='receiver')
        resp = yield handler.put()
        self.assertEqual("Whistleblowing Homepage", resp['header_title_homepage'])

    @inlineCallbacks
    def test_receiver_confirm_failure_for_priv_fields_updates(self):
        """Confirm privelleged fields are ignored"""

        yield set_receiver_acl_flag_true(self.dummyReceiver_1['id'])
        self.dummyNode['smtp_server'] = 'not.a.real.smtpserver'

        handler = self.request(self.dummyNode, role='receiver')
        yield handler.put()

        smtp_server = yield get_config_value(1, 'smtp_server')
        self.assertNotEqual('not.a.real.smtpserver', smtp_server)
