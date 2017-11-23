# -*- coding: utf-8 -*-
import os
import shutil
from storm.locals import Int, Bool, Unicode, DateTime, JSON

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import ModelWithID
from globaleaks.settings import Settings


class Node_v_26(ModelWithID):
    __storm_table__ = 'node'
    version = Unicode()
    version_db = Unicode()
    name = Unicode()
    public_site = Unicode()
    hidden_service = Unicode()
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
    tor2web_custodian = Bool()
    tor2web_whistleblower = Bool()
    tor2web_receiver = Bool()
    tor2web_unauth = Bool()
    allow_unencrypted = Bool()
    allow_iframes_inclusion = Bool()
    submission_minimum_delay = Int()
    submission_maximum_ttl = Int()
    can_postpone_expiration = Bool()
    can_delete_submission = Bool()
    can_grant_permissions = Bool()
    ahmia = Bool()
    wizard_done = Bool()
    disable_privacy_badge = Bool()
    disable_security_awareness_badge = Bool()
    disable_security_awareness_questions = Bool()
    disable_key_code_hint = Bool()
    disable_donation_panel = Bool()
    enable_captcha = Bool()
    enable_proof_of_work = Bool()
    whistleblowing_question = JSON()
    whistleblowing_button = JSON()
    simplified_login = Bool()
    enable_custom_privacy_badge = Bool()
    custom_privacy_badge_tor = JSON()
    custom_privacy_badge_none = JSON()
    header_title_homepage = JSON()
    header_title_submissionpage = JSON()
    header_title_receiptpage = JSON()
    header_title_tippage = JSON()
    widget_comments_title = JSON()
    widget_messages_title = JSON()
    widget_files_title = JSON()
    landing_page = Unicode()
    show_contexts_in_alphabetical_order = Bool()
    threshold_free_disk_megabytes_high = Int()
    threshold_free_disk_megabytes_medium = Int()
    threshold_free_disk_megabytes_low = Int()
    threshold_free_disk_percentage_high = Int()
    threshold_free_disk_percentage_medium = Int()
    threshold_free_disk_percentage_low = Int()


class Context_v_26(ModelWithID):
    __storm_table__ = 'context'
    show_small_cards = Bool()
    show_context = Bool()
    show_receivers = Bool()
    maximum_selectable_receivers = Int()
    select_all_receivers = Bool()
    enable_comments = Bool()
    enable_messages = Bool()
    enable_two_way_comments = Bool()
    enable_two_way_messages = Bool()
    enable_attachments = Bool()
    enable_whistleblower_identity = Bool()
    tip_timetolive = Int()
    name = JSON()
    description = JSON()
    recipients_clarification = JSON()
    questionnaire_layout = Unicode()
    show_receivers_in_alphabetical_order = Bool()
    presentation_order = Int()


class Notification_v_26(ModelWithID):
    __storm_table__ = 'notification'
    server = Unicode()
    port = Int()
    username = Unicode()
    password = Unicode()
    source_name = Unicode()
    source_email = Unicode()
    security = Unicode()
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
    archive_description = JSON()
    identity_access_authorized_mail_template = JSON()
    identity_access_authorized_mail_title = JSON()
    identity_access_denied_mail_template = JSON()
    identity_access_denied_mail_title = JSON()
    identity_access_request_mail_template = JSON()
    identity_access_request_mail_title = JSON()
    identity_provided_mail_template = JSON()
    identity_provided_mail_title = JSON()
    disable_admin_notification_emails = Bool()
    disable_custodian_notification_emails = Bool()
    disable_receiver_notification_emails = Bool()
    send_email_for_every_event = Bool()
    tip_expiration_threshold = Int()
    notification_threshold_per_hour = Int()
    notification_suspension_time=Int()
    exception_email_address = Unicode()
    exception_email_pgp_key_info = Unicode()
    exception_email_pgp_key_fingerprint = Unicode()
    exception_email_pgp_key_public = Unicode()
    exception_email_pgp_key_expiration = DateTime()
    exception_email_pgp_key_status = Unicode()


class MigrationScript(MigrationBase):
    def prologue(self):
        old_logo_path = os.path.abspath(os.path.join(Settings.files_path, 'globaleaks_logo.png'))
        if os.path.exists(old_logo_path):
            new_logo_path = os.path.abspath(os.path.join(Settings.files_path, 'logo.png'))
            shutil.move(old_logo_path, new_logo_path)

    def migrate_Node(self):
        old_node = self.store_old.find(self.model_from['Node']).one()
        new_node = self.model_to['Node']()

        for _, v in new_node._storm_columns.items():
            if v.name == 'enable_experimental_features':
                new_node.enable_experimental_features = False
            else:
                setattr(new_node, v.name, getattr(old_node, v.name))

        self.store_new.add(new_node)

    def migrate_Context(self):
        old_objs = self.store_old.find(self.model_from['Context'])
        for old_obj in old_objs:
            new_obj = self.model_to['Context']()
            for _, v in new_obj._storm_columns.items():
                if v.name == 'show_recipients_details':
                    new_obj.show_recipients_details = old_obj.show_receivers
                elif v.name == 'allow_recipients_selection':
                    new_obj.allow_recipients_selection = old_obj.show_receivers
                else:
                    setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)
