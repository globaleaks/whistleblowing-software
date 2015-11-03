# -*- encoding: utf-8 -*-

import string

from storm.locals import Int, Bool, Unicode, DateTime, JSON, Reference

from globaleaks.db.base_updater import TableReplacer
from globaleaks.db.datainit import load_appdata
from globaleaks.models import BaseModel, Model
from globaleaks.utils.utility import datetime_null, every_language


class Node_v_23(Model):
    __storm_table__ = 'node'
    name = Unicode()
    public_site = Unicode()
    hidden_service = Unicode()
    email = Unicode()
    receipt_salt = Unicode()
    languages_enabled = JSON()
    default_language = Unicode()
    default_timezone = Int()
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
    submission_minimum_delay = Int()
    submission_maximum_ttl = Int()
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


class User_v_23(Model):
    __storm_table__ = 'user'
    creation_date = DateTime()
    username = Unicode()
    password = Unicode()
    salt = Unicode()
    role = Unicode()
    state = Unicode()
    last_login = DateTime()
    mail_address = Unicode()
    language = Unicode()
    timezone = Int()
    password_change_needed = Bool()
    password_change_date = DateTime()


class Notification_v_23(Model):
    __storm_table__ = 'notification'
    server = Unicode()
    port = Int()
    username = Unicode()
    password = Unicode()
    source_name = Unicode()
    source_email = Unicode()
    security = Unicode()
    torify = Int()
    admin_pgp_alert_mail_title = JSON()
    admin_pgp_alert_mail_template = JSON()
    admin_anomaly_mail_template = JSON()
    admin_anomaly_mail_title = JSON()
    admin_anomaly_disk_low = JSON()
    admin_anomaly_disk_medium = JSON()
    admin_anomaly_disk_high = JSON()
    admin_anomaly_activities = JSON()
    tip_mail_template = JSON()
    tip_mail_title = JSON()
    file_mail_template = JSON()
    file_mail_title = JSON()
    comment_mail_template = JSON()
    comment_mail_title = JSON()
    message_mail_template = JSON()
    message_mail_title = JSON()
    tip_expiration_mail_template = JSON()
    tip_expiration_mail_title = JSON()
    pgp_alert_mail_title = JSON()
    pgp_alert_mail_template = JSON()
    receiver_notification_limit_reached_mail_template = JSON()
    receiver_notification_limit_reached_mail_title = JSON()
    zip_description = JSON()
    ping_mail_template = JSON()
    ping_mail_title = JSON()
    notification_digest_mail_title = JSON()
    disable_admin_notification_emails = Bool()
    disable_receivers_notification_emails = Bool()
    send_email_for_every_event = Bool()
    notification_threshold_per_hour = Int()
    notification_suspension_time = Int()


class Receiver_v_23(Model):
    __storm_table__ = 'receiver'
    name = Unicode()
    description = JSON()
    configuration = Unicode()
    pgp_key_info = Unicode()
    pgp_key_fingerprint = Unicode()
    pgp_key_public = Unicode()
    pgp_key_expiration = DateTime()
    pgp_key_status = Unicode()
    ping_mail_address = Unicode()
    can_delete_submission = Bool()
    can_postpone_expiration = Bool()
    tip_notification = Bool()
    ping_notification = Bool()
    tip_expiration_threshold = Int()
    presentation_order = Int()


Receiver_v_23.user = Reference(Receiver_v_23.id, User_v_23.id)


class Context_v_23(Model):
    __storm_table__ = 'context'
    show_small_cards = Bool()
    show_receivers = Bool()
    maximum_selectable_receivers = Int()
    select_all_receivers = Bool()
    enable_comments = Bool()
    enable_private_messages = Bool()
    tip_timetolive = Int()
    name = JSON()
    description = JSON()
    questionnaire_layout = Unicode()
    show_receivers_in_alphabetical_order = Bool()
    presentation_order = Int()


class InternalTip_v_23(Model):
    __storm_table__ = 'internaltip'
    creation_date = DateTime()
    context_id = Unicode()
    questionnaire_hash = Unicode()
    preview = JSON()
    progressive = Int()
    tor2web = Bool()
    expiration_date = DateTime()
    last_activity = DateTime()
    new = Int()


InternalTip_v_23.context = Reference(InternalTip_v_23.context_id, Context_v_23.id)


class ReceiverTip_v_23(Model):
    __storm_table__ = 'receivertip'
    internaltip_id = Unicode()
    receiver_id = Unicode()
    last_access = DateTime()
    access_counter = Int()
    notification_date = DateTime()
    label = Unicode()
    new = Int()


class Step_v_23(Model):
    __storm_table__ = 'step'
    context_id = Unicode()
    label = JSON()
    description = JSON()
    hint = JSON()
    presentation_order = Int()


class Field_v_23(Model):
    __storm_table__ = 'field'
    x = Int()
    y = Int()
    width = Int()
    label = JSON()
    description = JSON()
    hint = JSON()
    required = Bool()
    preview = Bool()
    multi_entry = Bool()
    multi_entry_hint = JSON()
    stats_enabled = Bool()
    is_template = Bool()
    template_id = Unicode()
    type = Unicode()


class ArchivedSchema_v_23(Model):
    __storm_table__ = 'archivedschema'
    hash = Unicode()
    type = Unicode()
    language = Unicode()
    schema = JSON()


class Replacer2324(TableReplacer):
    def migrate_Node(self):
        print "%s Node migration assistant: header_title_tippage" % self.std_fancy

        appdata_dict = load_appdata()

        old_node = self.store_old.find(self.get_right_model("Node", 23)).one()
        new_node = self.get_right_model("Node", 24)()

        for _, v in new_node._storm_columns.iteritems():
            if v.name == 'simplified_login':
                new_node.simplified_login = True
                continue

            if v.name == 'threshold_free_disk_megabytes_high':
                new_node.threshold_free_disk_megabytes_high = 200
                continue

            if v.name == 'threshold_free_disk_megabytes_medium':
                new_node.threshold_free_disk_megabytes_medium = 500
                continue

            if v.name == 'threshold_free_disk_megabytes_low':
                new_node.threshold_free_disk_megabytes_low = 1000
                continue

            if v.name == 'threshold_free_disk_percentage_high':
                new_node.threshold_free_disk_percentage_high = 3
                continue

            if v.name == 'threshold_free_disk_percentage_medium':
                new_node.threshold_free_disk_percentage_medium = 5
                continue

            if v.name == 'threshold_free_disk_percentage_low':
                new_node.threshold_free_disk_percentage_low = 10
                continue

            if v.name == 'tor2web_whistleblower':
                new_node.tor2web_whistleblower = old_node.tor2web_submission
                continue

            if v.name == 'tor2web_custodian':
                new_node.tor2web_custodian = False
                continue

            if v.name == 'enable_captcha':
                new_node.enable_captcha = True
                continue

            if v.name == 'enable_proof_of_work':
                new_node.enable_proof_of_work = True
                continue

            if v.name == 'header_title_tippage':
                # check needed to preserve funtionality if appdata will be altered in the future
                if v.name in appdata_dict['node']:
                    new_node.header_title_tippage = appdata_dict['node']['header_title_tippage']
                else:
                    new_node.header_title_tippage = every_language("")
                continue

            if v.name == 'widget_comments_title':
                # check needed to preserve funtionality if appdata will be altered in the future
                if v.name in appdata_dict['node']:
                    new_node.widget_comments_title = appdata_dict['node']['widget_comments_title']
                else:
                    new_node.widget_comments_title = every_language("")
                continue

            if v.name == 'widget_messages_title':
                # check needed to preserve funtionality if appdata will be altered in the future
                if v.name in appdata_dict['node']:
                    new_node.widget_messages_title = appdata_dict['node']['widget_messages_title']
                else:
                    new_node.widget_messages_title = every_language("")
                continue

            if v.name == 'widget_files_title':
                # check needed to preserve funtionality if appdata will be altered in the future
                if v.name in appdata_dict['node']:
                    new_node.widget_files_title = appdata_dict['node']['widget_files_title']
                else:
                    new_node.widget_files_title = every_language("")
                continue

            if v.name == 'can_grant_permissions':
                new_node.can_grant_permissions = False
                continue

            setattr(new_node, v.name, getattr(old_node, v.name))

        self.store_new.add(new_node)
        self.store_new.commit()

    def migrate_Notification(self):
        print "%s Notification migration assistant" % self.std_fancy

        old_node = self.store_old.find(self.get_right_model("Node", 23)).one()

        old_notification = self.store_old.find(self.get_right_model("Notification", 23)).one()
        new_notification = self.get_right_model("Notification", 24)()

        for _, v in new_notification._storm_columns.iteritems():
            if v.name == 'tip_expiration_threshold':
                new_notification.tip_expiration_threshold = 72 # that is the current default
                continue

            if v.name == 'exception_email_address':
                new_notification.exception_email_address = old_node.exception_email
                continue

            if v.name == 'exception_email_pgp_key_status':
                new_notification.exception_email_pgp_key_status = 'disabled'
                continue

            if v.name == 'exception_email_pgp_key_info':
                new_notification.exception_email_pgp_key_info = ''
                continue

            if v.name == 'exception_email_pgp_key_fingerprint':
                new_notification.exception_email_pgp_key_fingerprint = ''
                continue

            if v.name == 'exception_email_pgp_key_public':
                new_notification.exception_email_pgp_key_public = ''
                continue

            if v.name == 'exception_email_pgp_key_expiration':
                new_notification.exception_email_pgp_key_expiration = datetime_null()
                continue

            if v.name == 'archive_description':
                new_notification.archive_description = old_notification.zip_description
                continue

            old_value = getattr(old_notification, v.name)
            if v.name in new_notification.localized_strings:
                for lang in old_value:
                    old_value[lang] = string.replace(old_value[lang], "ReceiverName", "RecipientName")

            setattr(new_notification, v.name, old_value)

        self.store_new.add(new_notification)
        self.store_new.commit()

    def migrate_Receiver(self):
        print "%s Receiver migration assistant" % self.std_fancy

        old_receivers = self.store_old.find(self.get_right_model("Receiver", 23))

        for old_receiver in old_receivers:
            new_user = self.get_right_model("User", 24)()
            new_receiver = self.get_right_model("Receiver", 24)()

            for _, v in new_user._storm_columns.iteritems():
                if v.name == 'name':
                    new_user.name = old_receiver.name
                    continue

                if v.name == 'description':
                    new_user.description = old_receiver.description
                    continue

                if v.name == 'deletable':
                    new_user.deletable = True
                    continue

                if v.name == 'pgp_key_status':
                    new_user.pgp_key_status = old_receiver.pgp_key_status
                    continue

                if v.name == 'pgp_key_info':
                    new_user.pgp_key_info = old_receiver.pgp_key_info
                    continue

                if v.name == 'pgp_key_fingerprint':
                    new_user.pgp_key_fingerprint = old_receiver.pgp_key_fingerprint
                    continue

                if v.name == 'pgp_key_public':
                    new_user.pgp_key_public = old_receiver.pgp_key_public
                    continue

                if v.name == 'pgp_key_expiration':
                    new_user.pgp_key_expiration = old_receiver.pgp_key_expiration
                    continue

                setattr(new_user, v.name, getattr(old_receiver.user, v.name))

            for _, v in new_receiver._storm_columns.iteritems():
                if v.name == 'can_grant_permissions':
                    new_receiver.can_grant_permissions = False
                    continue

                setattr(new_receiver, v.name, getattr(old_receiver, v.name))

            # migrating we use old_receiver.id in order to not loose receiver-context associations
            new_receiver.id = new_user.username = new_user.id = old_receiver.id

            self.store_new.add(new_user)
            self.store_new.add(new_receiver)
        self.store_new.commit()


    def migrate_User(self):
        # Receivers and Users are migrated all together this time!
        # The only user to be migrated separately is the admin
        old_user_model = self.get_right_model("User", 23)
        old_admin = self.store_old.find(old_user_model, old_user_model.username == u'admin').one()

        new_admin = self.get_right_model("User", 24)()
        for _, v in new_admin._storm_columns.iteritems():
            if v.name == 'name':
                new_admin.name = u'Admin'
                continue

            if v.name == 'description':
                new_admin.description = {'en': ''}
                continue

            if v.name == 'deletable':
                new_admin.deletable = False
                continue

            if v.name == 'pgp_key_status':
                new_admin.pgp_key_status = 'disabled'
                continue

            if v.name == 'pgp_key_info':
                new_admin.pgp_key_info = ''
                continue

            if v.name == 'pgp_key_fingerprint':
                new_admin.pgp_key_fingerprint = ''
                continue

            if v.name == 'pgp_key_public':
                new_admin.pgp_key_public = ''
                continue

            if v.name == 'pgp_key_expiration':
                new_admin.pgp_key_expiration = datetime_null()
                continue

            setattr(new_admin, v.name, getattr(old_admin, v.name))

        self.store_new.add(new_admin)
        self.store_new.commit()


    def migrate_Context(self):
        print "%s Context migration assistant" % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("Context", 23))

        for old_obj in old_objs:
            new_obj = self.get_right_model("Context", 24)()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'show_context':
                    new_obj.show_context = True
                    continue

                if v.name == 'enable_comments':
                    new_obj.enable_comments = old_obj.enable_comments
                    continue

                if v.name == 'enable_messages':
                    new_obj.enable_messages = old_obj.enable_private_messages
                    continue

                if v.name == 'enable_two_way_comments':
                    new_obj.enable_two_way_comments = True
                    continue

                if v.name == 'enable_two_way_messages':
                    new_obj.enable_two_way_messages = True
                    continue

                if v.name == 'enable_attachments':
                    new_obj.enable_attachments = True
                    continue

                if v.name == 'enable_whistleblower_identity':
                    new_obj.enable_whistleblower_identity = False
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()


    def migrate_InternalTip(self):
        print "%s InternalTip migration assistant" % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("InternalTip", 23))

        for old_obj in old_objs:
            new_obj = self.get_right_model("InternalTip", 24)()

            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'update_date':
                    new_obj.update_date = old_obj.creation_date
                    continue

                if v.name == 'identity_provided':
                    new_obj.identity_provided = False
                    continue

                if v.name == 'total_score':
                    new_obj.total_score = 0
                    continue

                if v.name == 'enable_comments':
                    new_obj.enable_comments = old_obj.context.enable_comments
                    continue

                if v.name == 'enable_messages':
                    new_obj.enable_messages = old_obj.context.enable_private_messages
                    continue

                if v.name == 'enable_two_way_comments':
                    new_obj.enable_two_way_comments = True
                    continue

                if v.name == 'enable_two_way_messages':
                    new_obj.enable_two_way_messages = True
                    continue

                if v.name == 'enable_attachments':
                    new_obj.enable_attachments = True
                    continue

                if v.name == 'enable_whistleblower_identity':
                    new_obj.enable_whistleblower_identity = True
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()

    def migrate_ReceiverTip(self):
        print "%s ReceiverTip migration assistant" % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("ReceiverTip", 23))

        for old_obj in old_objs:
            new_obj = self.get_right_model("ReceiverTip", 24)()

            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'can_access_whistleblower_identity':
                    new_obj.can_access_whistleblower_identity = False
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()

    def migrate_Field(self):
        print "%s Field migration assistant" % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("Field", 23))

        for old_obj in old_objs:
            new_obj = self.get_right_model("Field", 24)()

            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'key':
                    new_obj.key = ''
                    continue

                if v.name == 'instance':
                    if old_obj.is_template:
                        new_obj.instance = 'template'
                    elif old_obj.template_id != '':
                        new_obj.instance = 'reference'
                    else:
                        new_obj.instance = 'instance'
                    continue

                if v.name == 'editable':
                    new_obj.editable = False
                    continue

                if v.name == 'activated_by_score':
                    new_obj.activated_by_score = 0
                    continue

                # Optional references should be threated in a special manner
                if v.name == 'template_id' and old_obj.template_id is None:
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()

    def migrate_ArchivedSchema(self):
        print "%s ArchivedSchema migration assistant" % self.std_fancy

        # Marking to avoid count check for ArchivedSchema
        self.fail_on_count_mismatch["ArchivedSchema"] = False

        old_objs = self.store_old.find(self.get_right_model("ArchivedSchema", 23))

        for old_obj in old_objs:
            new_obj = self.store_new.find(self.get_right_model("ArchivedSchema", 24),
                                          self.get_right_model("ArchivedSchema", 24).hash == old_obj.hash).one()

            if not new_obj:
                new_obj = self.get_right_model("ArchivedSchema", 24)()

            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'value':
                    if not isinstance(new_obj.value, dict):
                        new_obj.value = {}
                    new_obj.value[old_obj.language] = old_obj.value
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()
