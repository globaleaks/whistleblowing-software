# -*- encoding: utf-8 -*-

from storm.locals import Int, Bool, Unicode, DateTime, JSON, Reference, ReferenceSet

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import Model, ModelWithID, ReceiverContext


class Node_v_20(ModelWithID):
    __storm_table__ = 'node'
    name = Unicode()
    public_site = Unicode()
    hidden_service = Unicode()
    email = Unicode()
    receipt_salt = Unicode()
    last_update = DateTime()
    languages_enabled = JSON()
    default_language = Unicode()
    default_timezone = Int(default=0)
    description = JSON()
    presentation = JSON()
    footer = JSON()
    security_awareness_title = JSON()
    security_awareness_text = JSON()
    context_selector_label = JSON()
    maximum_namesize = Int()
    maximum_textsize = Int()
    maximum_filesize = Int()
    tor2web_admin = Bool()
    tor2web_submission = Bool()
    tor2web_receiver = Bool()
    tor2web_unauth = Bool()
    allow_unencrypted = Bool()
    allow_iframes_inclusion = Bool()
    can_postpone_expiration = Bool()
    can_delete_submission = Bool()
    ahmia = Bool()
    wizard_done = Bool()
    disable_privacy_badge = Bool()
    disable_security_awareness_badge = Bool()
    disable_security_awareness_questions = Bool()
    disable_key_code_hint = Bool()
    whistleblowing_question = JSON()
    whistleblowing_button = JSON()
    enable_custom_privacy_badge = Bool()
    custom_privacy_badge_tor = JSON()
    custom_privacy_badge_none = JSON()
    header_title_homepage = JSON()
    header_title_submissionpage = JSON()
    header_title_receiptpage = JSON()
    landing_page = Unicode()
    show_contexts_in_alphabetical_order = Bool()
    exception_email = Unicode()


class Notification_v_20(ModelWithID):
    __storm_table__ = 'notification'
    server = Unicode()
    port = Int()
    username = Unicode()
    password = Unicode()
    source_name = Unicode()
    source_email = Unicode()
    security = Unicode()
    torify = Int()
    admin_anomaly_template = JSON()
    admin_anomaly_mail_title = JSON()
    encrypted_tip_template = JSON()
    encrypted_tip_mail_title = JSON()
    plaintext_tip_template = JSON()
    plaintext_tip_mail_title = JSON()
    encrypted_file_template = JSON()
    encrypted_file_mail_title = JSON()
    plaintext_file_template = JSON()
    plaintext_file_mail_title = JSON()
    encrypted_comment_template = JSON()
    encrypted_comment_mail_title = JSON()
    plaintext_comment_template = JSON()
    plaintext_comment_mail_title = JSON()
    encrypted_message_template = JSON()
    encrypted_message_mail_title = JSON()
    plaintext_message_template = JSON()
    plaintext_message_mail_title = JSON()
    tip_expiration_template = JSON()
    tip_expiration_mail_title = JSON()
    admin_pgp_alert_mail_title = JSON()
    admin_pgp_alert_mail_template = JSON()
    pgp_alert_mail_title = JSON()
    pgp_alert_mail_template = JSON()
    notification_digest_mail_title = JSON()
    zip_description = JSON()
    ping_mail_template = JSON()
    ping_mail_title = JSON()
    disable_admin_notification_emails = Bool()
    disable_receivers_notification_emails = Bool()
    send_email_for_every_event = Bool()


class InternalTip_v_20(ModelWithID):
    __storm_table__ = 'internaltip'
    creation_date = DateTime()
    context_id = Unicode()
    wb_steps = JSON()
    expiration_date = DateTime()
    last_activity = DateTime()
    new = Int()


class User_v_20(ModelWithID):
    __storm_table__ = 'user'
    creation_date = DateTime()
    username = Unicode()
    password = Unicode()
    salt = Unicode()
    role = Unicode()
    state = Unicode()
    last_login = DateTime()
    language = Unicode()
    timezone = Int()
    password_change_needed = Bool()
    password_change_date = DateTime()


class Receiver_v_20(ModelWithID):
    __storm_table__ = 'receiver'
    user_id = Unicode()
    name = Unicode()
    description = JSON()
    configuration = Unicode()
    pgp_key_info = Unicode()
    pgp_key_fingerprint = Unicode()
    pgp_key_public = Unicode()
    pgp_key_expiration = DateTime()
    pgp_key_status = Unicode()
    mail_address = Unicode()
    ping_mail_address = Unicode()
    can_delete_submission = Bool()
    can_postpone_expiration = Bool()
    last_update = DateTime()
    tip_notification = Bool()
    ping_notification = Bool()
    presentation_order = Int()


Receiver_v_20.user = Reference(Receiver_v_20.user_id, User_v_20.id)


class Context_v_20(ModelWithID):
    __storm_table__ = 'context'
    show_small_cards = Bool()
    show_receivers = Bool()
    maximum_selectable_receivers = Int()
    select_all_receivers = Bool()
    enable_private_messages = Bool()
    tip_timetolive = Int()
    last_update = DateTime()
    name = JSON()
    description = JSON()
    receiver_introduction = JSON()
    can_postpone_expiration = Bool()
    can_delete_submission = Bool()
    show_receivers_in_alphabetical_order = Bool()
    presentation_order = Int()


Context_v_20.receivers = ReferenceSet(
    Context_v_20.id,
    ReceiverContext.context_id,
    ReceiverContext.receiver_id,
    Receiver_v_20.id
)


class Step_v_20(ModelWithID):
    __storm_table__ = 'step'
    context_id = Unicode()
    label = JSON()
    description = JSON()
    hint = JSON()
    number = Int()


class Field_v_20(ModelWithID):
    __storm_table__ = 'field'
    label = JSON()
    description = JSON()
    hint = JSON()
    multi_entry = Bool()
    required = Bool()
    preview = Bool()
    stats_enabled = Bool()
    is_template = Bool()
    x = Int()
    y = Int()
    type = Unicode()


class FieldOption_v_20(ModelWithID):
    __storm_table__ = 'fieldoption'
    field_id = Unicode()
    number = Int()
    attrs = JSON()


class StepField_v_20(Model):
    __storm_table__ = 'step_field'
    __storm_primary__ = 'step_id', 'field_id'
    step_id = Unicode()
    field_id = Unicode()


Field_v_20.options = ReferenceSet(
    Field_v_20.id,
    FieldOption_v_20.field_id
)

FieldOption_v_20.field = Reference(FieldOption_v_20.field_id, Field_v_20.id)

Step_v_20.children = ReferenceSet(
    Step_v_20.id,
    StepField_v_20.step_id,
    StepField_v_20.field_id,
    Field_v_20.id
)

Context_v_20.steps = ReferenceSet(Context_v_20.id, Step_v_20.context_id)

Step_v_20.context = Reference(Step_v_20.context_id, Context_v_20.id)


class MigrationScript(MigrationBase):
    def migrate_Node(self):
        old_node = self.store_old.find(self.model_from['Node']).one()
        new_node = self.model_to['Node']()

        for _, v in new_node._storm_columns.items():
            if v.name == 'submission_minimum_delay':
                setattr(new_node, v.name, 10)
                continue

            if v.name == 'submission_maximum_ttl':
                setattr(new_node, v.name, 10800)
                continue

            setattr(new_node, v.name, getattr(old_node, v.name))

        self.store_new.add(new_node)

    def migrate_Notification(self):
        old_notification = self.store_old.find(self.model_from['Notification']).one()
        new_notification = self.model_to['Notification']()

        for _, v in new_notification._storm_columns.items():
            if v.name == 'notification_threshold_per_hour':
                setattr(new_notification, v.name, 20)
                continue

            if v.name == 'notification_suspension_time':
                setattr(new_notification, v.name, 7200)
                continue

            if v.name == 'tip_expiration_threshold':
                setattr(new_notification, v.name, 72)
                continue

            old_value = getattr(old_notification, v.name, None)
            if old_value is not None:
                setattr(new_notification, v.name, old_value)

        self.store_new.add(new_notification)

    def migrate_User(self):
        # Receivers and Users are migrated all together this time!
        # The only user to be migrated is the admin
        old_user_model = self.model_from['User']
        old_admin = self.store_old.find(old_user_model, old_user_model.username == u'admin').one()

        old_node = self.store_old.find(self.model_from['Node']).one()

        new_admin = self.model_to['User']()
        for _, v in new_admin._storm_columns.items():
            if v.name == 'mail_address':
                new_admin.mail_address = old_node.email
                continue

            setattr(new_admin, v.name, getattr(old_admin, v.name))

        self.store_new.add(new_admin)


    def migrate_Receiver(self):
        old_receivers = self.store_old.find(self.model_from['Receiver'])
        for old_receiver in old_receivers:
            new_user = self.model_to['User']()
            new_receiver = self.model_to['Receiver']()

            for _, v in new_user._storm_columns.items():
                if v.name == 'mail_address':
                    new_user.mail_address = old_receiver.mail_address
                    continue

                setattr(new_user, v.name, getattr(old_receiver.user, v.name))

            for _, v in new_receiver._storm_columns.items():
                if v.name == 'tip_expiration_threshold':
                    new_receiver.tip_expiration_threshold = 72
                    continue

                setattr(new_receiver, v.name, getattr(old_receiver, v.name))

            # migrating we use old_receiver.id in order to not loose receiver-context associations
            new_receiver.id = new_user.username = new_user.id = old_receiver.id

            self.store_new.add(new_user)
            self.store_new.add(new_receiver)

    def migrate_Context(self):
        old_objs = self.store_old.find(self.model_from['Context'])
        for old_obj in old_objs:
            new_obj = self.model_to['Context']()
            for _, v in new_obj._storm_columns.items():
                if v.name == 'enable_comments':
                    if old_obj.enable_private_messages and old_obj.receivers.count() == 1:
                        new_obj.enable_comments = False
                    else:
                        new_obj.enable_comments = True
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

    def migrate_Step(self):
        old_objs = self.store_old.find(self.model_from['Step'])
        for old_obj in old_objs:
            new_obj = self.model_to['Step']()
            for _, v in new_obj._storm_columns.items():
                if v.name == 'presentation_order':
                    if old_obj.number:
                        new_obj.presentation_order = old_obj.number
                    else:
                        new_obj.presentation_order = 0
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

    def migrate_Field(self):
        old_objs = self.store_old.find(self.model_from['Field'])
        for old_obj in old_objs:
            new_obj = self.model_to['Field']()
            for _, v in new_obj._storm_columns.items():
                if v.name == 'presentation_order':
                    if old_obj.number:
                        new_obj.presentation_order = old_obj.number
                    else:
                        new_obj.presentation_order = 0
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

    def migrate_FieldOption(self):
        old_objs = self.store_old.find(self.model_from['FieldOption'])
        for old_obj in old_objs:
            new_obj = self.model_to['FieldOption']()
            for _, v in new_obj._storm_columns.items():
                if v.name == 'presentation_order':
                    if old_obj.number:
                        new_obj.presentation_order = old_obj.number
                    else:
                        new_obj.presentation_order = 0
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

    def migrate_InternalTip(self):
        old_objs = self.store_old.find(self.model_from['InternalTip'])
        for old_obj in old_objs:
            new_obj = self.model_to['InternalTip']()
            for _, v in new_obj._storm_columns.items():
                if v.name == 'preview':
                    preview_data = []
                    for s in old_obj.wb_steps:
                        for f in s['children']:
                            if f['preview']:
                                preview_data.append(f)

                    new_obj.preview = preview_data
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)
