# -*- encoding: utf-8 -*-

"""
  Changes (end2end encryption implemented)
    - Node: boolean if the system of encryption require
        backward crypto compatibility (node.crypto_backward)
    - InternalTip: keep wb public key and private key
        TODO authentication signature
    - Receiver: keep public and private key (RSA kind)
"""

from storm.locals import Int, Bool, Unicode, DateTime, JSON, ReferenceSet
from globaleaks.db.base_updater import TableReplacer
from globaleaks.db.datainit import load_appdata
from globaleaks.models import Model
from globaleaks.utils.utility import every_language


class InternalTip_v_20(Model):
    """
    add below remove from comment here:
+    pgp_glkey_pub VARCHAR,
+    pgp_glkey_priv VARCHAR,
    """
    pass


class Receiver_v_20(Model):
    """
    add below remove from comment here:
+    pgp_key_armor_priv VARCHAR,
+    pgp_glkey_pub VARCHAR,
+    pgp_glkey_priv VARCHAR,

    """
    pass


class Node_v_20(Model):
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
    exception_email = Unicode()


class Message_v_19(Model):
    __storm_table__ = 'message'
    receivertip_id = Unicode()
    author = Unicode()
    content = Unicode()
    visualized = Bool()
    type = Unicode()
    mark = Unicode()


class Comment_v_19(Model):
    __storm_table__ = 'comment'
    internaltip_id = Unicode()
    author = Unicode()
    content = Unicode()
    system_content = JSON()
    type = Unicode()
    mark = Unicode()

class InternalTip_v_19(Model):
    __storm_table__ = 'internaltip'
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


class Replacer2021(TableReplacer):

    def migrate_Node(self):
        print "%s Node migration assistant: adding crypto_backward" % self.std_fancy

        old_node = self.store_old.find(self.get_right_model("Node", 20)).one()
        new_node = self.get_right_model("Node", 21)()

        for _, v in new_node._storm_columns.iteritems():

            if v.name == 'disable_key_code_hint':
                new_node.disable_key_code_hint = False
                continue

            setattr(new_node, v.name, getattr(old_node, v.name))

        self.store_new.add(new_node)
        self.store_new.commit()

    def migrate_Notification(self):
        print "%s Notification migration assistant: various templates addeed" % self.std_fancy

        appdata_dict = load_appdata()

        old_notification = self.store_old.find(self.get_right_model("Notification", 19)).one()
        new_notification = self.get_right_model("Notification", 20)()

        for _, v in new_notification._storm_columns.iteritems():

            if v.name == 'send_email_for_every_event':
                new_notification.send_email_for_every_event = False
                continue

            if v.name == 'torify':
                new_notification.torify = True
                continue

            if v.name == 'admin_anomaly_mail_title':
                # check needed to preserve funtionality if templates will be altered in the future
                if v.name in appdata_dict['templates']:
                    new_notification.admin_anomaly_mail_title = appdata_dict['templates'][v.name]
                else:
                    new_notification.admin_anomaly_mail_title = every_language("")
                continue

            if v.name == 'notification_digest_mail_title':
                # check needed to preserve funtionality if templates will be altered in the future
                if v.name in appdata_dict['templates']:
                    new_notification.notification_digest_mail_title = appdata_dict['templates'][v.name]
                else:
                    new_notification.notification_digest_mail_title = every_language("")
                continue

            if v.name == 'upcoming_tip_expiration_mail_title':
                # check needed to preserve funtionality if templates will be altered in the future
                if v.name in appdata_dict['templates']:
                    new_notification.upcoming_tip_expiration_mail_title = appdata_dict['templates'][v.name]
                else:
                    new_notification.upcoming_tip_expiration_mail_title = every_language("")
                continue

            if v.name == 'upcoming_tip_expiration_template':
                # check needed to preserve funtionality if templates will be altered in the future
                if v.name in appdata_dict['templates']:
                    new_notification.upcoming_tip_expiration_template = appdata_dict['templates'][v.name]
                else:
                    new_notification.upcoming_tip_expiration_template = every_language("")
                continue

            setattr(new_notification, v.name, getattr(old_notification, v.name) )

        self.store_new.add(new_notification)
        self.store_new.commit()

    def migrate_Message(self):
        print "%s Message migration assistant: mark -> new" % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("Message", 19))

        for old_obj in old_objs:

            new_obj = self.get_right_model("Message", 20)()

            for _, v in new_obj._storm_columns.iteritems():

                if v.name == 'new':
                    new_obj.new = False
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()

    def migrate_Comment(self):
        print "%s Comment migration assistant: mark -> new" % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("Comment", 19))

        for old_obj in old_objs:

            new_obj = self.get_right_model("Comment", 20)()

            for _, v in new_obj._storm_columns.iteritems():

                if v.name == 'new':
                    new_obj.new = False
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()

    def migrate_InternalTip(self):
        print "%s InternalTip migration assistant: mark -> new" % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("InternalTip", 19))

        for old_obj in old_objs:

            new_obj = self.get_right_model("InternalTip", 20)()

            for _, v in new_obj._storm_columns.iteritems():

                if v.name == 'new':
                    new_obj.new = False
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()

    def migrate_ReceiverTip(self):
        print "%s ReceiverTip migration assistant: mark -> new" % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("ReceiverTip", 19))

        for old_obj in old_objs:

            new_obj = self.get_right_model("ReceiverTip", 20)()

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
        print "%s InternalFile migration assistant: mark -> new" % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("InternalFile", 19))

        for old_obj in old_objs:

            new_obj = self.get_right_model("InternalFile", 20)()

            for _, v in new_obj._storm_columns.iteritems():

                if v.name == 'new':
                    new_obj.new = False
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()

    def migrate_ReceiverFile(self):
        print "%s ReceiverFile migration assistant: mark -> new" % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("ReceiverFile", 19))

        for old_obj in old_objs:

            new_obj = self.get_right_model("ReceiverFile", 20)()

            for _, v in new_obj._storm_columns.iteritems():

                if v.name == 'new':
                    new_obj.new = False
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()

    def migrate_Receiver(self):
        print "%s Receiver migration assistant: gpg_ -> pgp_" % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("Receiver", 19))

        for old_obj in old_objs:

            new_obj = self.get_right_model("Receiver", 20)()

            for _, v in new_obj._storm_columns.iteritems():

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
