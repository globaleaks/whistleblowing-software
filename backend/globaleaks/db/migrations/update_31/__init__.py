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


class MigrationScript(MigrationBase):
    renamed_attrs = {
        'Context': {
            'show_small_receiver_cards': 'show_small_cards'
        }
    }
