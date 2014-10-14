# -*- coding: utf-8 -*-
import random
import os

import json

from twisted.internet.defer import inlineCallbacks

from globaleaks.rest.errors import InvalidInputFormat
from globaleaks.tests import helpers
from globaleaks.rest import requests, errors
from globaleaks.handlers import admin, admstaticfiles
from globaleaks.settings import GLSetting
from globaleaks import __version__
from globaleaks.models import Node, Context, Receiver
from globaleaks.utils.utility import uuid4

# special guest:
from io import BytesIO as StringIO

class TestNodeInstance(helpers.TestHandler):
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

        stuff = u"³²¼½¬¼³²"
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
                                'configured' ]:
                continue

            print response_key
            self.assertEqual(self.responses[0][response_key],
                             self.dummyNode[response_key])

    @inlineCallbacks
    def test_put_update_node_invalid_lang(self):
        self.dummyNode['languages_enabled'] = ["en", "shit" ]
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

    @inlineCallbacks
    def test_put_update_node_reset_css(self):
        self.dummyNode['reset_css'] = True

        open(os.path.join(GLSetting.static_path, "custom_stylesheet.css"), 'a').close()

        handler = self.request(self.dummyNode, role='admin')
        yield handler.put()

        self.assertFalse(os.path.exists(os.path.join(GLSetting.static_path, "custom_stylesheet.css")))

    @inlineCallbacks
    def test_put_update_node_reset_css_with_no_css(self):
        self.dummyNode['reset_css'] = True

        handler = self.request(self.dummyNode, role='admin')
        yield handler.put()

    @inlineCallbacks
    def test_put_update_node_reset_homepage(self):
        self.dummyNode['reset_homepage'] = True

        open(os.path.join(GLSetting.static_path, "custom_homepage.html"), 'a').close()

        handler = self.request(self.dummyNode, role='admin')
        yield handler.put()

        self.assertFalse(os.path.exists(os.path.join(GLSetting.static_path, "custom_homepage.html")))

    @inlineCallbacks
    def test_put_update_node_reset_homepage_with_no_homepage(self):
        self.dummyNode['reset_homepage'] = True

        handler = self.request(self.dummyNode, role='admin')
        yield handler.put()

class TestNotificationInstance(helpers.TestHandler):
    _handler = admin.notification.NotificationInstance

    @inlineCallbacks
    def test_update_notification(self):
         self.dummyNotification['server'] = 'stuff'
         handler = self.request(self.dummyNotification, role='admin')
         yield handler.put()
         self.assertEqual(self.responses[0]['server'], 'stuff')


class TestContextsCollection(helpers.TestHandler):
    _handler = admin.ContextsCollection

    def test_get(self):
        handler = self.request(role='admin')
        return handler.get()

    @inlineCallbacks
    def test_post(self):

        stuff = u"³²¼½¬¼³²"
        for attrname in Context.localized_strings:
            self.dummyContext[attrname] = u"³²¼½¬¼³²"

        # the test context need fields to be present
        from globaleaks.handlers.admin.field import create_field
        for idx, field in enumerate(self.dummyFields):
            self.dummyFields[idx]['id'] = yield create_field(field, 'en')

        # the test context need fields to be present
        from globaleaks.handlers.admin.field import create_field
        for idx, field in enumerate(self.dummyFields):
            f = yield create_field(field, 'en')
            self.dummyFields[idx]['id'] = f['id']

        self.dummyContext['steps'][0]['children'] = [
            self.dummyFields[0]['id'], # Field 1
            self.dummyFields[1]['id'], # Field 2
            self.dummyFields[4]['id']  # Generalities
        ]

        handler = self.request(self.dummyContext, role='admin')
        yield handler.post()

        self.dummyContext['id'] =  self.responses[0]['id']
        self.dummyContext['creation_date'] = self.responses[0]['creation_date']
        self.assertEqual(self.responses[0]['description'], stuff)


class TestContextInstance(helpers.TestHandler):
    _handler = admin.ContextInstance

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        yield handler.get(self.dummyContext['id'])
        self._handler.validate_message(json.dumps(self.responses[0]), requests.adminContextDesc)

    @inlineCallbacks
    def test_put(self):
        stuff = u"³²¼½¬¼³²"
        for attrname in Context.localized_strings:
            self.dummyContext[attrname] = u"³²¼½¬¼³²"

        handler = self.request(self.dummyContext, role='admin')
        yield handler.put(self.dummyContext['id'])
        self.dummyContext['creation_date'] = self.responses[0]['creation_date']
        self.dummyContext['last_update'] = self.responses[0]['last_update']
        self.assertEqual(self.responses[0]['description'], stuff)

    @inlineCallbacks
    def test_update_context_timetolive(self):
        self.dummyContext['submission_timetolive'] = 23 # hours
        self.dummyContext['tip_timetolive'] = 100 # days

        stuff = u"³²¼½¬¼³²"
        for attrname in Context.localized_strings:
            self.dummyContext[attrname] = stuff

        handler = self.request(self.dummyContext, role='admin')
        yield handler.put(self.dummyContext['id'])

        self.assertEqual(self.responses[0]['submission_timetolive'], self.dummyContext['submission_timetolive'])
        self.assertEqual(self.responses[0]['tip_timetolive'], self.dummyContext['tip_timetolive'])

        @inlineCallbacks
        def test_update_context_invalid_timetolive(self):
            self.dummyContext['submission_timetolive'] = 1000 # hours
            self.dummyContext['tip_timetolive'] = 3 # days

            stuff = u"³²¼½¬¼³²"
            for attrname in Context.localized_strings:
                self.dummyContext[attrname] = stuff

            # 1000 hours are more than three days, and a Tip can't live less than a submission
            handler = self.request(self.dummyContext, role='admin')

            yield self.assertFailure(handler.put(self.dummyContext['id']), errors.InvalidTipSubmCombo)

    @inlineCallbacks
    def test_delete(self):
        handler = self.request(self.dummyContext, role='admin')
        try:
            yield handler.delete(self.dummyContext['id'])
            self.assertTrue(True)
        except Exception as excep:
            print "Wrong exception: %s" % excep
            raise excep

        yield self.assertFailure(handler.get(self.dummyContext['id']),
                     errors.ContextIdNotFound)

class TestReceiversCollection(helpers.TestHandler):
    _handler = admin.ReceiversCollection

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        yield handler.get()

        self.assertEqual(len(self.responses[0]), 2)

    @inlineCallbacks
    def test_post(self):
        self.dummyReceiver_1['name'] = 'beppe'

        new_email = "guy@globaleaks.xxx"
        self.dummyReceiver_1['mail_address'] = new_email
        self.dummyReceiver_1['password'] = helpers.VALID_PASSWORD1

        stuff = u"³²¼½¬¼³²"
        for attrname in Receiver.localized_strings:
            self.dummyReceiver_1[attrname] = stuff

        handler = self.request(self.dummyReceiver_1, role='admin')
        yield handler.post()

    @inlineCallbacks
    def test_post_invalid_mail_addr(self):
        self.dummyReceiver_1['name'] = 'beppe'
        self.dummyReceiver_1['mail_address'] = "[antani@xx.it"
        self.dummyReceiver_1['password'] = helpers.VALID_PASSWORD1

        stuff = u"³²¼½¬¼³²"
        for attrname in Receiver.localized_strings:
            self.dummyReceiver_1[attrname] = stuff

        handler = self.request(self.dummyReceiver_1, role='admin')

        yield self.assertFailure(handler.post(), InvalidInputFormat)

    @inlineCallbacks
    def test_post_duplicated_username(self):
        self.dummyReceiver_1['name'] = 'beppe'
        self.dummyReceiver_1['mail_address'] = "evilamaker.py@vecllais.naif"
        self.dummyReceiver_1['password'] = helpers.VALID_PASSWORD1

        stuff = u"³²¼½¬¼³²"
        for attrname in Receiver.localized_strings:
            self.dummyReceiver_1[attrname] = stuff

        handler = self.request(self.dummyReceiver_1, role='admin')

        yield handler.post()

        # duplicated username raises errors.ExpectedUniqueField
        yield self.assertFailure(handler.post(), errors.ExpectedUniqueField)


class TestReceiverInstance(helpers.TestHandler):
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

        stuff = u"³²¼½¬¼³²"
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

        stuff = u"³²¼½¬¼³²"
        for attrname in Receiver.localized_strings:
            self.dummyReceiver_1[attrname] = stuff

        handler = self.request(self.dummyReceiver_1, role='admin')
        yield handler.put(self.dummyReceiver_1['id'])
        self.assertEqual(self.responses[0]['name'], self.dummyReceiver_1['name'])

    @inlineCallbacks
    def test_put_invalid_context_id(self):
        self.dummyReceiver_1['name'] = u'justalazyupdate'
            # keep the context ID wrong but matching eventually regexp
        self.dummyReceiver_1['contexts'] = [ unicode(uuid4()) ]
        self.dummyReceiver_1['name'] = u'another unique name %d' % random.randint(1, 10000)
        self.dummyReceiver_1['mail_address'] = u'but%d@random.id' % random.randint(1, 1000)
        self.dummyReceiver_1['password'] = u'12345678andaletter'

        stuff = u"³²¼½¬¼³²"
        for attrname in Receiver.localized_strings:
            self.dummyReceiver_1[attrname] = stuff

        handler = self.request(self.dummyReceiver_1, role='admin')

        yield self.assertFailure(handler.put(self.dummyReceiver_1['id']),
                     errors.ContextIdNotFound)

    @inlineCallbacks
    def test_delete(self):
        handler = self.request(self.dummyReceiver_1, role='admin')
        try:
            yield handler.delete(self.dummyReceiver_1['id'])
            self.assertTrue(True)
        except Exception as excep:
            print "Wrong exception: %s" % excep
            raise excep

        yield self.assertFailure(handler.get(self.dummyReceiver_1['id']),
                     errors.ReceiverIdNotFound)


class TestAdminStaticFileInstance(helpers.TestHandler):
    """
    Sadly we can't use the official handler test, because in a
    file upload, Cyclone and GL patches transform the body in a StringIO.

    So the code in GLBackend expect a StringIO. If here I use the handlers,
    with a StringIO inside, can't be JSON-ized.

    If I send a real dict to the handler, the GLBackend code fail, because
    expect a StringIO.

    If I support in the handler both kind of data, well, no. I would not
    change the handler code just to fit our test.

    So... that's shit, but _post hanlder is tested in a more direct way
    """
    _handler = admstaticfiles.StaticFileInstance

    crappyjunk =  "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

    fakeFile = dict()
    fakeFile['body'] = StringIO()
    fakeFile['body'].write(crappyjunk)
    fakeFile['body_len'] = len(crappyjunk)
    fakeFile['content_type'] = 'image/jpeg'
    fakeFile['filename'] = 'imag0005.jpg'

    @inlineCallbacks
    def test_file_download(self):
        realpath = os.path.join(GLSetting.static_path, self.fakeFile['filename'])
        dumped_file = yield admstaticfiles.dump_static_file(self.fakeFile, realpath)
        self.assertTrue(dumped_file.has_key('filelocation'))

        self.responses = []

        handler = self.request(role='admin', kwargs={'path': GLSetting.static_path})
        yield handler.get(self.fakeFile['filename'])
        self.assertEqual(self.responses[0], self.crappyjunk)

    @inlineCallbacks
    def test_file_delete_it(self):
        realpath = os.path.join(GLSetting.static_path, self.fakeFile['filename'])
        dumped_file = yield admstaticfiles.dump_static_file(self.fakeFile, realpath)
        self.assertTrue(dumped_file.has_key('filelocation'))

        self.responses = []

        handler = self.request(role='admin', kwargs={'path': GLSetting.static_path})
        yield handler.delete(self.fakeFile['filename'])


class TestAdminStaticFileList(helpers.TestHandler):
    """
    """
    _handler = admstaticfiles.StaticFileList

    crappyjunk =  "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

    # default files not filtered from get(/) handler
    default_files = [ 'globaleaks_logo.png',
                      'favicon.ico',
                      'robots.txt',
                      'default-profile-picture.png',
                      'custom_stylesheet.css']

    fakeFile = dict()
    fakeFile['body'] = StringIO()
    fakeFile['body'].write(crappyjunk)
    fakeFile['body_len'] = len(crappyjunk)
    fakeFile['content_type'] = 'image/jpeg'
    fakeFile['filename'] = 'imag0005.jpg'

    @inlineCallbacks
    def test_get_default_staticfile_list(self):
        handler = self.request(role='admin')
        yield handler.get()
        self.assertTrue( isinstance(self.responses[0], list) )

        # this check verifies that only not filtered default files are shown
        # other files shall be present and are ignored in this test
        files_dict = {}

        for f in self.responses[0]:
            files_dict[f['filename']] = f['size']

        for system_names in self.default_files:
            self.assertTrue(system_names in files_dict.keys())


    @inlineCallbacks
    def test_get_list_with_one_custom_file(self):
        realpath = os.path.join(GLSetting.static_path, self.fakeFile['filename'])
        dumped_file = yield admstaticfiles.dump_static_file(self.fakeFile, realpath)
        self.assertTrue(dumped_file.has_key('filelocation'))

        handler = self.request(role='admin')
        yield handler.get()
        self.assertTrue( isinstance(self.responses[0], list) )

        found = False

        for f in self.responses[0]:
            if f['filename'] == self.fakeFile['filename']:
                found = True
                self.assertEqual(self.fakeFile['body_len'], f['size'])

        self.assertTrue(found)
