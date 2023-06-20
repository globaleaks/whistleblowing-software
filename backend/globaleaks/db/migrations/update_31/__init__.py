# -*- coding: utf-8 -*-
import base64
import os

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import Model
from globaleaks.models.properties import *
from globaleaks.settings import Settings


class Node_v_30(Model):
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
    disable_encryption_warnings = Column(Boolean)
    allow_iframes_inclusion = Column(Boolean)
    submission_minimum_delay = Column(Integer)
    can_postpone_expiration = Column(Boolean)
    can_delete_submission = Column(Boolean)
    can_grant_permissions = Column(Boolean)
    wizard_done = Column(Boolean)
    disable_submissions = Column(Boolean)
    disable_privacy_badge = Column(Boolean)
    disable_key_code_hint = Column(Boolean, default=False)
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


class User_v_30(Model):
    __tablename__ = 'user'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    creation_date = Column(DateTime)
    username = Column(UnicodeText)
    password = Column(UnicodeText)
    salt = Column(UnicodeText)
    name = Column(UnicodeText)
    description = Column(JSON)
    role = Column(UnicodeText)
    state = Column(UnicodeText)
    last_login = Column(DateTime)
    mail_address = Column(UnicodeText)
    language = Column(UnicodeText)
    timezone = Column(Integer)
    password_change_needed = Column(Boolean)
    password_change_date = Column(DateTime)
    pgp_key_fingerprint = Column(UnicodeText)
    pgp_key_public = Column(UnicodeText)
    pgp_key_expiration = Column(DateTime)


class Context_v_30(Model):
    __tablename__ = 'context'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    show_small_cards = Column(Boolean)
    show_context = Column(Boolean)
    show_recipients_details = Column(Boolean)
    allow_recipients_selection = Column(Boolean)
    maximum_selectable_receivers = Column(Integer)
    select_all_receivers = Column(Boolean)
    enable_two_way_comments = Column(Boolean)
    enable_attachments = Column(Boolean)
    tip_timetolive = Column(Integer)
    name = Column(JSON)
    description = Column(JSON)
    recipients_clarification = Column(JSON)
    status_page_message = Column(JSON)
    show_receivers_in_alphabetical_order = Column(Boolean)
    presentation_order = Column(Integer)
    questionnaire_id = Column(UnicodeText(36), default='default')


class ReceiverTip_v_30(Model):
    __tablename__ = 'receivertip'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    internaltip_id = Column(UnicodeText(36))
    receiver_id = Column(UnicodeText(36))
    last_access = Column(DateTime)
    access_counter = Column(Integer)
    label = Column(UnicodeText)
    can_access_whistleblower_identity = Column(Boolean, default=True)
    new = Column(Integer)


class Notification_v_30(Model):
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
    export_template = Column(JSON)
    export_message_recipient = Column(JSON)
    export_message_whistleblower = Column(JSON)
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
            'show_small_receiver_cards': 'show_small_cards'
        }
    }

    def migrate_Node(self):
        old_node = self.session_old.query(self.model_from['Node']).one()
        new_node = self.model_to['Node']()

        for key in new_node.__mapper__.column_attrs.keys():
            if key == 'allow_indexing':
                new_node.allow_indexing = False

            elif key in ['logo_id', 'css_id']:
                if key == 'logo_id':
                    path = os.path.join(Settings.files_path, 'logo.png')
                else:
                    path = os.path.join(Settings.files_path, 'custom_stylesheet.css')

                if not os.path.exists(path):
                    continue

                new_file = self.model_to['File']()
                with open(path, 'rb') as f:
                    new_file.data = base64.b64encode(f.read()).decode()

                self.session_new.add(new_file)
                self.session_new.flush()

                if key == 'logo_id':
                    new_node.logo_id = new_file.id
                else:
                    new_node.css_id = new_file.id

                os.remove(path)
            elif key == 'basic_auth':
                new_node.basic_auth = False
            elif key == 'basic_auth_username':
                new_node.basic_auth_username = ''
            elif key == 'basic_auth_password':
                new_node.basic_auth_password = ''
            elif key == 'contexts_clarification':
                new_node.contexts_clarification = old_node.context_selector_label
            elif key == 'context_selector_type':
                new_node.context_selector_type = 'list'
            elif key == 'show_small_context_cards':
                new_node.show_small_context_cards = False
            else:
                setattr(new_node, key, getattr(old_node, key))

        self.session_new.add(new_node)

        for fname in ['default-profile-picture.png', 'robots.txt']:
            p = os.path.join(Settings.files_path, fname)
            if os.path.exists(p):
                os.remove(p)

    def migrate_User(self):
        for old_obj in self.session_old.query(self.model_from['User']):
            new_obj = self.model_to['User']()
            for key in new_obj.__mapper__.column_attrs.keys():
                if key == 'img_id':
                    img_path = os.path.join(Settings.files_path, old_obj.id + ".png")
                    if not os.path.exists(img_path):
                        continue

                    picture = self.model_to['File']()
                    with open(img_path, 'r') as img_file:
                        picture.data = base64.b64encode(img_file.read()).decode()

                    self.session_new.add(picture)
                    new_obj.picture_id = picture.id
                    os.remove(img_path)
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)
