from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers

from globaleaks.models import *
from globaleaks.settings import transact
from globaleaks.rest import errors

class TestModels(helpers.TestGL):

    receiver_inc = 0

    @transact
    def context_add(self, store):
        c = self.localization_set(self.dummyContext, Context, 'en')
        context = Context(c)
        context.fields = self.dummyContext['fields']
        context.tags = self.dummyContext['tags']
        context.submission_timetolive = context.tip_timetolive = 1000
        context.description = context.name = \
            context.submission_disclaimer = context.submission_introduction = \
            context.receipt_description = { "en" : u'Localized723' }
        context.receipt_regexp = u"unipop547"
        store.add(context)
        return context.id

    @transact
    def context_get(self, store, context_id):
        context = store.find(Context, Context.id == context_id).one()
        if context is None:
            return None
        return context.id

    @transact
    def context_del(self, store, context_id):
        context = store.find(Context, Context.id == context_id).one()
        if context is not None:
            store.remove(context)

    @transact
    def receiver_add(self, store):
        r = self.localization_set(self.dummyReceiver, Receiver, 'en')
        receiver_user = User(self.dummyReceiverUser)
        receiver_user.last_login = self.dummyReceiverUser['last_login']

        receiver_user.username = str(self.receiver_inc) + self.dummyReceiver['notification_fields']['mail_address']
        receiver_user.password = self.dummyReceiverUser['password']
        store.add(receiver_user)

        receiver = Receiver(r)
        receiver.user = receiver_user
        receiver.gpg_key_status = Receiver._gpg_types[0]
        receiver.notification_fields = self.dummyReceiver['notification_fields']

        store.add(receiver)

        self.receiver_inc = self.receiver_inc + 1

        return receiver.id

    @transact
    def receiver_get(self, store, receiver_id):
        receiver = store.find(Receiver, Receiver.id == receiver_id).one()
        if receiver is None:
            return None
        return receiver.id

    @transact
    def receiver_del(self, store, receiver_id):
        receiver = store.find(Receiver, Receiver.id == receiver_id).one()
        if receiver is not None:
            store.remove(receiver)

    @transact
    def create_context_with_receivers(self, store):
        c = self.localization_set(self.dummyContext, Context, 'en')
        r = self.localization_set(self.dummyReceiver, Receiver, 'en')

        receiver_user1 = User(self.dummyReceiverUser)
        receiver_user1.last_login = self.dummyReceiverUser['last_login']

        receiver_user2 = User(self.dummyReceiverUser)
        receiver_user2.last_login = self.dummyReceiverUser['last_login']

        # Avoid receivers with the same username!
        receiver_user1.username = unicode("xxx")
        receiver_user2.username = unicode("yyy")

        store.add(receiver_user1)
        store.add(receiver_user2)

        context = Context(c)
        context.fields = self.dummyContext['fields']
        context.fields = self.dummyContext['fields']
        context.tags = self.dummyContext['tags']
        context.submission_timetolive = context.tip_timetolive = 1000
        context.description = context.name =\
            context.submission_disclaimer = context.submission_introduction =\
            context.receipt_description = { "en" : u'Localized76w' }
        context.receipt_regexp = u"unipop09876"

        receiver1 = Receiver(r)
        receiver2 = Receiver(r)

        receiver1.user = receiver_user1
        receiver2.user = receiver_user2
        receiver1.gpg_key_status = receiver2.gpg_key_status = Receiver._gpg_types[0]
        receiver1.notification_fields = receiver2.notification_fields = {'mail_address': 'x@x.it'}

        context.receivers.add(receiver1)
        context.receivers.add(receiver2)

        store.add(context)

        return context.id

    @transact
    def create_receiver_with_contexts(self, store):
        c = self.localization_set(self.dummyContext, Context, 'en')
        r = self.localization_set(self.dummyReceiver, Receiver, 'en')

        receiver_user = User(self.dummyReceiverUser)
        receiver_user.last_login = self.dummyReceiverUser['last_login']

        # Avoid receivers with the same username!
        receiver_user.username = unicode("xxx")

        store.add(receiver_user)

        receiver = Receiver(r)
        receiver.user = receiver_user
        receiver.gpg_key_status = Receiver._gpg_types[0]
        receiver.notification_fields = {'mail_address': 'y@y.it'}

        context1 = Context(c)
        context1.fields = self.dummyContext['fields']
        context1.tags = self.dummyContext['tags']
        context1.submission_timetolive = context1.tip_timetolive = 1000
        context1.description = context1.name =\
            context1.submission_disclaimer = context1.submission_introduction =\
            context1.receipt_description = { "en" : u'Valar Morghulis' }
        context1.receipt_regexp = u"unipop254"

        context2 = Context(c)
        context2.fields = self.dummyContext['fields']
        context2.tags = self.dummyContext['tags']
        context2.submission_timetolive = context2.tip_timetolive = 1000
        context2.description = context2.name =\
            context2.submission_disclaimer = context2.submission_introduction =\
            context2.receipt_description = { "en" : u'Valar Dohaeris' }
        context2.receipt_regexp = u"unipop43423"

        receiver.contexts.add(context1)
        receiver.contexts.add(context2)
        store.add(receiver)
        return receiver.id

    @transact
    def list_receivers_of_context(self, store, context_id):
        context = store.find(Context, Context.id == context_id).one()
        receivers = []
        for receiver in context.receivers:
            receivers.append(receiver.id)
        return receivers

    @transact
    def list_context_of_receivers(self, store, receiver_id):
        receiver = store.find(Receiver, Receiver.id == receiver_id).one()
        contexts = []
        for context in receiver.contexts:
            contexts.append(context.id)
        return contexts

    @transact
    def do_invalid_receiver_0length_name(self, store):
        self.dummyReceiver['name'] = ''
        Receiver(self.dummyReceiver)

    @transact
    def do_invalid_description_oversize(self, store):
        self.dummyReceiver['description'] = "A" * 5000
        try:
            Receiver(self.dummyReceiver)
            return False
        except TypeError:
            return True

    @inlineCallbacks
    def test_context_add_and_get(self):
        context_id = yield self.context_add()
        context_id = yield self.context_get(context_id)
        self.assertTrue(context_id is not None)

    @inlineCallbacks
    def test_context_add_and_del(self):
        context_id = yield self.context_add()
        yield self.context_del(context_id)
        context_id = yield self.context_get(context_id)
        self.assertTrue(context_id is None)

    @inlineCallbacks
    def test_receiver_add_and_get(self):
        receiver_id = yield self.receiver_add()
        receiver_id = yield self.receiver_get(receiver_id)
        self.assertTrue(receiver_id is not None)

    @inlineCallbacks
    def test_receiver_add_and_del(self):
        receiver_id = yield self.receiver_add()
        yield self.receiver_del(receiver_id)
        receiver_id = yield self.receiver_get(receiver_id)
        self.assertTrue(receiver_id is None)

    @inlineCallbacks
    def test_context_receiver_reference_1(self):
        context_id = yield self.create_context_with_receivers()
        receivers = yield self.list_receivers_of_context(context_id)
        self.assertEqual(2, len(receivers))

    @inlineCallbacks
    def test_context_receiver_reference_2(self):
        receiver_id = yield self.create_receiver_with_contexts()
        contexts = yield self.list_context_of_receivers(receiver_id)
        self.assertEqual(2, len(contexts))

    def test_invalid_receiver_0length_name(self):
        self.assertFailure(self.do_invalid_receiver_0length_name(),
                errors.InvalidInputFormat)

    def test_invalid_description_oversize(self):
        self.assertFailure(self.do_invalid_receiver_0length_name(),
                errors.InvalidInputFormat)
