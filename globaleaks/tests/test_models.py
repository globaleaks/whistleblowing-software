from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers

from globaleaks.models import *
from globaleaks.settings import transact, transact_ro
from globaleaks.rest import errors
from globaleaks.utils.structures import Fields


class TestModels(helpers.TestGL):

    receiver_inc = 0

    @transact
    def context_add(self, store):
        c = self.localization_set(self.dummyContext, Context, 'en')
        context = Context(c)

        fo = Fields()
        fo.update_fields('en', self.dummyContext['fields'])
        fo.context_import(context)

        context.tags = self.dummyContext['tags']
        context.submission_timetolive = context.tip_timetolive = 1000
        context.description = context.name = \
            context.submission_disclaimer = \
            context.submission_introduction = {"en": u'Localized723'}
        store.add(context)
        return context.id

    @transact_ro
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
        r = self.localization_set(self.dummyReceiver_1, Receiver, 'en')
        receiver_user = User(self.dummyReceiverUser_1)
        receiver_user.last_login = self.dummyReceiverUser_1['last_login']

        receiver_user.username = str(
            self.receiver_inc) + self.dummyReceiver_1['mail_address']
        receiver_user.password = self.dummyReceiverUser_1['password']
        store.add(receiver_user)

        receiver = Receiver(r)
        receiver.user = receiver_user
        receiver.gpg_key_status = Receiver._gpg_types[0]
        receiver.mail_address = self.dummyReceiver_1['mail_address']

        store.add(receiver)

        self.receiver_inc += 1

        return receiver.id

    @transact_ro
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
        r = self.localization_set(self.dummyReceiver_1, Receiver, 'en')

        receiver_user1 = User(self.dummyReceiverUser_1)
        receiver_user1.last_login = self.dummyReceiverUser_1['last_login']

        receiver_user2 = User(self.dummyReceiverUser_1)
        receiver_user2.last_login = self.dummyReceiverUser_1['last_login']

        # Avoid receivers with the same username!
        receiver_user1.username = unicode("xxx")
        receiver_user2.username = unicode("yyy")

        store.add(receiver_user1)
        store.add(receiver_user2)

        context = Context(c)

        fo = Fields()
        fo.update_fields('en', self.dummyContext['fields'])
        fo.context_import(context)

        context.tags = self.dummyContext['tags']
        context.submission_timetolive = context.tip_timetolive = 1000
        context.description = context.name = \
            context.submission_disclaimer = \
            context.submission_introduction = {"en": u'Localized76w'}

        receiver1 = Receiver(r)
        receiver2 = Receiver(r)

        receiver1.user = receiver_user1
        receiver2.user = receiver_user2
        receiver1.gpg_key_status = receiver2.gpg_key_status = Receiver._gpg_types[
            0]
        receiver1.mail_address = receiver2.mail_address = 'x@x.it'

        context.receivers.add(receiver1)
        context.receivers.add(receiver2)

        store.add(context)

        return context.id

    @transact
    def create_receiver_with_contexts(self, store):
        c = self.localization_set(self.dummyContext, Context, 'en')
        r = self.localization_set(self.dummyReceiver_1, Receiver, 'en')

        receiver_user = User(self.dummyReceiverUser_1)
        receiver_user.last_login = self.dummyReceiverUser_1['last_login']

        # Avoid receivers with the same username!
        receiver_user.username = unicode("xxx")

        store.add(receiver_user)

        receiver = Receiver(r)
        receiver.user = receiver_user
        receiver.gpg_key_status = Receiver._gpg_types[0]
        receiver.mail_address = unicode('y@y.it')

        context1 = Context(c)

        fo = Fields()
        fo.update_fields('en', self.dummyContext['fields'])
        fo.context_import(context1)

        context1.tags = self.dummyContext['tags']
        context1.submission_timetolive = context1.tip_timetolive = 1000
        context1.description = context1.name = \
            context1.submission_disclaimer = \
            context1.submission_introduction = {"en": u'Valar Morghulis'}

        context2 = Context(c)

        fo.context_import(context2)

        context2.tags = self.dummyContext['tags']
        context2.submission_timetolive = context2.tip_timetolive = 1000
        context2.description = context2.name =\
            context2.submission_disclaimer = \
            context2.submission_introduction = {"en": u'Valar Dohaeris'}

        receiver.contexts.add(context1)
        receiver.contexts.add(context2)
        store.add(receiver)
        return receiver.id

    @transact_ro
    def list_receivers_of_context(self, store, context_id):
        context = store.find(Context, Context.id == context_id).one()
        receivers = []
        for receiver in context.receivers:
            receivers.append(receiver.id)
        return receivers

    @transact_ro
    def list_context_of_receivers(self, store, receiver_id):
        receiver = store.find(Receiver, Receiver.id == receiver_id).one()
        contexts = []
        for context in receiver.contexts:
            contexts.append(context.id)
        return contexts

    @transact
    def do_invalid_receiver_0length_name(self, store):
        self.dummyReceiver_1['name'] = ''
        Receiver(self.dummyReceiver_1)

    @transact
    def do_invalid_receiver_description_oversize(self, store):
        self.dummyReceiver_1['description'] = "A" * 5000
        Receiver(self.dummyReceiver_1)

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

    def test_invalid_receiver_description_oversize(self):
        self.assertFailure(self.do_invalid_receiver_description_oversize(),
                           errors.InvalidInputFormat)


class TestNextGenFields(helpers.TestGL):

    @transact
    def create_field(self, store):

        attrs = {
            'label': "{'en': 'test label'}",
            'description': "{'en': 'test description'}",
            'hint': "{'en': 'test hint'}",
            'multi_entry': False,
            'type': 'checkbox',
            'options': {},
            'required': False,
            'preview': False,
            'stats_enabled': True,
            'x': 0,
            'y': 0
        }

        return Field.new(store, attrs).id

    @transact
    def create_field_group(self, store):

        attrs = {
            'label': "{'en': 'test label'}",
            'description': "{'en': 'test description'}",
            'hint': "{'en': 'test hint'}",
            'multi_entry': False,
            'type': 'fieldgroup',
            'options': {},
            'required': False,
            'preview': False,
            'stats_enabled': True,
            'x': 0,
            'y': 0
        }

        return Field.new(store, attrs).id


    @transact
    def transact_field_delete(self, store, field_id):
        Field.delete(store, field_id)

    @inlineCallbacks
    def test_001_field_creation(self):
        field_id = yield self.create_field()
        exists = yield self._exists('Field', field_id)
        self.assertTrue(exists, "Field does not exist")

    @inlineCallbacks
    def test_002_delete_field(self):
        field_id = yield self.create_field()
        yield self.transact_field_delete(field_id)

        exists = yield self._exists('Field', field_id)
        self.assertFalse(exists, "Field still exists")

    @inlineCallbacks
    def test_003_field_group_creation(self):
        field_group_id = yield self.create_field_group()
        exists = yield self._exists('Field', field_group_id)
        self.assertTrue(exists, "Field does not exist")

    @inlineCallbacks
    def test_004_delete_field_group_with_children(self):
        field_id = yield self.create_field()
        field_group_id = yield self.create_field_group()

        yield self.transact_field_delete(field_group_id)


class TestComposingFields(helpers.TestGLWithPopulatedDB):
    fixtures = ['fields.json']


    @inlineCallbacks
    def setUp(self):
        yield super(TestComposingFields, self).setUp()

        self.birthdate_id = u"27121164-0d0f-4180-9e9c-b1f72e815105"
        self.name_id = u"25521164-0d0f-4f80-9e9c-93f72e815105"
        self.surname_id = u"25521164-1d0f-5f80-8e8c-93f73e815156"
        self.sex_id = u"98891164-1a0b-5b80-8b8b-93b73b815156"

        self.generalities_id = u"37242164-1b1f-1110-1e1c-b1f12e815105"

    @transact
    def transact_field_delete(self, store, field_id):
        Field.delete(store, field_id)

    @transact_ro
    def transact_get_children(self, store, field_id):
        field = Field.get(store, field_id)
        return [c.id for c in field.children]

    @inlineCallbacks
    def test_001_add_children(self):
        children = yield self.transact_get_children(self.generalities_id)
        self.assertIn(self.name_id, children)
        self.assertIn(self.birthdate_id, children)
        self.assertNotIn(self.surname_id, children)
        self.assertNotIn(self.sex_id, children)

        Field.add_children(self.generalities_id,
                                self.surname_id, self.sex_id)
        children = yield self.transact_get_children(self.generalities_id)
        self.assertIn(self.surname_id, children)
        self.assertIn(self.name_id, children)
        self.assertIn(self.sex_id, children)


    @inlineCallbacks
    def test_002_delete_field_child_of_a_group_should_succed(self):
        # Should fail with Exception and FieldGroup still present

        children = yield self.transact_get_children(self.generalities_id)

        for c in children:
            yield self.transact_field_delete(c)

    @inlineCallbacks
    def test_003_delete_field_group_with_children_should_succed(self):
        # Should fail with Exception and FieldGroup still present

        children = yield self.transact_get_children(self.generalities_id)

        for c in children:
            yield self.transact_field_delete(c)

        yield self.transact_field_delete(self.generalities_id)

    @inlineCallbacks
    def test_004_new_step(self):
        @transact
        def create_step(store, context_id, number):
            return Step.new(store, context_id, number, self.generalities_id)

        @transact
        def step_exists(store, context_id, step_id):
            return bool(Step.get(store, context_id, step_id))

        context_id = yield self.dummyContext['id']
        step_id = yield create_step(context_id, 0)
        self.assertTrue(step_exists(context_id, step_id))
