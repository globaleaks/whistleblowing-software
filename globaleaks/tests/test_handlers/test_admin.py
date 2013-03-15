from twisted.internet.defer import inlineCallbacks

from globaleaks.rest.errors import InvalidInputFormat
from globaleaks.tests import helpers
from globaleaks.rest import errors
from globaleaks.handlers import admin
from globaleaks.settings import transact

# special guest:
from globaleaks.models import Notification

class TestNodeInstance(helpers.TestHandler):
    _handler = admin.NodeInstance

    def test_get(self):
        handler = self.request(role='admin')
        return handler.get()

    @inlineCallbacks
    def test_put_update_node(self):
        self.dummyNode['hidden_service'] = 'abcdef1234567890.onion'
        self.dummyNode['public_site'] = 'http://blogleaks.blogspot.com'

        handler = self.request(self.dummyNode, role='admin')
        yield handler.put()

        del self.dummyNode['password']
        del self.dummyNode['old_password']
        del self.responses[0]['last_update']

        self.assertEqual(self.responses[0], self.dummyNode)


    @inlineCallbacks
    def test_put_update_node_invalid_hidden(self):
        self.dummyNode['hidden_service'] = 'www.scroogle.com'
        self.dummyNode['public_site'] = 'http://blogleaks.blogspot.com'

        handler = self.request(self.dummyNode, role='admin')
        try:
            yield handler.put()
            self.assertTrue(False)
        except InvalidInputFormat:
            self.assertTrue(True)

    @inlineCallbacks
    def test_put_update_node_invalid_public(self):
        self.dummyNode['hidden_service'] = 'acdef1234567890.onion'
        self.dummyNode['public_site'] = 'blogleaks.blogspot.com'

        handler = self.request(self.dummyNode, role='admin')
        try:
            yield handler.put()
            self.assertTrue(False)
        except InvalidInputFormat:
            self.assertTrue(True)


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
        request_context = self.dummyContext
        del request_context['contexts'] # why is here !?
        handler = self.request(request_context, role='admin')
        yield handler.post()

        request_context['context_gus'] =  self.responses[0]['context_gus']
        del self.responses[0]['creation_date']
        del request_context['creation_date']
        self.assertEqual(self.responses[0], request_context)

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
        request_context = self.dummyContext
        request_context['name'] = u'spam'
        del request_context['contexts'] # I don't know what's doing here!!?
        handler = self.request(request_context, role='admin')
        yield handler.put(request_context['context_gus'])
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
        handler = self.request(self.dummyReceiver, role='admin')

        try:
            yield handler.post()
            self.assertTrue(False)
        except errors.NoEmailSpecified:
            self.assertTrue(True)
        except Exception, e:
            self.assertTrue(False)
            raise e

    @inlineCallbacks
    def test_post_duplicated_username(self):
        self.dummyReceiver['name'] = 'beppe'
        self.dummyReceiver['notification_fields']['mail_address'] = "vecna@hellais.naif"
        handler = self.request(self.dummyReceiver, role='admin')

        try:
            yield handler.post()
            yield handler.post() # duplication here!
            self.assertTrue(False)
        except errors.InvalidInputFormat:
            self.assertTrue(True)
        except Exception, e:
            self.assertTrue(False)


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
    def test_put(self):
        self.dummyReceiver['context_gus'] = ''
        del self.dummyReceiver['username']
        self.dummyReceiver['name'] = u'new name'
        handler = self.request(self.dummyReceiver, role='admin')
        yield handler.put(self.dummyReceiver['receiver_gus'])
        self.assertEqual(self.responses[0]['name'], self.dummyReceiver['name'])

    @inlineCallbacks
    def test_put_invalid_context_gus(self):
        self.dummyReceiver['name'] = u'justalazyupdate'
        # keep the context_gus wrong but matching eventually regexp
        import uuid
        self.dummyReceiver['contexts'] = [ unicode(uuid.uuid4()) ]
        handler = self.request(self.dummyReceiver, role='admin')
        # I've some issue in use assertRaises with 'yield', then:
        try:
            yield handler.put(self.dummyReceiver['receiver_gus'])
            self.assertTrue(False)
        except errors.ContextGusNotFound:
            self.assertTrue(True)

    @inlineCallbacks
    def test_delete(self):
        handler = self.request(self.dummyReceiver, role='admin')
        try:
            yield handler.delete(self.dummyReceiver['receiver_gus'])
            self.assertTrue(True)
        except Exception, e:
            self.assertTrue(False)
        try:
            yield handler.get(self.dummyReceiver['receiver_gus'])
            self.assertTrue(False)
        except errors.ReceiverGusNotFound:
            self.assertTrue(True)

