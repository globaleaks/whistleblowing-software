from __future__ import unicode_literals

from storm import exceptions
from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.rest import errors
from globaleaks.settings import transact, transact_ro
from globaleaks.tests import helpers

class TestModels(helpers.TestGL):
    receiver_inc = 0

    @transact
    def context_add(self, store):
        c = self.localization_set(self.dummyContext, models.Context, 'en')
        context = models.Context(c)

        context.tags = self.dummyContext['tags']
        context.submission_timetolive = context.tip_timetolive = 1000
        context.description = context.name = \
            context.submission_disclaimer = \
            context.submission_introduction = {'en': 'Localized723'}
        store.add(context)
        return context.id

    @transact_ro
    def context_get(self, store, context_id):
        context = models.Context.get(store, context_id)
        if context is None:
            return None
        return context.id

    @transact
    def context_del(self, store, context_id):
        context = models.Context.get(store, context_id)
        if context is not None:
            store.remove(context)

    @transact
    def receiver_add(self, store):
        r = self.localization_set(self.dummyReceiver_1, models.Receiver, 'en')
        receiver_user = models.User(self.dummyReceiverUser_1)
        receiver_user.last_login = self.dummyReceiverUser_1['last_login']

        receiver_user.username = str(
            self.receiver_inc) + self.dummyReceiver_1['mail_address']
        receiver_user.password = self.dummyReceiverUser_1['password']
        store.add(receiver_user)

        receiver = models.Receiver(r)
        receiver.user = receiver_user
        receiver.gpg_key_status = models.Receiver._gpg_types[0]
        receiver.mail_address = self.dummyReceiver_1['mail_address']

        store.add(receiver)

        self.receiver_inc += 1

        return receiver.id

    @transact_ro
    def receiver_get(self, store, receiver_id):
        receiver = models.Receiver.get(store, receiver_id)
        if receiver is None:
            return None
        return receiver.id

    @transact
    def receiver_del(self, store, receiver_id):
        receiver = models.Receiver.get(store, receiver_id)
        if receiver is not None:
            store.remove(receiver)

    @transact
    def create_context_with_receivers(self, store):
        c = self.localization_set(self.dummyContext, models.Context, 'en')
        r = self.localization_set(self.dummyReceiver_1, models.Receiver, 'en')

        receiver_user1 = models.User(self.dummyReceiverUser_1)
        receiver_user1.last_login = self.dummyReceiverUser_1['last_login']

        receiver_user2 = models.User(self.dummyReceiverUser_1)
        receiver_user2.last_login = self.dummyReceiverUser_1['last_login']

        # Avoid receivers with the same username!
        receiver_user1.username = 'xxx'
        receiver_user2.username = 'yyy'

        store.add(receiver_user1)
        store.add(receiver_user2)

        context = models.Context(c)

        context.tags = self.dummyContext['tags']
        context.submission_timetolive = context.tip_timetolive = 1000
        context.description = context.name = \
            context.submission_disclaimer = \
            context.submission_introduction = {'en': 'Localized76w'}

        receiver1 = models.Receiver(r)
        receiver2 = models.Receiver(r)

        receiver1.user = receiver_user1
        receiver2.user = receiver_user2
        receiver1.gpg_key_status = models.Receiver._gpg_types[0]
        receiver2.gpg_key_status = models.Receiver._gpg_types[0]
        receiver1.mail_address = 'x@x.it'
        receiver2.mail_address = 'x@x.it'

        context.receivers.add(receiver1)
        context.receivers.add(receiver2)

        store.add(context)

        return context.id

    @transact
    def create_receiver_with_contexts(self, store):
        c = self.localization_set(self.dummyContext, models.Context, 'en')
        r = self.localization_set(self.dummyReceiver_1, models.Receiver, 'en')

        receiver_user = models.User(self.dummyReceiverUser_1)
        receiver_user.last_login = self.dummyReceiverUser_1['last_login']
        # Avoid receivers with the same username!
        receiver_user.username = u'xxx'
        store.add(receiver_user)

        receiver = models.Receiver(r)
        receiver.user = receiver_user
        receiver.gpg_key_status = models.Receiver._gpg_types[0]
        receiver.mail_address = unicode('y@y.it')

        context1 = models.Context(c)

        context1.tags = self.dummyContext['tags']
        context1.submission_timetolive = context1.tip_timetolive = 1000
        context1.description = context1.name = \
            context1.submission_disclaimer = \
            context1.submission_introduction = {'en': 'Valar Morghulis'}

        context2 = models.Context(c)

        context2.tags = self.dummyContext['tags']
        context2.submission_timetolive = context2.tip_timetolive = 1000
        context2.description = context2.name =\
            context2.submission_disclaimer = \
            context2.submission_introduction = {'en': 'Valar Dohaeris'}

        receiver.contexts.add(context1)
        receiver.contexts.add(context2)
        store.add(receiver)
        return receiver.id

    @transact_ro
    def list_receivers_of_context(self, store, context_id):
        context = models.Context.get(store, context_id)
        receivers = []
        for receiver in context.receivers:
            receivers.append(receiver.id)
        return receivers

    @transact_ro
    def list_context_of_receivers(self, store, receiver_id):
        """
        Return the list of context ids associated with the receiver identified
        by receiver_id.
        """
        receiver = models.Receiver.get(store, receiver_id)
        return [context.id for context in receiver.contexts]

    @transact
    def do_invalid_receiver_0length_name(self, store):
        self.dummyReceiver_1['name'] = ''
        r = models.Receiver(self.dummyReceiver_1)
        store.add(r)

    @transact
    def do_invalid_receiver_description_oversize(self, store):
        self.dummyReceiver_1['description'] = 'A' * 5000
        models.Receiver(self.dummyReceiver_1)
        store.add(r)

    @inlineCallbacks
    def test_context_add_and_get(self):
        context_id = yield self.context_add()
        context_id = yield self.context_get(context_id)
        self.assertIsNotNone(context_id)

    @inlineCallbacks
    def test_context_add_and_del(self):
        context_id = yield self.context_add()
        yield self.context_del(context_id)
        context_id = yield self.context_get(context_id)
        self.assertIsNone(context_id)

    @inlineCallbacks
    def test_receiver_add_and_get(self):
        receiver_id = yield self.receiver_add()
        receiver_id = yield self.receiver_get(receiver_id)
        self.assertIsNotNone(receiver_id)

    @inlineCallbacks
    def test_receiver_add_and_del(self):
        receiver_id = yield self.receiver_add()
        yield self.receiver_del(receiver_id)
        receiver_id = yield self.receiver_get(receiver_id)
        self.assertIsNone(receiver_id)

    @inlineCallbacks
    def test_context_receiver_reference_1(self):
        context_id = yield self.create_context_with_receivers()
        yield self.assert_model_exists(models.Context, context_id)
        receivers = yield self.list_receivers_of_context(context_id)
        self.assertEqual(2, len(receivers))

    @inlineCallbacks
    def test_context_receiver_reference_2(self):
        receiver_id = yield self.create_receiver_with_contexts()
        yield self.assert_model_exists(models.Receiver, receiver_id)
        contexts = yield self.list_context_of_receivers(receiver_id)
        self.assertEqual(2, len(contexts))

    def test_invalid_receiver_0length_name(self):
        self.assertFailure(self.do_invalid_receiver_0length_name(),
                           errors.InvalidInputFormat)

    def test_invalid_receiver_description_oversize(self):
        self.assertFailure(self.do_invalid_receiver_description_oversize(),
                           errors.InvalidInputFormat)


@transact
def create_field(store, **custom_attrs):
    attrs = {
        'label': '{"en": "test label"}',
        'description': '{"en": "test description"}',
        'hint': '{"en": "test hint"}',
        'multi_entry': False,
        'type': 'fieldgroup',
        'options': {},
        'required': False,
        'preview': False,
        'stats_enabled': True,
        'x': 0,
        'y': 0
    }
    attrs.update(custom_attrs)
    return models.Field.new(store, attrs).id

class TestField(helpers.TestGL):
    fixtures = ['fields.json']

    @inlineCallbacks
    def setUp(self):
        yield super(TestField, self).setUp()

        self.birthdate_id = '27121164-0d0f-4180-9e9c-b1f72e815105'
        self.name_id = '25521164-0d0f-4f80-9e9c-93f72e815105'
        self.surname_id = '25521164-1d0f-5f80-8e8c-93f73e815156'
        self.sex_id = '98891164-1a0b-5b80-8b8b-93b73b815156'
        self.generalities_id = '37242164-1b1f-1110-1e1c-b1f12e815105'

    @transact
    def field_delete(self, store, field_id):
        models.Field.get(store, field_id).delete(store)

    @transact
    def add_children(self, store, field_id, *field_ids):
        parent = models.Field.get(store, field_id)
        for field_id in field_ids:
            field = models.Field.get(store, field_id)
            parent.children.add(field)

    @transact_ro
    def get_children(self, store, field_id):
        field = models.Field.get(store, field_id)
        return [c.id for c in field.children]

    @inlineCallbacks
    def test_add_field(self):
        field_id = yield create_field()
        yield self.assert_model_exists(models.Field, field_id)

        field_id = yield create_field(type='checkbox')
        yield self.assert_model_exists(models.Field, field_id)

    @inlineCallbacks
    def test_add_field_group(self):
        field1_id = yield create_field(
            label='{"en": "the first testable field"}',
            type='checkbox'
        )
        field2_id = yield create_field(
            label='{"en": "the second testable field"}',
            type='inputbox'
        )
        fieldgroup_id = yield create_field(
            label='{"en": "a testable group of fields."}',
            type='fieldgroup',
            x=1, y=2,
        )
        yield self.assert_model_exists(models.Field, fieldgroup_id)
        yield self.assert_model_exists(models.Field, field2_id)
        yield self.add_children(fieldgroup_id, field1_id, field2_id)
        fieldgroup_children = yield self.get_children(fieldgroup_id)
        self.assertIn(field1_id, fieldgroup_children)
        self.assertIn(field2_id, fieldgroup_children)

    @inlineCallbacks
    def test_delete_field_child(self):
        children = yield self.get_children(self.generalities_id)
        for c in children:
            yield self.field_delete(c)

        children = yield self.get_children(self.generalities_id)
        self.assertEqual(len(children), 0)

    @inlineCallbacks
    def test_delete_field_group(self):
        children = yield self.get_children(self.generalities_id)
        self.assertGreater(len(children), 0)

        yield self.field_delete(self.generalities_id)
        yield self.assert_model_not_exists(models.Field, self.generalities_id)


class TestStep(helpers.TestGL):
    #skip = ('"test_gl_with_populated_db.json" must be updated'
    #        'in order to run this test.')
    fixtures = ['fields.json', "test_gl_with_populated_db.json"]

    @inlineCallbacks
    def setUp(self):
        from globaleaks import db
        yield db.create_tables(create_node=False)
        from globaleaks.settings import GLSetting
        GLSetting.bind_addresses = ['localhost']
        GLSetting.set_devel_mode()
        GLSetting.logging = None
        #GLSetting.scheduler_threadpool = FakeThreadPool()
        GLSetting.memory_copy.allow_unencrypted = True
        GLSetting.sessions = {}
        GLSetting.failed_login_attempts = 0
        GLSetting.working_path = './working_path'
        GLSetting.ramdisk_path = './working_path/ramdisk'
        GLSetting.eval_paths()
        GLSetting.remove_directories()
        GLSetting.create_directories()
        self.generalities_id = '37242164-1b1f-1110-1e1c-b1f12e815105'
        self.context_id = '34948a37-201e-44e0-bede-67212f1b7ee6'
        yield super(TestStep, self).setUp(create_node=False)

    @transact
    def create_step(self, store, context_id, field_id):
        step = {
          'context_id': context_id,
          'number': 1,
          'label': "",
          'description': "",
          'hint': ""
        }

        step = models.Step.new(store, step)
        field = models.Field.get(store, field_id)
        step.children.add(field)
        return step.id

    @inlineCallbacks
    def test_new(self):
        # tabula rasa elettrificata
        # https://www.youtube.com/watch?v=1kGQaE3OFoI
        steps = yield transact(lambda store: store.find(models.Step).is_empty())()
        self.assertTrue(steps)

        step1 = yield self.create_step(self.context_id, self.generalities_id)
        yield self.assert_model_exists(models.Step, step1)
        # creation of another step with same context and fieldgroup shall fail.
        self.assertFailure(self.create_step(self.context_id, self.generalities_id),
                           exceptions.IntegrityError)
        # creation of another step bindded to the same context and different
        # fieldgroup shall succeed.
        second_fieldgroup = yield create_field(type='fieldgroup')
        step2 = yield self.create_step(self.context_id, second_fieldgroup)
        yield self.assert_model_exists(models.Step, step2)
