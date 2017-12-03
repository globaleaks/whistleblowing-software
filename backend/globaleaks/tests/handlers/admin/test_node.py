# -*- coding: utf-8 -*-

from globaleaks import __version__
from globaleaks.handlers.admin import node
from globaleaks.models.l10n import NodeL10NFactory
from globaleaks.rest.errors import InvalidInputFormat, InvalidModelInput
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks

# special guest:
stuff = u"³²¼½¬¼³²"


class TestNodeInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = node.NodeInstance

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        response = yield handler.get()

        self.assertTrue(response['version'], __version__)

    @inlineCallbacks
    def test_put_update_node(self):
        self.dummyNode['hostname'] = 'blogleaks.blogspot.com'

        for attrname in NodeL10NFactory.localized_keys:
            self.dummyNode[attrname] = stuff

        handler = self.request(self.dummyNode, role='admin')
        response = yield handler.put()

        self.assertTrue(isinstance(response, dict))
        self.assertTrue(response['version'], __version__)

        for response_key in response.keys():
            # some keys are added by GLB, and can't be compared
            if response_key in ['password', 'languages_supported',
                                'version', 'version_db',
                                'latest_version',
                                'configured', 'wizard_done',
                                'receipt_salt', 'languages_enabled',
                                'root_tenant', 'https_possible',
                                'hostname', 'onionservice']:
                continue

            self.assertEqual(response[response_key],
                             self.dummyNode[response_key])

    @inlineCallbacks
    def test_put_update_node_invalid_lang(self):
        self.dummyNode['languages_enabled'] = ["en", "shit"]
        handler = self.request(self.dummyNode, role='admin')

        yield self.assertFailure(handler.put(), InvalidInputFormat)

    @inlineCallbacks
    def test_put_update_node_languages_with_default_not_compatible_with_enabled(self):
        self.dummyNode['languages_enabled'] = ["fr"]
        self.dummyNode['default_language'] = "en"
        handler = self.request(self.dummyNode, role='admin')

        yield self.assertFailure(handler.put(), InvalidInputFormat)

    @inlineCallbacks
    def test_put_update_node_languages_removing_en_adding_fr(self):
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

    def test_put_update_node_invalid_wbtip_ttl(self):
        self.dummyNode['wbtip_timetolive'] = -10

        handler = self.request(self.dummyNode, role='admin')

        return self.assertFailure(handler.put(), InvalidModelInput)
