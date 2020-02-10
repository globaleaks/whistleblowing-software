# -*- coding: utf-8 -*-
import os
import shutil

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import Model
from globaleaks.models.properties import *
from globaleaks.settings import Settings


class Node_v_26(Model):
    __tablename__ = 'node'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    version = Column(UnicodeText)
    version_db = Column(UnicodeText)
    name = Column(UnicodeText)
    public_site = Column(UnicodeText)
    hidden_service = Column(UnicodeText)
    receipt_salt = Column(UnicodeText)
    languages_enabled = Column(JSON)
    default_language = Column(UnicodeText)
    default_timezone = Column(Integer)
    description = Column(JSON)
    presentation = Column(JSON)
    footer = Column(JSON)
    context_selector_label = Column(JSON)
    maximum_filesize = Column(Integer)
    tor2web_admin = Column(Boolean)
    tor2web_custodian = Column(Boolean)
    tor2web_whistleblower = Column(Boolean)
    tor2web_receiver = Column(Boolean)
    tor2web_unauth = Column(Boolean)
    allow_unencrypted = Column(Boolean)
    allow_iframes_inclusion = Column(Boolean)
    submission_minimum_delay = Column(Integer)
    can_postpone_expiration = Column(Boolean)
    can_delete_submission = Column(Boolean)
    can_grant_permissions = Column(Boolean)
    wizard_done = Column(Boolean)
    disable_privacy_badge = Column(Boolean)
    disable_key_code_hint = Column(Boolean)
    enable_captcha = Column(Boolean)
    whistleblowing_question = Column(JSON)
    whistleblowing_button = Column(JSON)
    simplified_login = Column(Boolean)
    enable_custom_privacy_badge = Column(Boolean)
    header_title_homepage = Column(JSON)
    header_title_submissionpage = Column(JSON)
    header_title_receiptpage = Column(JSON)
    header_title_tippage = Column(JSON)
    landing_page = Column(UnicodeText)
    show_contexts_in_alphabetical_order = Column(Boolean)
    threshold_free_disk_megabytes_high = Column(Integer)
    threshold_free_disk_megabytes_medium = Column(Integer)
    threshold_free_disk_megabytes_low = Column(Integer)
    threshold_free_disk_percentage_high = Column(Integer)
    threshold_free_disk_percentage_medium = Column(Integer)
    threshold_free_disk_percentage_low = Column(Integer)


class Context_v_26(Model):
    __tablename__ = 'context'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    show_small_cards = Column(Boolean)
    show_context = Column(Boolean)
    show_receivers = Column(Boolean)
    maximum_selectable_receivers = Column(Integer)
    select_all_receivers = Column(Boolean)
    enable_comments = Column(Boolean)
    enable_messages = Column(Boolean)
    enable_two_way_comments = Column(Boolean)
    enable_two_way_messages = Column(Boolean)
    enable_attachments = Column(Boolean)
    enable_whistleblower_identity = Column(Boolean)
    tip_timetolive = Column(Integer)
    name = Column(JSON)
    description = Column(JSON)
    recipients_clarification = Column(JSON)
    questionnaire_layout = Column(UnicodeText)
    show_receivers_in_alphabetical_order = Column(Boolean)
    presentation_order = Column(Integer)


class Notification_v_26(Model):
    __tablename__ = 'notification'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    server = Column(UnicodeText)
    port = Column(Integer)
    username = Column(UnicodeText)
    password = Column(UnicodeText)
    source_email = Column(UnicodeText)
    security = Column(UnicodeText)
    admin_pgp_alert_mail_title = Column(JSON)
    admin_pgp_alert_mail_template = Column(JSON)
    admin_anomaly_mail_template = Column(JSON)
    admin_anomaly_mail_title = Column(JSON)
    admin_anomaly_disk_low = Column(JSON)
    admin_anomaly_disk_medium = Column(JSON)
    admin_anomaly_disk_high = Column(JSON)
    admin_anomaly_activities = Column(JSON)
    tip_mail_template = Column(JSON)
    tip_mail_title = Column(JSON)
    file_mail_template = Column(JSON)
    file_mail_title = Column(JSON)
    comment_mail_template = Column(JSON)
    comment_mail_title = Column(JSON)
    message_mail_template = Column(JSON)
    message_mail_title = Column(JSON)
    tip_expiration_mail_template = Column(JSON)
    tip_expiration_mail_title = Column(JSON)
    pgp_alert_mail_title = Column(JSON)
    pgp_alert_mail_template = Column(JSON)
    receiver_notification_limit_reached_mail_template = Column(JSON)
    receiver_notification_limit_reached_mail_title = Column(JSON)
    archive_description = Column(JSON)
    identity_access_authorized_mail_template = Column(JSON)
    identity_access_authorized_mail_title = Column(JSON)
    identity_access_denied_mail_template = Column(JSON)
    identity_access_denied_mail_title = Column(JSON)
    identity_access_request_mail_template = Column(JSON)
    identity_access_request_mail_title = Column(JSON)
    identity_provided_mail_template = Column(JSON)
    identity_provided_mail_title = Column(JSON)
    disable_admin_notification_emails = Column(Boolean)
    disable_custodian_notification_emails = Column(Boolean)
    disable_receiver_notification_emails = Column(Boolean)
    tip_expiration_threshold = Column(Integer)
    exception_email_address = Column(UnicodeText)
    exception_email_pgp_key_fingerprint = Column(UnicodeText)
    exception_email_pgp_key_public = Column(UnicodeText)
    exception_email_pgp_key_expiration = Column(DateTime)


class MigrationScript(MigrationBase):
    renamed_attrs = {
      'Context': {
          'show_recipients_details': 'show_receivers',
          'allow_recipients_selection': 'show_receivers'
      },
    }
    def prologue(self):
        old_logo_path = os.path.abspath(os.path.join(Settings.files_path, 'globaleaks_logo.png'))
        if os.path.exists(old_logo_path):
            new_logo_path = os.path.abspath(os.path.join(Settings.files_path, 'logo.png'))
            shutil.move(old_logo_path, new_logo_path)
