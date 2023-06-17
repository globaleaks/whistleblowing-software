# -*- coding: utf-8 -*-
from globaleaks import __version__, DATABASE_VERSION, LANGUAGES_SUPPORTED_CODES, models
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models.properties import *
from globaleaks.utils.utility import datetime_now, datetime_null


class Node_v_31(models.Model):
    __tablename__ = 'node'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    version = Column(UnicodeText, default=str(__version__))
    version_db = Column(UnicodeText, default=str(DATABASE_VERSION))
    name = Column(UnicodeText, default='')
    basic_auth = Column(Boolean, default=False)
    basic_auth_username = Column(UnicodeText, default='')
    basic_auth_password = Column(UnicodeText, default='')
    public_site = Column(UnicodeText, default='')
    hidden_service = Column(UnicodeText, default='')
    receipt_salt = Column(UnicodeText)
    languages_enabled = Column(JSON, default=LANGUAGES_SUPPORTED_CODES)
    default_language = Column(UnicodeText, default='en')
    default_timezone = Column(Integer, default=0)
    description = Column(JSON, default=dict)
    presentation = Column(JSON, default=dict)
    footer = Column(JSON, default=dict)
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
    can_postpone_expiration = Column(Boolean, default=False)
    can_delete_submission = Column(Boolean, default=False)
    can_grant_permissions = Column(Boolean, default=False)
    allow_indexing = Column(Boolean, default=False)
    wizard_done = Column(Boolean, default=False)
    disable_submissions = Column(Boolean, default=False)
    disable_privacy_badge = Column(Boolean, default=False)
    disable_key_code_hint = Column(Boolean, default=False)
    enable_captcha = Column(Boolean, default=True)
    whistleblowing_question = Column(JSON, default=dict)
    whistleblowing_button = Column(JSON, default=dict)
    simplified_login = Column(Boolean, default=True)
    enable_custom_privacy_badge = Column(Boolean, default=False)
    header_title_homepage = Column(JSON, default=dict)
    header_title_submissionpage = Column(JSON, default=dict)
    header_title_receiptpage = Column(JSON, default=dict)
    header_title_tippage = Column(JSON, default=dict)
    landing_page = Column(UnicodeText, default='homepage')
    contexts_clarification = Column(JSON, default=dict)
    show_small_context_cards = Column(Boolean, default=False)
    show_contexts_in_alphabetical_order = Column(Boolean, default=False)
    threshold_free_disk_megabytes_high = Column(Integer, default=200)
    threshold_free_disk_megabytes_medium = Column(Integer, default=500)
    threshold_free_disk_megabytes_low = Column(Integer, default=1000)
    threshold_free_disk_percentage_high = Column(Integer, default=3)
    threshold_free_disk_percentage_medium = Column(Integer, default=5)
    threshold_free_disk_percentage_low = Column(Integer, default=10)
    context_selector_type = Column(UnicodeText, default='list')
    logo_id = Column(UnicodeText(36))
    css_id = Column(UnicodeText(36))


class User_v_31(models.Model):
    __tablename__ = 'user'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    creation_date = Column(DateTime, default=datetime_now)
    username = Column(UnicodeText)
    password = Column(UnicodeText)
    salt = Column(UnicodeText)
    name = Column(UnicodeText)
    description = Column(JSON)
    role = Column(UnicodeText)
    state = Column(UnicodeText)
    last_login = Column(DateTime, default=datetime_null)
    mail_address = Column(UnicodeText)
    language = Column(UnicodeText)
    timezone = Column(Integer)
    password_change_needed = Column(Boolean, default=True)
    password_change_date = Column(DateTime, default=datetime_null)
    pgp_key_fingerprint = Column(UnicodeText, default='')
    pgp_key_public = Column(UnicodeText, default='')
    pgp_key_expiration = Column(DateTime, default=datetime_null)
    img_id = Column(UnicodeText(36))


class Comment_v_31(models.Model):
    __tablename__ = 'comment'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    creation_date = Column(DateTime, default=datetime_now)
    internaltip_id = Column(UnicodeText(36))
    author = Column(UnicodeText)
    content = Column(UnicodeText)
    type = Column(UnicodeText)
    new = Column(Integer, default=True)


class Message_v_31(models.Model):
    __tablename__ = 'message'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    creation_date = Column(DateTime, default=datetime_now)
    receivertip_id = Column(UnicodeText(36))
    author = Column(UnicodeText)
    content = Column(UnicodeText)
    type = Column(UnicodeText)
    new = Column(Integer, default=True)


class MigrationScript(MigrationBase):
    def migrate_File(self):
        old_node = self.session_old.query(self.model_from['Node']).one()

        for old_obj in self.session_old.query(self.model_from['File']):
            new_obj = self.model_to['File']()

            for key in new_obj.__mapper__.column_attrs.keys():
                if key == 'id':
                    if old_obj.id == old_node.logo_id:
                        new_obj.id = 'logo'
                    elif old_obj.id == old_node.css_id:
                        new_obj.id = 'css'
                    else:
                        new_obj.id = old_obj.id
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def migrate_Comment(self):
        for old_obj in self.session_old.query(self.model_from['Comment']):
            new_obj = self.model_to['Comment']()
            for key in new_obj.__mapper__.column_attrs.keys():
                if key == 'author_id':
                    if old_obj.type == 'whistleblower':
                        continue

                    old_rtip_model = self.model_from['ReceiverTip']
                    old_rtips = self.session_old.query(old_rtip_model).filter(old_rtip_model.internaltip_id == old_obj.internaltip_id)
                    if old_rtips.count() == 1:
                        new_obj.author_id = old_rtips.one().receiver.id
                    else:
                        old_user_model = self.model_from['User']
                        old_user = self.session_old.query(old_user_model).filter(old_user_model.name == old_obj.author).one()
                        if old_user is not None:
                            new_obj.author_id = old_user.id

                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)
