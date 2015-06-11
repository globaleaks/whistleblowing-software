# -*- encoding: utf-8 -*-

from storm.locals import Int, Bool, Unicode, DateTime, JSON, Reference, ReferenceSet
from globaleaks.db.base_updater import TableReplacer
from globaleaks.db.datainit import load_appdata
from globaleaks.models import Model, ReceiverContext
from globaleaks.utils.utility import every_language

templates_list = [
  'admin_anomaly_activities',
  'admin_anomaly_disk_high',
  'admin_anomaly_disk_low',
  'admin_anomaly_disk_medium',
  'admin_anomaly_mail_template',
  'admin_anomaly_mail_title',
  'admin_pgp_alert_mail_title',
  'admin_pgp_alert_mail_template',
  'tip_mail_template',
  'tip_mail_title',
  'file_mail_template',
  'file_mail_title',
  'comment_mail_template',
  'comment_mail_title',
  'message_mail_template',
  'message_mail_title',
  'pgp_alert_mail_title',
  'pgp_alert_mail_template',
  'receiver_threshold_reached_mail_template',
  'receiver_threshold_reached_mail_title',
  'ping_mail_template',
  'ping_mail_title',
  'notification_digest_mail_title',
  'tip_expiration_mail_title',
  'tip_expiration_mail_template',
  'zip_description'
]


class Node_v_20(Model):
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


class Notification_v_20(Model):
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


class User_v_20(Model):
    __storm_table__ = 'user'
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


class Receiver_v_20(Model):
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


class Context_v_20(Model):
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


class Step_v_20(Model):
    __storm_table__ = 'step'
    context_id = Unicode()
    label = JSON()
    description = JSON()
    hint = JSON()
    number = Int()


class Field_v_20(Model):
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


class FieldOption_v_20(Model):
    __storm_table__ = 'fieldoption'
    field_id = Unicode()
    number = Int()
    attrs = JSON()


class Replacer2021(TableReplacer):
    def migrate_Node(self):
        print "%s Node migration assistant:" % self.std_fancy

        old_node = self.store_old.find(self.get_right_model("Node", 20)).one()
        new_node = self.get_right_model("Node", 21)()

        for _, v in new_node._storm_columns.iteritems():

            if v.name == 'submission_minimum_delay':
                setattr(new_node, v.name, 10)
                continue

            if v.name == 'submission_maximum_ttl':
                setattr(new_node, v.name, 10800)
                continue

            setattr(new_node, v.name, getattr(old_node, v.name))

        self.store_new.add(new_node)
        self.store_new.commit()

    def migrate_Notification(self):
        print "%s Notification migration assistant:" % self.std_fancy

        appdata_dict = load_appdata()

        old_notification = self.store_old.find(self.get_right_model("Notification", 20)).one()
        new_notification = self.get_right_model("Notification", 21)()

        for _, v in new_notification._storm_columns.iteritems():
            # In this release we enforce reloading all the updated templates due to the
            # semplification applied and the fact that we are not aware of any adopter
            # that has customized them.
            if v.name in templates_list:
                if v.name in appdata_dict['templates']:
                    value = appdata_dict['templates'][v.name]
                else:
                    value = every_language("")

                setattr(new_notification, v.name, value)
                continue

            if v.name == 'notification_threshold_per_hour':
               setattr(new_notification, v.name, 20)
               continue

            if v.name == 'notification_suspension_time':
               setattr(new_notification, v.name, 7200)
               continue

            if v.name == 'tip_expiration_threshold':
               setattr(new_notification, v.name, 72)
               continue

            setattr(new_notification, v.name, getattr(old_notification, v.name))

        self.store_new.add(new_notification)
        self.store_new.commit()

    def migrate_User(self):
        # Receivers and Users are migrated all together this time!
        # The only user to be migrated is the admin
        user_model = self.get_right_model("User", 20)
        old_admin = self.store_old.find(user_model, user_model.username == u'admin').one()
        old_node = self.store_old.find(self.get_right_model("Node", 20)).one()

        new_admin = self.get_right_model("User", 21)()
        for _, v in new_admin._storm_columns.iteritems():
           if v.name == 'mail_address':
               new_admin.mail_address = old_node.email
               continue

           setattr(new_admin, v.name, getattr(old_admin, v.name))

        self.store_new.add(new_admin)
        self.store_new.commit()


    def migrate_Receiver(self):
        print "%s Receiver migration assistant" % self.std_fancy

        old_receivers = self.store_old.find(self.get_right_model("Receiver", 20))

        for old_receiver in old_receivers:
            new_user = self.get_right_model("User", 21)()
            new_receiver = self.get_right_model("Receiver", 21)()

            for _, v in new_user._storm_columns.iteritems():
                if v.name == 'mail_address':
                    new_user.mail_address = old_receiver.mail_address
                    continue

                setattr(new_user, v.name, getattr(old_receiver.user, v.name))

            for _, v in new_receiver._storm_columns.iteritems():
                if v.name == 'tip_expiration_threshold':
                   new_receiver.tip_expiration_threshold = 72
                   continue

                setattr(new_receiver, v.name, getattr(old_receiver, v.name))

            # migrating we use old_receiver.id in order to not loose receiver-context associations
            new_receiver.id = new_user.username = new_user.id = old_receiver.id

            self.store_new.add(new_user)
            self.store_new.add(new_receiver)
        self.store_new.commit()

    def migrate_Context(self):
        print "%s Context migration assistant" % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("Context", 20))

        for old_obj in old_objs:

            new_obj = self.get_right_model("Context", 21)()

            for _, v in new_obj._storm_columns.iteritems():

                if v.name == 'enable_comments':
                    if (old_obj.enable_private_messages and old_obj.receivers.count() == 1):
                        new_obj.enable_comments = False
                    else:
                        new_obj.enable_comments = True
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()

    def migrate_Step(self):
        print "%s Step migration assistant" % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("Step", 20))

        for old_obj in old_objs:

            new_obj = self.get_right_model("Step", 21)()

            for _, v in new_obj._storm_columns.iteritems():

                if v.name == 'presentation_order':
                    if old_obj.number:
                        new_obj.presentation_order = old_obj.number
                    else:
                        new_obj.presentation_order = 0
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()

    def migrate_Field(self):
        print "%s Field migration assistant" % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("Field", 20))

        for old_obj in old_objs:

            new_obj = self.get_right_model("Field", 21)()

            for _, v in new_obj._storm_columns.iteritems():

                if v.name == 'presentation_order':
                    if old_obj.number:
                        new_obj.presentation_order = old_obj.number
                    else:
                        new_obj.presentation_order = 0
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()

    def migrate_FieldOption(self):
        print "%s FieldOption migration assistant" % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("FieldOption", 20))

        for old_obj in old_objs:

            new_obj = self.get_right_model("FieldOption", 21)()

            for _, v in new_obj._storm_columns.iteritems():

                if v.name == 'presentation_order':
                    if old_obj.number:
                        new_obj.presentation_order = old_obj.number
                    else:
                        new_obj.presentation_order = 0
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()
