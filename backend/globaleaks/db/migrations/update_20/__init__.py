# -*- encoding: utf-8 -*-

"""
  Changes
    - Node: add possibility to disable Key Code Hint
    - Nootification: add possibility to force mail notification for every event
    - Notification: various templates added
    - *Tip, *File, Comment, Message : markers simplified to a simple boolean
    - ReceiverTip added label
    - Receiver renamed variables from gpg_* to pgp_*
"""

from storm.locals import Int, Bool, Unicode, DateTime, JSON
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import Model


class Node_v_19(Model):
    __storm_table__ = 'node'
    name = Unicode()
    public_site = Unicode()
    hidden_service = Unicode()
    email = Unicode()
    receipt_salt = Unicode()
    last_update = DateTime()
    receipt_regexp = Unicode()
    languages_enabled = JSON()
    default_language = Unicode()
    default_timezone = Int()
    description = JSON()
    presentation = JSON()
    footer = JSON()
    security_awareness_title = JSON()
    security_awareness_text = JSON()
    maximum_namesize = Int()
    maximum_textsize = Int()
    maximum_filesize = Int()
    tor2web_admin = Bool()
    tor2web_submission = Bool()
    tor2web_receiver = Bool()
    tor2web_unauth = Bool()
    allow_unencrypted = Bool()
    allow_iframes_inclusion = Bool()
    postpone_superpower = Bool()
    can_delete_submission = Bool()
    ahmia = Bool()
    wizard_done = Bool()
    disable_privacy_badge = Bool()
    disable_security_awareness_badge = Bool()
    disable_security_awareness_questions = Bool()
    whistleblowing_question = JSON()
    whistleblowing_button = JSON()
    enable_custom_privacy_badge = Bool()
    custom_privacy_badge_tor = JSON()
    custom_privacy_badge_none = JSON()
    header_title_homepage = JSON()
    header_title_submissionpage = JSON()
    header_title_receiptpage = JSON()
    landing_page = Unicode()
    exception_email = Unicode()


class Notification_v_19(Model):
    __storm_table__ = 'notification'
    server = Unicode()
    port = Int()
    username = Unicode()
    password = Unicode()
    source_name = Unicode()
    source_email = Unicode()
    security = Unicode()
    admin_anomaly_template = JSON()
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
    admin_pgp_alert_mail_title = JSON()
    admin_pgp_alert_mail_template = JSON()
    pgp_alert_mail_title = JSON()
    pgp_alert_mail_template = JSON()
    zip_description = JSON()
    ping_mail_template = JSON()
    ping_mail_title = JSON()
    disable_admin_notification_emails = Bool()
    disable_receivers_notification_emails = Bool()


class Message_v_19(Model):
    __storm_table__ = 'message'
    creation_date = DateTime()
    receivertip_id = Unicode()
    author = Unicode()
    content = Unicode()
    visualized = Bool()
    type = Unicode()
    mark = Unicode()


class Comment_v_19(Model):
    __storm_table__ = 'comment'
    creation_date = DateTime()
    internaltip_id = Unicode()
    author = Unicode()
    content = Unicode()
    system_content = JSON()
    type = Unicode()
    mark = Unicode()


class InternalTip_v_19(Model):
    __storm_table__ = 'internaltip'
    creation_date = DateTime()
    context_id = Unicode()
    wb_steps = JSON()
    expiration_date = DateTime()
    last_activity = DateTime()
    access_limit = Int()
    download_limit = Int()
    mark = Unicode()


class ReceiverTip_v_19(Model):
    __storm_table__ = 'receivertip'
    internaltip_id = Unicode()
    receiver_id = Unicode()
    last_access = DateTime()
    access_counter = Int()
    notification_date = DateTime()
    mark = Unicode()


class InternalFile_v_19(Model):
    __storm_table__ = 'internalfile'
    creation_date = DateTime()
    internaltip_id = Unicode()
    name = Unicode()
    file_path = Unicode()
    content_type = Unicode()
    description = Unicode()
    size = Int()
    mark = Unicode()


class ReceiverFile_v_19(Model):
    __storm_table__ = 'receiverfile'
    internaltip_id = Unicode()
    internalfile_id = Unicode()
    receiver_id = Unicode()
    receiver_tip_id = Unicode()
    file_path = Unicode()
    size = Int()
    downloads = Int()
    last_access = DateTime()
    mark = Unicode()
    status = Unicode()


class Receiver_v_19(Model):
    __storm_table__ = 'receiver'
    user_id = Unicode()
    name = Unicode()
    description = JSON()
    configuration = Unicode()
    gpg_key_info = Unicode()
    gpg_key_fingerprint = Unicode()
    gpg_key_armor = Unicode()
    gpg_key_expiration = DateTime()
    gpg_key_status = Unicode()
    mail_address = Unicode()
    ping_mail_address = Unicode()
    can_delete_submission = Bool()
    postpone_superpower = Bool()
    last_update = DateTime()
    tip_notification = Bool()
    comment_notification = Bool()
    file_notification = Bool()
    message_notification = Bool()
    ping_notification = Bool()
    presentation_order = Int()


class Context_v_19(Model):
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
    postpone_superpower = Bool()
    can_delete_submission = Bool()
    presentation_order = Int()


class MigrationScript(MigrationBase):
    def migrate_Node(self):
        old_node = self.store_old.find(self.model_from['Node']).one()
        new_node = self.model_to['Node']()

        new_templates = ['context_selector_label']

        for _, v in new_node._storm_columns.iteritems():
            if self.update_model_with_new_templates(new_node, v.name, new_templates, self.appdata['node']):
                continue

            if v.name == 'can_postpone_expiration':
                old_attr = 'postpone_superpower'
                setattr(new_node, v.name, getattr(old_node, old_attr))
                continue

            if v.name == 'disable_key_code_hint':
                new_node.disable_key_code_hint = False
                continue

            if v.name == 'show_contexts_in_alphabetical_order':
                new_node.show_contexts_in_alphabetical_order = False
                continue

            setattr(new_node, v.name, getattr(old_node, v.name))

        self.store_new.add(new_node)
        self.store_new.commit()

    def migrate_Notification(self):
        old_notification = self.store_old.find(self.model_from['Notification']).one()
        new_notification = self.model_to['Notification']()

        new_templates = [
            'admin_anomaly_mail_title',
            'admin_anomaly_mail_template',
            'notification_digest_mail_title',
            'tip_expiration_mail_title',
            'tip_expiration_template'
        ]

        for _, v in new_notification._storm_columns.iteritems():
            if self.update_model_with_new_templates(new_notification, v.name, new_templates, self.appdata['templates']):
                continue

            if v.name == 'send_email_for_every_event':
                new_notification.send_email_for_every_event = True
                continue

            if v.name == 'torify':
                new_notification.torify = True
                continue

            setattr(new_notification, v.name, getattr(old_notification, v.name))

        self.store_new.add(new_notification)
        self.store_new.commit()

    def migrate_Message(self):
        old_objs = self.store_old.find(self.model_from['Message'])
        for old_obj in old_objs:
            new_obj = self.model_to['Message']()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'new':
                    new_obj.new = False
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()

    def migrate_Comment(self):
        old_objs = self.store_old.find(self.model_from['Comment'])
        for old_obj in old_objs:
            new_obj = self.model_to['Comment']()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'new':
                    new_obj.new = False
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()

    def migrate_InternalTip(self):
        old_objs = self.store_old.find(self.model_from['InternalTip'])
        for old_obj in old_objs:
            new_obj = self.model_to['InternalTip']()
            for _, v in new_obj._storm_columns.iteritems():

                if v.name == 'new':
                    new_obj.new = False
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()

    def migrate_ReceiverTip(self):
        old_objs = self.store_old.find(self.model_from['ReceiverTip'])
        for old_obj in old_objs:
            new_obj = self.model_to['ReceiverTip']()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'label':
                    new_obj.label = u''
                    continue

                if v.name == 'new':
                    new_obj.new = False
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()

    def migrate_InternalFile(self):
        old_objs = self.store_old.find(self.model_from['InternalFile'])
        for old_obj in old_objs:
            new_obj = self.model_to['InternalFile']()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'new':
                    new_obj.new = False
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()

    def migrate_ReceiverFile(self):
        old_objs = self.store_old.find(self.model_from['ReceiverFile'])
        for old_obj in old_objs:
            new_obj = self.model_to['ReceiverFile']()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'new':
                    new_obj.new = False
                    continue

                if v.name == 'receivertip_id':
                    old_attr = 'receiver_tip_id'
                    setattr(new_obj, v.name, getattr(old_obj, old_attr))
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()

    def migrate_Context(self):
        old_objs = self.store_old.find(self.model_from['Context'])
        for old_obj in old_objs:
            new_obj = self.model_to['Context']()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'can_postpone_expiration':
                    old_attr = 'postpone_superpower'
                    setattr(new_obj, v.name, getattr(old_obj, old_attr))
                    continue

                if v.name == 'show_receivers_in_alphabetical_order':
                    new_obj.show_receivers_in_alphabetical_order = False
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()

    def migrate_Receiver(self):
        old_objs = self.store_old.find(self.model_from['Receiver'])
        for old_obj in old_objs:
            new_obj = self.model_to['Receiver']()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'can_postpone_expiration':
                    old_attr = 'postpone_superpower'
                    setattr(new_obj, v.name, getattr(old_obj, old_attr))
                    continue

                if v.name == 'pgp_key_public':
                    old_attr = 'gpg_key_armor'
                    setattr(new_obj, v.name, getattr(old_obj, old_attr))
                    continue

                if v.name.startswith('pgp_'):
                    old_attr = v.name.replace('pgp_', 'gpg_', 1)
                    setattr(new_obj, v.name, getattr(old_obj, old_attr))
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()
