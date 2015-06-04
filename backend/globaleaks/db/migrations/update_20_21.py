# -*- encoding: utf-8 -*-

"""
  Changes
    - Node: add possibility to disable Key Code Hint

"""

from storm.locals import Int, Bool, Unicode, DateTime, JSON, Reference
from globaleaks.db.base_updater import TableReplacer
from globaleaks.db.datainit import load_appdata
from globaleaks.models import Model
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
        return
        print "%s User migration assistant"  % self.std_fancy

        old_users = self.store_old.find(self.get_right_model("User", 20))

        old_users = self.store_old.find(self.get_right_model("User", 20))

        receiver_model = self.get_right_model("Receiver", 20)

        for old_user in old_users:

            new_user = self.get_right_model("User", 21)()

            for _, v in new_user._storm_columns.iteritems():
                if v.name == 'mail_address':
                    old_receiver = self.store_old.find(receiver_model)
                    print old_user.id
                    for a in old_receiver:
                        #print a.id
                        print a.user_id
                        #print a.mail_address
                    #new_user.mail_address = old_receiver.mail_address
                    #print new_user.mail_address
                    continue

                setattr(new_user, v.name, getattr(old_user, v.name))

            self.store_new.add(new_user)

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


            self.store_new.add(new_user)
            self.store_new.add(new_receiver)
        self.store_new.commit()
