import random
from twisted.internet.defer import inlineCallbacks

from globaleaks.rest.errors import InvalidInputFormat
from globaleaks.tests import helpers
from globaleaks.rest import errors
from globaleaks.handlers import admin
from globaleaks.settings import transact
from globaleaks.utils import log

# special guest:
from globaleaks.models import Notification

class TestNodeInstance(helpers.TestHandler):
    _handler = admin.NodeInstance

    def test_get(self):
        handler = self.request(role='admin')
        return handler.get()

    @inlineCallbacks
    def test_put_update_node(self):
        self.dummyNode['hidden_service'] = 'http://abcdef1234567890.onion'
        self.dummyNode['public_site'] = 'http://blogleaks.blogspot.com'

        handler = self.request(self.dummyNode, role='admin')
        yield handler.put()

        self.dummyNode['creation_date'] = self.responses[0]['creation_date']
        self.dummyNode['last_update'] = self.responses[0]['last_update']
        del self.dummyNode['password']
        del self.dummyNode['old_password']
        del self.dummyNode['salt']
        del self.dummyNode['salt_receipt']
        del self.responses[0]['version']

        self.assertEqual(self.responses[0], self.dummyNode)

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
            print "Wrong exception: %s" % excep
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
        notification.tip_template = "my dummy template %s:w"
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
        del self.dummyContext['contexts'] # why is here !?
        self.dummyContext['name'] = "a random one to avoid dup %d" % random.randint(1, 1000)

        handler = self.request(self.dummyContext, role='admin')
        yield handler.post()

        self.dummyContext['context_gus'] =  self.responses[0]['context_gus']
        self.dummyContext['creation_date'] = self.responses[0]['creation_date']
        self.assertEqual(self.responses[0], self.dummyContext)

    @inlineCallbacks
    def test_invalid_duplicated_context_name(self):
        del self.dummyContext['contexts']
        self.dummyContext['name'] = u'a random name %d, but' % random.randint(1,1000)

        handler = self.request(self.dummyContext, role='admin')

        try:
            yield handler.post()
            yield handler.post() # duplication happen here
            self.assertTrue(False)
        except errors.ExpectedUniqueField:
            self.assertTrue(True)
        except Exception as excep:
            print "Wrong exception: %s" % excep
            raise excep


class TestContextInstance(helpers.TestHandler):
    _handler = admin.ContextInstance

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        yield handler.get(self.dummyContext['context_gus'])
        del self.dummyContext['contexts']
        self.assertEqual(self.responses[0], self.dummyContext)

    @inlineCallbacks
    def test_put(self):
        self.dummyContext['description'] = u'how many readers remind of HIMEM.SYS?'
        del self.dummyContext['contexts'] # I don't know what's doing here!!?
        handler = self.request(self.dummyContext, role='admin')
        yield handler.put(self.dummyContext['context_gus'])
        self.dummyContext['creation_date'] = self.responses[0]['creation_date']
        self.dummyContext['last_update'] = self.responses[0]['last_update']
        self.assertEqual(self.responses[0], self.dummyContext)


class TestReceiversCollection(helpers.TestHandler):
    _handler = admin.ReceiversCollection

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        yield handler.get()

        # XXX helpers.py.. Why self.responses is became a double array ?
        del self.dummyReceiver['contexts']
        del self.responses[0][0]['contexts']
        self.assertEqual(self.responses[0][0], self.dummyReceiver)

    @inlineCallbacks
    def test_post(self):
        self.dummyReceiver['name'] = 'beppe'

        # this is required because helpers is creating a new receiver
        new_email = "guy@globaleaks.xxx"
        self.dummyReceiver['notification_fields']['mail_address'] = new_email
        self.dummyReceiver['password'] = u'newcreatedpassword'

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
        self.dummyReceiver['password'] = u'newcreatedpassword'

        handler = self.request(self.dummyReceiver, role='admin')

        try:
            yield handler.post()
            self.assertTrue(False)
        except errors.NoEmailSpecified:
            self.assertTrue(True)
        except Exception as excep:
            print "Wrong exception: %s" % excep
            raise excep

    @inlineCallbacks
    def test_post_duplicated_username(self):
        self.dummyReceiver['name'] = 'beppe'
        self.dummyReceiver['notification_fields']['mail_address'] = "evilamaker.py@vecllais.naif"
        self.dummyReceiver['password'] = u'newcreatedpassword'
        handler = self.request(self.dummyReceiver, role='admin')

        try:
            yield handler.post()
            yield handler.post() # duplication here!
            self.assertTrue(False)
        except errors.ExpectedUniqueField:
            self.assertTrue(True)
        except Exception as excep:
            print "Wrong exception: %s" % excep
            raise excep


class TestReceiverInstance(helpers.TestHandler):
    _handler = admin.ReceiverInstance

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        yield handler.get(self.dummyReceiver['receiver_gus'])
        del self.dummyReceiver['contexts']
        del self.responses[0]['contexts']
        self.assertEqual(self.responses[0], self.dummyReceiver)

    @inlineCallbacks
    def test_put_change_password(self):
        self.dummyReceiver['context_gus'] = ''
        del self.dummyReceiver['username']
        self.dummyReceiver['name'] = u'new unique name %d' % random.randint(1, 10000)
        self.dummyReceiver['notification_fields']['mail_address'] = \
            u'but%d@random.id' % random.randint(1, 1000)
        self.dummyReceiver['password'] = u'12345678'

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
        self.dummyReceiver['password'] = u'12345678'

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

