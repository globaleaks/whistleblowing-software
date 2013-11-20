# -*- coding: utf-8 -*-
import random
import os
from twisted.internet.defer import inlineCallbacks

from globaleaks.rest.errors import InvalidInputFormat
from globaleaks.tests import helpers
from globaleaks.rest import errors
from globaleaks.handlers import admin, admstaticfiles
from globaleaks.settings import transact, GLSetting
from globaleaks import __version__

# special guest:
from globaleaks.models import Notification
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

        handler = self.request(self.dummyNode, role='admin')
        yield handler.put()

        self.assertTrue(isinstance(self.responses[0], dict))
        self.assertTrue(self.responses[0]['version'], __version__)

        for response_key in self.responses[0].keys():

            # some keys are added by GLB, and can't be compared
            if response_key in ['password', 'languages_supported',
                                'creation_date', 'last_update', 'version' ]:
                continue

            self.assertEqual(self.responses[0][response_key],
                             self.dummyNode[response_key])


    @inlineCallbacks
    def test_put_update_node_invalid_lang(self):
        self.dummyNode['languages_enabled'] = ["en", "shit" ]

        handler = self.request(self.dummyNode, role='admin')
        try:
            yield handler.put()
            self.assertTrue(False)
        except InvalidInputFormat as excep:
            self.assertSubstring("Invalid lang code enabled: shit", excep.reason)
        except Exception as excep:
            print "Wrong exception: %s" % excep
            self.assertFalse(True)

    @inlineCallbacks
    def test_put_update_node_invalid_hidden(self):
        self.dummyNode['hidden_service'] = 'http://www.scroogle.com'
        self.dummyNode['public_site'] = 'http://blogleaks.blogspot.com'

        handler = self.request(self.dummyNode, role='admin')
        try:
            yield handler.put()
            self.assertTrue(False)
        except InvalidInputFormat:
            self.assertTrue(True)
        except Exception as excep:
            print "Wrong exception: %s" % excep
            raise excep

    @inlineCallbacks
    def test_put_update_node_invalid_public(self):
        self.dummyNode['hidden_service'] = 'http://abcdef1234567890.onion'
        self.dummyNode['public_site'] = 'blogleaks.blogspot.com'

        handler = self.request(self.dummyNode, role='admin')
        try:
            yield handler.put()
            self.assertTrue(False)
        except InvalidInputFormat:
            self.assertTrue(True)
        except Exception as excep:
            print "Wrong exception: %s" % excep.log_message
            raise excep


class TestNotificationInstance(helpers.TestHandler):
    _handler = admin.NotificationInstance

    @transact
    def mock_initialize_notification(self, store):
        """
        This is what is commonly performed in initialize_node
        """
        # load notification template

        notification = Notification()
        notification.tip_template = "my dummy template %EventName%"
        # It's the only NOT NULL variable with CHECK
        notification.security = Notification._security_types[0]
        store.add(notification)

    @inlineCallbacks
    def test_update_notification(self):
        yield self.mock_initialize_notification
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
        self.dummyContext['name'] = "a random one to avoid dup %d" % random.randint(1, 1000)

        handler = self.request(self.dummyContext, role='admin')
        yield handler.post()

        self.dummyContext['context_gus'] =  self.responses[0]['context_gus']
        self.dummyContext['creation_date'] = self.responses[0]['creation_date']
        self.assertEqual(self.responses[0]['name'], self.dummyContext['name'])


class TestContextInstance(helpers.TestHandler):
    _handler = admin.ContextInstance

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        yield handler.get(self.dummyContext['context_gus'])

        self.assertTrue(isinstance(self.responses[0], dict))

        for response_key in self.responses[0].keys():

            # some keys are added by GLB, and can't be compared
            if response_key in ['creation_date', 'last_update', 'receipt_example']:
                continue

            # the localized strings are kept in one side as localized l10n
            # and in the other as dict.
            if response_key in ['name', 'description',
                                'receipt_description',
                                'submission_introduction',
                                'submission_disclaimer' ]:
                # print self.responses[0][response_key]
                # print self.dummyContext[response_key]
                continue

            if response_key in ['fields']:
                # refactor of fields, remove and enhance!
                continue

            self.assertEqual(self.responses[0][response_key],
                             self.dummyContext[response_key])


    @inlineCallbacks
    def test_put(self):
        self.dummyContext['description'] = u'how many readers remind of HIMEM.SYS?'

        handler = self.request(self.dummyContext, role='admin')
        yield handler.put(self.dummyContext['context_gus'])
        self.dummyContext['creation_date'] = self.responses[0]['creation_date']
        self.dummyContext['last_update'] = self.responses[0]['last_update']
        self.assertEqual(self.responses[0]['description'], self.dummyContext['description'])

    @inlineCallbacks
    def test_update_context_timetolive(self):
        self.dummyContext['submission_timetolive'] = 23 # hours
        self.dummyContext['tip_timetolive'] = 100 # days

        handler = self.request(self.dummyContext, role='admin')
        yield handler.put(self.dummyContext['context_gus'])

        self.assertEqual(self.responses[0]['submission_timetolive'], self.dummyContext['submission_timetolive'])
        self.assertEqual(self.responses[0]['tip_timetolive'], self.dummyContext['tip_timetolive'])

    @inlineCallbacks
    def test_update_context_invalid_timetolive(self):
        self.dummyContext['submission_timetolive'] = 1000 # hours
        self.dummyContext['tip_timetolive'] = 3 # days

        # 1000 hours are more than three days, and a Tip can't live less than a submission
        handler = self.request(self.dummyContext, role='admin')
        try:
            yield handler.put(self.dummyContext['context_gus'])
            self.assertTrue(False)
        except errors.InvalidTipSubmCombo:
            self.assertTrue(True)
        except Exception as excep:
            print "Wrong exception: %s" % excep
            self.assertTrue(False)


class TestReceiversCollection(helpers.TestHandler):
    _handler = admin.ReceiversCollection

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        yield handler.get()

        # XXX helpers.py.. Why self.responses is became a double array ?
        del self.dummyReceiver['contexts']
        del self.responses[0][0]['contexts']
        self.assertEqual(self.responses[0][0]['receiver_gus'], self.dummyReceiver['receiver_gus'])

    @inlineCallbacks
    def test_post(self):
        self.dummyReceiver['name'] = 'beppe'

        new_email = "guy@globaleaks.xxx"
        self.dummyReceiver['notification_fields']['mail_address'] = new_email
        self.dummyReceiver['password'] = helpers.VALID_PASSWORD1

        handler = self.request(self.dummyReceiver, role='admin')
        yield handler.post()

        # We delete this because it's randomly generated
        del self.responses[0]['receiver_gus']
        del self.dummyReceiver['receiver_gus']

        self.assertEqual(self.responses[0]['name'], self.dummyReceiver['name'])

    @inlineCallbacks
    def test_post_invalid_mail_addr(self):
        self.dummyReceiver['name'] = 'beppe'
        self.dummyReceiver['notification_fields']['mail_address'] = "[antani@xx.it"
        self.dummyReceiver['password'] = helpers.VALID_PASSWORD1

        handler = self.request(self.dummyReceiver, role='admin')

        try:
            yield handler.post()
            self.assertTrue(False)
        except errors.NoEmailSpecified:
            self.assertTrue(True)
        except Exception as excep:
            print "Wrong exception: %s" % excep.log_message
            raise excep

    @inlineCallbacks
    def test_post_duplicated_username(self):
        self.dummyReceiver['name'] = 'beppe'
        self.dummyReceiver['notification_fields']['mail_address'] = "evilamaker.py@vecllais.naif"
        self.dummyReceiver['password'] = helpers.VALID_PASSWORD1
        handler = self.request(self.dummyReceiver, role='admin')

        try:
            yield handler.post()
            yield handler.post() # duplication here!
            self.assertTrue(False)
        except errors.ExpectedUniqueField:
            self.assertTrue(True)
        except Exception as excep:
            print "Wrong exception: %s" % excep.log_message
            raise excep


class TestReceiverInstance(helpers.TestHandler):
    _handler = admin.ReceiverInstance

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        yield handler.get(self.dummyReceiver['receiver_gus'])
        del self.dummyReceiver['contexts']
        del self.responses[0]['contexts']
        self.assertEqual(self.responses[0]['receiver_gus'], self.dummyReceiver['receiver_gus'])

    @inlineCallbacks
    def test_put_change_password(self):
        self.dummyReceiver['context_gus'] = ''
        del self.dummyReceiver['username']
        self.dummyReceiver['name'] = u'new unique name %d' % random.randint(1, 10000)
        self.dummyReceiver['notification_fields']['mail_address'] = \
            u'but%d@random.id' % random.randint(1, 1000)
        self.dummyReceiver['password'] = u'12345678antani'

        handler = self.request(self.dummyReceiver, role='admin')
        yield handler.put(self.dummyReceiver['receiver_gus'])
        self.assertEqual(self.responses[0]['name'], self.dummyReceiver['name'])

    @inlineCallbacks
    def test_put_with_password_empty(self):
        self.dummyReceiver['context_gus'] = ''
        del self.dummyReceiver['username']
        self.dummyReceiver['name'] = u'new unique name %d' % random.randint(1, 10000)
        self.dummyReceiver['notification_fields']['mail_address'] =\
        u'but%d@random.id' % random.randint(1, 1000)
        self.dummyReceiver['password'] = u""

        handler = self.request(self.dummyReceiver, role='admin')
        yield handler.put(self.dummyReceiver['receiver_gus'])
        self.assertEqual(self.responses[0]['name'], self.dummyReceiver['name'])

    @inlineCallbacks
    def test_put_invalid_context_gus(self):
        self.dummyReceiver['name'] = u'justalazyupdate'
        # keep the context_gus wrong but matching eventually regexp
        import uuid
        self.dummyReceiver['contexts'] = [ unicode(uuid.uuid4()) ]
        self.dummyReceiver['name'] = u'another unique name %d' % random.randint(1, 10000)
        self.dummyReceiver['notification_fields']['mail_address'] =\
            u'but%d@random.id' % random.randint(1, 1000)
        self.dummyReceiver['password'] = u'12345678andaletter'

        handler = self.request(self.dummyReceiver, role='admin')
        try:
            yield handler.put(self.dummyReceiver['receiver_gus'])
            self.assertTrue(False)
        except errors.ContextGusNotFound:
            self.assertTrue(True)
        except Exception as excep:
            print "Wrong exception: %s" % excep
            raise excep

    @inlineCallbacks
    def test_delete(self):
        handler = self.request(self.dummyReceiver, role='admin')
        try:
            yield handler.delete(self.dummyReceiver['receiver_gus'])
            self.assertTrue(True)
        except Exception as excep:
            print "Wrong exception: %s" % excep
            raise excep

        try:
            yield handler.get(self.dummyReceiver['receiver_gus'])
            self.assertTrue(False)
        except errors.ReceiverGusNotFound:
            self.assertTrue(True)


class TestAdminStaticFile(helpers.TestHandler):
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

    def test_asf_reserved_name_check(self):

        self.assertRaises(errors.InvalidInputFormat,
                          admstaticfiles.reserved_name_check,
                          u'86a4ffc4-26d4-4942-a3bd-9fc1f5d48453', 'whatever.tiff')
        self.assertRaises(errors.ReservedFileName,
                          admstaticfiles.reserved_name_check,
                          u'globaleaks_logo_FxHtHA_$RANDOM(³³³)', 'something_plausible.png')

        self.assertTrue( admstaticfiles.reserved_name_check('custom_stylesheet', 'myfunnycolors.css') )
        self.assertTrue( admstaticfiles.reserved_name_check('globaleaks_logo', 'something.jpg') )
        self.assertTrue( admstaticfiles.reserved_name_check('86a4ffc4-26d4-4942-a3bd-9fc1f5d48453',
                                                            'whatever.jpeg' ) )

        self.assertFalse( admstaticfiles.reserved_name_check('dirty_random_crap', 'ignored') )


    @inlineCallbacks
    def test_get(self):

        fakeFile = dict()
        fakeFile['body'] = StringIO()
        fakeFile['body'].write(TestAdminStaticFile.crappyjunk)
        fakeFile['body_len'] = len(TestAdminStaticFile.crappyjunk)
        fakeFile['content_type'] = 'image/jpeg'
        fakeFile['filename'] = 'imag0005.jpg'

        realpath = os.path.join(GLSetting.static_path, "ouffff")
        dumped_file = yield admstaticfiles.dump_static_file(fakeFile, realpath)
        self.assertTrue(dumped_file.has_key('filelocation'))

        handler = self.request(role='admin')
        yield handler.get()
        self.assertTrue( isinstance(self.responses[0], list) )
