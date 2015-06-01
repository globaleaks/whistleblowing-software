# -*- coding: utf-8 -*-
import random
import json

from twisted.internet.defer import inlineCallbacks

from globaleaks import __version__
from globaleaks.db.datainit import load_appdata
from globaleaks.rest.errors import InvalidInputFormat
from globaleaks.tests import helpers
from globaleaks.rest import requests, errors
from globaleaks.handlers import admin
from globaleaks.models import Node, Context, Receiver
from globaleaks.utils.utility import uuid4

# special guest:

stuff = u"³²¼½¬¼³²"


class TestNodeInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = admin.NodeInstance

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        yield handler.get()

        self.assertTrue(self.responses[0]['version'], __version__)

    @inlineCallbacks
    def test_put_update_node(self):
        self.dummyNode['hidden_service'] = 'http://abcdef1234567890.onion'
        self.dummyNode['public_site'] = 'https://blogleaks.blogspot.com'

        for attrname in Node.localized_strings:
            self.dummyNode[attrname] = stuff

        handler = self.request(self.dummyNode, role='admin')
        yield handler.put()

        self.assertTrue(isinstance(self.responses[0], dict))
        self.assertTrue(self.responses[0]['version'], __version__)

        for response_key in self.responses[0].keys():

            # some keys are added by GLB, and can't be compared
            if response_key in ['password', 'languages_supported',
                                'creation_date', 'last_update',
                                'version', 'receipt_example',
                                'configured', 'wizard_done']:
                continue

            self.assertEqual(self.responses[0][response_key],
                             self.dummyNode[response_key])

    @inlineCallbacks
    def test_put_update_node_invalid_lang(self):
        self.dummyNode['languages_enabled'] = ["en", "shit"]
        handler = self.request(self.dummyNode, role='admin')

        yield self.assertFailure(handler.put(), InvalidInputFormat)

    @inlineCallbacks
    def test_put_update_node_invalid_hidden(self):
        self.dummyNode['hidden_service'] = 'http://www.scroogle.com'
        self.dummyNode['public_site'] = 'http://blogleaks.blogspot.com'

        handler = self.request(self.dummyNode, role='admin')

        yield self.assertFailure(handler.put(), InvalidInputFormat)

    @inlineCallbacks
    def test_put_update_node_invalid_public(self):
        self.dummyNode['hidden_service'] = 'http://abcdef1234567890.onion'
        self.dummyNode['public_site'] = 'blogleaks.blogspot.com'

        handler = self.request(self.dummyNode, role='admin')

        yield self.assertFailure(handler.put(), InvalidInputFormat)


class TestNotificationInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = admin.notification.NotificationInstance

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        yield handler.get()
        self.assertEqual(self.responses[0]['server'], 'mail.headstrong.de')

    @inlineCallbacks
    def test_put(self):
        handler = self.request(role='admin')
        yield handler.get()

        self.responses[0]['server'] = 'stuff'

        handler = self.request(self.responses[0], role='admin')
        yield handler.put()
        self.assertEqual(self.responses[1]['server'], 'stuff')

    @inlineCallbacks
    def test_put_reset_templates(self):
        handler = self.request(role='admin')
        yield handler.get()

        self.responses[0]['reset_templates'] = True

        handler = self.request(self.responses[0], role='admin')
        yield handler.put()

        appdata_dict = load_appdata()
        for k in appdata_dict['templates']:
            self.assertEqual(self.responses[1][k], appdata_dict['templates'][k]['en'])


class TestContextsCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = admin.ContextsCollection

    def test_get(self):
        handler = self.request(role='admin')
        return handler.get()


class TestContextsCreate(helpers.TestHandlerWithPopulatedDB):
    _handler = admin.ContextCreate

    @inlineCallbacks
    def test_post(self):
        for attrname in Context.localized_strings:
            self.dummyContext[attrname] = stuff

        self.dummyContext['steps'][0]['children'] = []

        handler = self.request(self.dummyContext, role='admin')
        yield handler.post()

        self.dummyContext['id'] = self.responses[0]['id']
        self.dummyContext['creation_date'] = self.responses[0]['creation_date']
        self.assertEqual(self.responses[0]['description'], stuff)


class TestContextInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = admin.ContextInstance

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        yield handler.get(self.dummyContext['id'])
        self._handler.validate_message(json.dumps(self.responses[0]), requests.AdminContextDesc)

    @inlineCallbacks
    def test_put(self):
        for attrname in Context.localized_strings:
            self.dummyContext[attrname] = stuff

        handler = self.request(self.dummyContext, role='admin')
        yield handler.put(self.dummyContext['id'])
        self.dummyContext['creation_date'] = self.responses[0]['creation_date']
        self.dummyContext['last_update'] = self.responses[0]['last_update']
        self.assertEqual(self.responses[0]['description'], stuff)

    @inlineCallbacks
    def test_put_delete_all_steps(self):
        for attrname in Context.localized_strings:
            self.dummyContext[attrname] = stuff

        self.dummyContext['steps'] = []
        handler = self.request(self.dummyContext, role='admin')
        yield handler.put(self.dummyContext['id'])
        self.assertEqual(len(self.responses[0]['steps']), 0)

    @inlineCallbacks
    def test_put_delete_fields_of_all_steps(self):
        for attrname in Context.localized_strings:
            self.dummyContext[attrname] = stuff

        for s in self.dummyContext['steps']:
            s['children'] = []

        handler = self.request(self.dummyContext, role='admin')
        yield handler.put(self.dummyContext['id'])

        for s in self.responses[0]['steps']:
            self.assertEqual(len(s['children']), 0)

    @inlineCallbacks
    def test_update_context_timetolive(self):
        self.dummyContext['tip_timetolive'] = 100  # days

        for attrname in Context.localized_strings:
            self.dummyContext[attrname] = stuff

        handler = self.request(self.dummyContext, role='admin')
        yield handler.put(self.dummyContext['id'])

        self.assertEqual(self.responses[0]['tip_timetolive'], self.dummyContext['tip_timetolive'])

    @inlineCallbacks
    def test_update_context_invalid_timetolive(self):
        self.dummyContext['tip_timetolive'] = -3  # days

        for attrname in Context.localized_strings:
            self.dummyContext[attrname] = stuff

        # 1000 hours are more than three days, and a Tip can't live less than a submission
        handler = self.request(self.dummyContext, role='admin')

        yield self.assertFailure(handler.put(self.dummyContext['id']), errors.InvalidTipTimeToLive)

    @inlineCallbacks
    def test_delete(self):
        handler = self.request(self.dummyContext, role='admin')
        yield handler.delete(self.dummyContext['id'])
        yield self.assertFailure(handler.get(self.dummyContext['id']),
                                 errors.ContextIdNotFound)


class TestReceiversCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = admin.ReceiversCollection

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        yield handler.get()

        self.assertEqual(len(self.responses[0]), 2)


class TestReceiverCreate(helpers.TestHandlerWithPopulatedDB):
    _handler = admin.ReceiverCreate

    @inlineCallbacks
    def test_post(self):
        self.dummyReceiver_1['name'] = 'beppe'

        self.dummyReceiver_1['mail_address'] =  "test@globaleaks.org"
        self.dummyReceiver_1['password'] = helpers.VALID_PASSWORD1

        for attrname in Receiver.localized_strings:
            self.dummyReceiver_1[attrname] = stuff

        handler = self.request(self.dummyReceiver_1, role='admin')
        yield handler.post()

    @inlineCallbacks
    def test_post_invalid_mail_address(self):
        self.dummyReceiver_1['name'] = 'beppe'
        self.dummyReceiver_1['mail_address'] = "[est@globaleaks.org"
        self.dummyReceiver_1['password'] = helpers.VALID_PASSWORD1

        for attrname in Receiver.localized_strings:
            self.dummyReceiver_1[attrname] = stuff

        handler = self.request(self.dummyReceiver_1, role='admin')

        yield self.assertFailure(handler.post(), InvalidInputFormat)


class TestReceiverInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = admin.ReceiverInstance

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        yield handler.get(self.dummyReceiver_1['id'])
        del self.dummyReceiver_1['contexts']
        del self.responses[0]['contexts']
        self.assertEqual(self.responses[0]['id'], self.dummyReceiver_1['id'])

    @inlineCallbacks
    def test_put_change_password(self):
        self.dummyReceiver_1['context_id'] = ''
        self.dummyReceiver_1['name'] = u'new unique name %d' % random.randint(1, 10000)
        self.dummyReceiver_1['mail_address'] = u'but%d@random.id' % random.randint(1, 1000)
        self.dummyReceiver_1['password'] = u'12345678antani'

        for attrname in Receiver.localized_strings:
            self.dummyReceiver_1[attrname] = stuff

        handler = self.request(self.dummyReceiver_1, role='admin')
        yield handler.put(self.dummyReceiver_1['id'])
        self.assertEqual(self.responses[0]['name'], self.dummyReceiver_1['name'])

    @inlineCallbacks
    def test_put_with_password_empty(self):
        self.dummyReceiver_1['context_id'] = ''
        self.dummyReceiver_1['name'] = u'new unique name %d' % random.randint(1, 10000)
        self.dummyReceiver_1['mail_address'] = u'but%d@random.id' % random.randint(1, 1000)
        self.dummyReceiver_1['password'] = u""

        for attrname in Receiver.localized_strings:
            self.dummyReceiver_1[attrname] = stuff

        handler = self.request(self.dummyReceiver_1, role='admin')
        yield handler.put(self.dummyReceiver_1['id'])
        self.assertEqual(self.responses[0]['name'], self.dummyReceiver_1['name'])

    @inlineCallbacks
    def test_put_invalid_context_id(self):
        self.dummyReceiver_1['name'] = u'justalazyupdate'
        self.dummyReceiver_1['contexts'] = [unicode(uuid4())]
        self.dummyReceiver_1['name'] = u'another unique name %d' % random.randint(1, 10000)
        self.dummyReceiver_1['mail_address'] = u'but%d@random.id' % random.randint(1, 1000)
        self.dummyReceiver_1['password'] = u'12345678andaletter'

        for attrname in Receiver.localized_strings:
            self.dummyReceiver_1[attrname] = stuff

        handler = self.request(self.dummyReceiver_1, role='admin')

        yield self.assertFailure(handler.put(self.dummyReceiver_1['id']),
                                 errors.ContextIdNotFound)

    @inlineCallbacks
    def test_delete(self):
        handler = self.request(self.dummyReceiver_1, role='admin')
        yield handler.delete(self.dummyReceiver_1['id'])
        yield self.assertFailure(handler.get(self.dummyReceiver_1['id']),
                                 errors.ReceiverIdNotFound)
