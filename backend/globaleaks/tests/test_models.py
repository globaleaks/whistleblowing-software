# -*- coding: utf-8 -*-

from globaleaks import models, LANGUAGES_SUPPORTED
from globaleaks.models import config
from globaleaks.models.config_desc import GLConfig
from globaleaks.models.l10n import NodeL10NFactory, EnabledLanguage, ConfigL10N
from globaleaks.orm import transact
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestSystemConfigModels(helpers.TestGL):
    @inlineCallbacks
    def test_config_import(self):
        yield self._test_config_import()

    @transact
    def _test_config_import(self, store):
        c = store.find(config.Config).count()

        stated_conf = reduce(lambda x,y: x+y, [len(v) for k, v in GLConfig.iteritems()], 0)
        self.assertEqual(c, stated_conf)

    @inlineCallbacks
    def test_valid_config(self):
        yield self._test_valid_cfg()

    @transact
    def _test_valid_cfg(self, store):
        self.assertEqual(True, config.is_cfg_valid(store))

    @inlineCallbacks
    def test_missing_config(self):
        yield self._test_missing_config()

    @transact
    def _test_missing_config(self, store):
        self.assertEqual(True, config.is_cfg_valid(store))

        p = config.Config('private', 'smtp_password', 'XXXX')
        p.var_group = u'outside'
        store.add(p)

        self.assertEqual(False, config.is_cfg_valid(store))

        node = config.NodeFactory(store)
        c = node.get_cfg('hostname')
        store.remove(c)
        store.commit()

        self.assertEqual(False, node.db_corresponds())

        # Delete all of the vars in Private Factory
        prv = config.PrivateFactory(store)

        store.execute('DELETE FROM config WHERE var_group = "private"')

        self.assertEqual(False, prv.db_corresponds())

        ntfn = config.NotificationFactory(store)

        c = config.Config('notification', 'server', 'guarda.giochi.con.occhi')
        c.var_name = u'anextravar'
        store.add(c)

        self.assertEqual(False, ntfn.db_corresponds())

        config.update_defaults(store)

        self.assertEqual(True, config.is_cfg_valid(store))


class TestConfigL10N(helpers.TestGL):
    @inlineCallbacks
    def test_config_l10n_init(self):
        yield self.run_node_mgr()

    @transact
    def run_node_mgr(self, store):
        # Initialize the Node manager
        node_l10n = NodeL10NFactory(store)
        num_trans = len(NodeL10NFactory.localized_keys)

        # Make a query with the Node manager
        ret = node_l10n.retrieve_rows('en')

        self.assertTrue(len(ret) == num_trans)

    @inlineCallbacks
    def test_enabled_langs(self):
        yield self.enable_langs()

    @transact
    def enable_langs(self, store):
        res = EnabledLanguage.list(store)

        self.assertTrue(u'en' in res)
        self.assertTrue(len(res) == len(LANGUAGES_SUPPORTED))

        c = store.find(ConfigL10N).count()
        self.assertTrue(1500 < c < 2300)

    @inlineCallbacks
    def test_disable_langs(self):
        yield self.disable_langs()

    @transact
    def disable_langs(self, store):
        c = len(EnabledLanguage.list(store))
        i = store.find(ConfigL10N).count()
        n = i/c

        EnabledLanguage.remove_old_langs(store, [u'en'])

        c_f = len(EnabledLanguage.list(store))
        i_f = store.find(ConfigL10N).count()

        self.assertTrue(i-i_f == n and c_f == c-1)


class TestModels(helpers.TestGL):
    receiver_inc = 0

    @transact
    def context_add(self, store):
        c = self.localization_set(self.dummyContext, models.Context, 'en')
        context = models.Context(c)
        context.questionnaire_id = u'default'
        context.tip_timetolive = 1000
        context.description = context.name = \
            context.submission_disclaimer = \
            context.submission_introduction = {'en': 'Localized723'}
        store.add(context)
        return context.id

    @transact
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
        u = self.localization_set(self.dummyReceiverUser_1, models.User, 'en')
        receiver_user = models.User(u)
        receiver_user.mail_address = self.dummyReceiverUser_1['mail_address']
        receiver_user.username = str(
            self.receiver_inc) + self.dummyReceiver_1['mail_address']
        receiver_user.password = self.dummyReceiverUser_1['password']
        receiver_user.salt = self.dummyReceiverUser_1['salt']
        store.add(receiver_user)

        r = self.localization_set(self.dummyReceiver_1, models.Receiver, 'en')
        receiver = models.Receiver(r)
        receiver.user = receiver_user
        receiver.user.pgp_key_expiration = "1970-01-01 00:00:00.000000"
        receiver.user.pgp_key_fingerprint = ""
        receiver.user.pgp_key_public = ""

        receiver.mail_address = self.dummyReceiver_1['mail_address']

        store.add(receiver)

        self.receiver_inc += 1

        return receiver.id

    @transact
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
        u1 = self.localization_set(self.dummyReceiverUser_1, models.User, 'en')
        receiver_user1 = models.User(u1)
        receiver_user1.password = self.dummyReceiverUser_1['password']
        receiver_user1.salt = self.dummyReceiverUser_1['salt']

        u2 = self.localization_set(self.dummyReceiverUser_2, models.User, 'en')
        receiver_user2 = models.User(u2)
        receiver_user2.password = self.dummyReceiverUser_2['password']
        receiver_user2.salt = self.dummyReceiverUser_2['salt']

        store.add(receiver_user1)
        store.add(receiver_user2)

        c = self.localization_set(self.dummyContext, models.Context, 'en')
        context = models.Context(c)
        context.questionnaire_id = u'default'
        context.tip_timetolive = 1000
        context.description = context.name = \
            context.submission_disclaimer = \
            context.submission_introduction = {'en': 'Localized76w'}

        r1 = self.localization_set(self.dummyReceiver_1, models.Receiver, 'en')
        r2 = self.localization_set(self.dummyReceiver_2, models.Receiver, 'en')
        receiver1 = models.Receiver(r1)
        receiver2 = models.Receiver(r2)

        receiver1.user = receiver_user1
        receiver2.user = receiver_user2

        receiver1.user.pgp_key_expiration = "1970-01-01 00:00:00.000000"
        receiver1.user.pgp_key_fingerprint = ""
        receiver1.user.pgp_key_public = ""

        receiver2.user.pgp_key_expiration = "1970-01-01 00:00:00.000000"
        receiver2.user.pgp_key_fingerprint = ""
        receiver2.user.pgp_key_public = ""

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

        u = self.localization_set(self.dummyReceiverUser_1, models.User, 'en')
        receiver_user = models.User(u)
        # Avoid receivers with the same username!
        receiver_user.username = u'xxx'
        receiver_user.password = self.dummyReceiverUser_1['password']
        receiver_user.salt = self.dummyReceiverUser_1['salt']
        store.add(receiver_user)

        receiver = models.Receiver(r)
        receiver.user = receiver_user
        receiver.user.pgp_key_expiration = "1970-01-01 00:00:00.000000"
        receiver.user.pgp_key_fingerprint = ""
        receiver.user.pgp_key_public = ""
        receiver.mail_address = u'y@y.it'

        context1 = models.Context(c)
        context1.questionnaire_id = u'default'
        context1.tip_timetolive = 1000
        context1.description = context1.name = \
            context1.submission_disclaimer = \
            context1.submission_introduction = {'en': 'Valar Morghulis'}

        context2 = models.Context(c)
        context2.questionnaire_id = u'default'
        context2.tip_timetolive = 1000
        context2.description = context2.name = \
            context2.submission_disclaimer = \
            context2.submission_introduction = {'en': 'Valar Dohaeris'}

        receiver.contexts.add(context1)
        receiver.contexts.add(context2)
        store.add(receiver)
        return receiver.id

    @transact
    def list_receivers_of_context(self, store, context_id):
        context = models.Context.get(store, context_id)
        receivers = []
        for receiver in context.receivers:
            receivers.append(receiver.id)
        return receivers

    @transact
    def list_context_of_receivers(self, store, receiver_id):
        """
        Return the list of context ids associated with the receiver identified
        by receiver_id.
        """
        receiver = models.Receiver.get(store, receiver_id)
        return [context.id for context in receiver.contexts]

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


class TestField(helpers.TestGL):
    @inlineCallbacks
    def setUp(self):
        yield super(TestField, self).setUp()

    @transact
    def field_delete(self, store, field_id):
        store.remove(models.Field.get(store, field_id))

    @transact
    def add_children(self, store, field_id, *field_ids):
        parent = models.Field.get(store, field_id)
        for field_id in field_ids:
            field = models.Field.get(store, field_id)
            parent.children.add(field)

    @transact
    def get_children(self, store, field_id):
        return [c.id for c in models.Field.get(store, field_id).children]

    @inlineCallbacks
    def test_field(self):
        field1_id = yield self.create_dummy_field()
        yield self.assert_model_exists(models.Field, field1_id)

        field2_id = yield self.create_dummy_field(type='checkbox')
        yield self.assert_model_exists(models.Field, field2_id)

        yield self.field_delete(field1_id)
        yield self.assert_model_not_exists(models.Field, field1_id)
        yield self.assert_model_exists(models.Field, field2_id)

    @inlineCallbacks
    def test_field_group(self):
        field1_id = yield self.create_dummy_field(
            label={"en": "the first testable field"},
            type='checkbox'
        )

        field2_id = yield self.create_dummy_field(
            label={"en": "the second testable field"},
            type='inputbox'
        )

        fieldgroup_id = yield self.create_dummy_field(
            label={"en": "a testable group of fields."},
            type='fieldgroup',
            x=1, y=2,
        )

        yield self.assert_model_exists(models.Field, fieldgroup_id)
        yield self.assert_model_exists(models.Field, field2_id)
        yield self.add_children(fieldgroup_id, field1_id, field2_id)

        fieldgroup_children = yield self.get_children(fieldgroup_id)
        self.assertIn(field1_id, fieldgroup_children)
        self.assertIn(field2_id, fieldgroup_children)

        yield self.field_delete(fieldgroup_id)
        yield self.assert_model_not_exists(models.Field, fieldgroup_id)
        yield self.assert_model_not_exists(models.Field, field1_id)
        yield self.assert_model_not_exists(models.Field, field2_id)
