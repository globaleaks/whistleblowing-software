# -*- coding: utf-8 -*-
from storm.locals import Int, Bool, Unicode, DateTime, JSON

from globaleaks import __version__, DATABASE_VERSION, LANGUAGES_SUPPORTED_CODES, models
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.utils.utility import datetime_now, datetime_null



class Node_v_31(models.ModelWithID):
    __storm_table__ = 'node'
    version = Unicode(default=unicode(__version__))
    version_db = Unicode(default=unicode(DATABASE_VERSION))
    name = Unicode(default=u'')
    basic_auth = Bool(default=False)
    basic_auth_username = Unicode(default=u'')
    basic_auth_password = Unicode(default=u'')
    public_site = Unicode(default=u'')
    hidden_service = Unicode(default=u'')
    receipt_salt = Unicode()
    languages_enabled = JSON(default=LANGUAGES_SUPPORTED_CODES)
    default_language = Unicode(default=u'en')
    default_timezone = Int(default=0)
    description = JSON(default_factory=dict)
    presentation = JSON(default_factory=dict)
    footer = JSON(default_factory=dict)
    security_awareness_title = JSON(default_factory=dict)
    security_awareness_text = JSON(default_factory=dict)
    maximum_namesize = Int(default=128)
    maximum_textsize = Int(default=4096)
    maximum_filesize = Int(default=30)
    tor2web_admin = Bool(default=True)
    tor2web_custodian = Bool(default=True)
    tor2web_whistleblower = Bool(default=False)
    tor2web_receiver = Bool(default=True)
    tor2web_unauth = Bool(default=True)
    allow_unencrypted = Bool(default=False)
    disable_encryption_warnings = Bool(default=False)
    allow_iframes_inclusion = Bool(default=False)
    submission_minimum_delay = Int(default=10)
    submission_maximum_ttl = Int(default=10800)
    can_postpone_expiration = Bool(default=False)
    can_delete_submission = Bool(default=False)
    can_grant_permissions = Bool(default=False)
    ahmia = Bool(default=False)
    allow_indexing = Bool(default=False)
    wizard_done = Bool(default=False)
    disable_submissions = Bool(default=False)
    disable_privacy_badge = Bool(default=False)
    disable_security_awareness_badge = Bool(default=False)
    disable_security_awareness_questions = Bool(default=False)
    disable_key_code_hint = Bool(default=False)
    disable_donation_panel = Bool(default=False)
    enable_captcha = Bool(default=True)
    enable_proof_of_work = Bool(default=True)
    enable_experimental_features = Bool(default=False)
    whistleblowing_question = JSON(default_factory=dict)
    whistleblowing_button = JSON(default_factory=dict)
    whistleblowing_receipt_prompt = JSON(default_factory=dict)
    simplified_login = Bool(default=True)
    enable_custom_privacy_badge = Bool(default=False)
    custom_privacy_badge_tor = JSON(default_factory=dict)
    custom_privacy_badge_none = JSON(default_factory=dict)
    header_title_homepage = JSON(default_factory=dict)
    header_title_submissionpage = JSON(default_factory=dict)
    header_title_receiptpage = JSON(default_factory=dict)
    header_title_tippage = JSON(default_factory=dict)
    widget_comments_title = JSON(default_factory=dict)
    widget_messages_title = JSON(default_factory=dict)
    widget_files_title = JSON(default_factory=dict)
    landing_page = Unicode(default=u'homepage')
    contexts_clarification = JSON(default_factory=dict)
    show_small_context_cards = Bool(default=False)
    show_contexts_in_alphabetical_order = Bool(default=False)
    threshold_free_disk_megabytes_high = Int(default=200)
    threshold_free_disk_megabytes_medium = Int(default=500)
    threshold_free_disk_megabytes_low = Int(default=1000)
    threshold_free_disk_percentage_high = Int(default=3)
    threshold_free_disk_percentage_medium = Int(default=5)
    threshold_free_disk_percentage_low = Int(default=10)
    context_selector_type = Unicode(default=u'list')
    logo_id = Unicode()
    css_id = Unicode()


class User_v_31(models.ModelWithID):
    __storm_table__ = 'user'
    creation_date = DateTime(default_factory=datetime_now)
    username = Unicode()
    password = Unicode()
    salt = Unicode()
    deletable = Bool(default=True)
    name = Unicode()
    description = JSON()
    role = Unicode()
    state = Unicode()
    last_login = DateTime(default_factory=datetime_null)
    mail_address = Unicode()
    language = Unicode()
    timezone = Int()
    password_change_needed = Bool(default=True)
    password_change_date = DateTime(default_factory=datetime_null)
    pgp_key_info = Unicode(default=u'')
    pgp_key_fingerprint = Unicode(default=u'')
    pgp_key_public = Unicode(default=u'')
    pgp_key_expiration = DateTime(default_factory=datetime_null)
    pgp_key_status = Unicode(default=u'disabled') # 'disabled', 'enabled'
    img_id = Unicode()


class Comment_v_31(models.ModelWithID):
    __storm_table__ = 'comment'
    creation_date = DateTime(default_factory=datetime_now)
    internaltip_id = Unicode()
    author = Unicode()
    content = Unicode()
    type = Unicode()
    new = Int(default=True)


class Message_v_31(models.ModelWithID):
    __storm_table__ = 'message'
    creation_date = DateTime(default_factory=datetime_now)
    receivertip_id = Unicode()
    author = Unicode()
    content = Unicode()
    type = Unicode()
    new = Int(default=True)


class MigrationScript(MigrationBase):
    def migrate_File(self):
        old_node = self.store_old.find(self.model_from['Node']).one()

        old_objs = self.store_old.find(self.model_from['File'])
        for old_obj in old_objs:
            new_obj = self.model_to['File']()

            for _, v in new_obj._storm_columns.items():
                if v.name == 'id':
                    if old_obj.id == old_node.logo_id:
                        new_obj.id = 'logo'
                    elif old_obj.id == old_node.css_id:
                        new_obj.id = 'css'
                    else:
                        new_obj.id = old_obj.id
                else:
                    setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

    def migrate_Comment(self):
        old_objs = self.store_old.find(self.model_from['Comment'])
        for old_obj in old_objs:
            new_obj = self.model_to['Comment']()
            for _, v in new_obj._storm_columns.items():
                if v.name == 'author_id':
                    if old_obj.type == 'whistleblower':
                        continue

                    old_rtip_model = self.model_from['ReceiverTip']
                    old_rtips = self.store_old.find(old_rtip_model, old_rtip_model.internaltip_id == old_obj.internaltip_id)
                    if old_rtips.count() == 1:
                        new_obj.author_id = old_rtips.one().receiver.id
                    else:
                        old_user_model = self.model_from['User']
                        old_user = self.store_old.find(old_user_model, old_user_model.name == old_obj.author).one()
                        if old_user is not None:
                            new_obj.author_id = old_user.id

                else:
                    setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

    def migrate_User(self):
        old_objs = self.store_old.find(self.model_from['User'])
        for old_obj in old_objs:
            new_obj = self.model_to['User']()
            for _, v in new_obj._storm_columns.items():
                if v.name == 'public_name':
                    new_obj.public_name = old_obj.name
                else:
                    setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)
