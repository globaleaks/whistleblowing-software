# -*- coding: utf-8 -*-
from globaleaks import __version__, DATABASE_VERSION, LANGUAGES_SUPPORTED_CODES, models
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models.properties import *
from globaleaks.utils.utility import datetime_now, datetime_null


class Node_v_32(models.Model):
    __tablename__ = 'node'
    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)
    version = Column(UnicodeText, default=unicode(__version__))
    version_db = Column(UnicodeText, default=unicode(DATABASE_VERSION))
    name = Column(UnicodeText, default=u'')
    basic_auth = Column(Boolean, default=False)
    basic_auth_username = Column(UnicodeText, default=u'')
    basic_auth_password = Column(UnicodeText, default=u'')
    public_site = Column(UnicodeText, default=u'')
    hidden_service = Column(UnicodeText, default=u'')
    receipt_salt = Column(UnicodeText)
    languages_enabled = Column(JSON, default=LANGUAGES_SUPPORTED_CODES)
    default_language = Column(UnicodeText, default=u'en')
    default_timezone = Column(Integer, default=0)
    default_password = Column(UnicodeText, default=u'globaleaks')
    description = Column(JSON, default=dict)
    presentation = Column(JSON, default=dict)
    footer = Column(JSON, default=dict)
    security_awareness_title = Column(JSON, default=dict)
    security_awareness_text = Column(JSON, default=dict)
    maximum_namesize = Column(Integer, default=128)
    maximum_textsize = Column(Integer, default=4096)
    maximum_filesize = Column(Integer, default=30)
    tor2web_admin = Column(Boolean, default=True)
    tor2web_custodian = Column(Boolean, default=True)
    tor2web_whistleblower = Column(Boolean, default=False)
    tor2web_receiver = Column(Boolean, default=True)
    tor2web_unauth = Column(Boolean, default=True)
    allow_unencrypted = Column(Boolean, default=False)
    disable_encryption_warnings = Column(Boolean, default=False)
    allow_iframes_inclusion = Column(Boolean, default=False)
    submission_minimum_delay = Column(Integer, default=10)
    submission_maximum_ttl = Column(Integer, default=10800)
    can_postpone_expiration = Column(Boolean, default=False)
    can_delete_submission = Column(Boolean, default=False)
    can_grant_permissions = Column(Boolean, default=False)
    ahmia = Column(Boolean, default=False)
    allow_indexing = Column(Boolean, default=False)
    wizard_done = Column(Boolean, default=False)

    disable_submissions = Column(Boolean, default=False)
    disable_privacy_badge = Column(Boolean, default=False)
    disable_security_awareness_badge = Column(Boolean, default=False)
    disable_security_awareness_questions = Column(Boolean, default=False)
    disable_key_code_hint = Column(Boolean, default=False)
    disable_donation_panel = Column(Boolean, default=False)

    enable_captcha = Column(Boolean, default=True)
    enable_proof_of_work = Column(Boolean, default=True)

    enable_experimental_features = Column(Boolean, default=False)

    whistleblowing_question = Column(JSON, default=dict)
    whistleblowing_button = Column(JSON, default=dict)
    whistleblowing_receipt_prompt = Column(JSON, default=dict)

    simplified_login = Column(Boolean, default=True)

    enable_custom_privacy_badge = Column(Boolean, default=False)
    custom_privacy_badge_tor = Column(JSON, default=dict)
    custom_privacy_badge_none = Column(JSON, default=dict)

    header_title_homepage = Column(JSON, default=dict)
    header_title_submissionpage = Column(JSON, default=dict)
    header_title_receiptpage = Column(JSON, default=dict)
    header_title_tippage = Column(JSON, default=dict)

    widget_comments_title = Column(JSON, default=dict)
    widget_messages_title = Column(JSON, default=dict)
    widget_files_title = Column(JSON, default=dict)

    landing_page = Column(UnicodeText, default=u'homepage')

    contexts_clarification = Column(JSON, default=dict)
    show_small_context_cards = Column(Boolean, default=False)
    show_contexts_in_alphabetical_order = Column(Boolean, default=False)

    threshold_free_disk_megabytes_high = Column(Integer, default=200)
    threshold_free_disk_megabytes_medium = Column(Integer, default=500)
    threshold_free_disk_megabytes_low = Column(Integer, default=1000)

    threshold_free_disk_percentage_high = Column(Integer, default=3)
    threshold_free_disk_percentage_medium = Column(Integer, default=5)
    threshold_free_disk_percentage_low = Column(Integer, default=10)

    context_selector_type = Column(UnicodeText, default=u'list')


class InternalTip_v_32(models.Model):
    __tablename__ = 'internaltip'
    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)
    creation_date = Column(DateTime, default=datetime_now)
    update_date = Column(DateTime, default=datetime_now)

    context_id = Column(Unicode(36))

    questionnaire_hash = Column(UnicodeText)
    preview = Column(JSON)
    progressive = Column(Integer, default=0)
    tor2web = Column(Boolean, default=False)
    total_score = Column(Integer, default=0)
    expiration_date = Column(DateTime)

    identity_provided = Column(Boolean, default=False)
    identity_provided_date = Column(DateTime, default=datetime_null)

    enable_two_way_comments = Column(Boolean, default=True)
    enable_two_way_messages = Column(Boolean, default=True)
    enable_attachments = Column(Boolean, default=True)
    enable_whistleblower_identity = Column(Boolean, default=False)

    new = Column(Integer, default=True)


class WhistleblowerTip_v_32(models.Model):
    __tablename__ = 'whistleblowertip'
    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)
    internaltip_id = Column(Unicode(36))
    receipt_hash = Column(UnicodeText)

    last_access = Column(DateTime, default=datetime_now)
    access_counter = Column(Integer, default=0)


class User_v_32(models.Model):
    __tablename__ = 'user'
    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)
    creation_date = Column(DateTime, default=datetime_now)
    username = Column(UnicodeText)
    password = Column(UnicodeText)
    salt = Column(UnicodeText)
    deletable = Column(Boolean, default=True)
    name = Column(UnicodeText)
    description = Column(JSON)
    public_name = Column(UnicodeText)
    role = Column(UnicodeText)
    state = Column(UnicodeText)
    last_login = Column(DateTime, default=datetime_null)
    mail_address = Column(UnicodeText)
    language = Column(UnicodeText)
    timezone = Column(Integer)
    password_change_needed = Column(Boolean, default=True)
    password_change_date = Column(DateTime, default=datetime_null)
    pgp_key_info = Column(UnicodeText, default=u'')
    pgp_key_fingerprint = Column(UnicodeText, default=u'')
    pgp_key_public = Column(UnicodeText, default=u'')
    pgp_key_expiration = Column(DateTime, default=datetime_null)
    pgp_key_status = Column(UnicodeText, default=u'disabled')
    img_id = Column(Unicode(36))


class MigrationScript(MigrationBase):
    def migrate_InternalTip(self):
        old_objs = self.session_old.query(self.model_from['InternalTip'])
        for old_obj in old_objs:
            new_obj = self.model_to['InternalTip']()

            old_wbtip_model = self.model_from['WhistleblowerTip']
            old_wbtip = self.session_old.query(old_wbtip_model).filter(old_wbtip_model.internaltip_id == old_obj.id).one()
            if old_wbtip is None:
                self.entries_count['InternalTip'] -= 1
                continue

            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'wb_last_access':
                    if old_wbtip.last_access != datetime_null():
                        new_obj.wb_last_access = old_wbtip.last_access
                    else:
                        new_obj.last_access = old_obj.creation_date
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def migrate_Node(self):
        old_node = self.session_old.query(self.model_from['Node']).one()
        new_node = self.model_to['Node']()

        for key in [c.key for c in new_node.__table__.columns]:
            if key not in ['tb_download_link', 'wbtip_timetolive']:
                setattr(new_node, key, getattr(old_node, key))

        self.session_new.add(new_node)
