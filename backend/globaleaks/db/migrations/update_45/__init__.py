# -*- coding: UTF-8
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import Model
from globaleaks.models.properties import *
from globaleaks.utils.utility import datetime_never, datetime_now, datetime_null


class Context_v_44(Model):
    __tablename__ = 'context'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    tid = Column(Integer, default=1, nullable=False)
    show_small_receiver_cards = Column(Boolean, default=False, nullable=False)
    show_context = Column(Boolean, default=True, nullable=False)
    show_recipients_details = Column(Boolean, default=False, nullable=False)
    allow_recipients_selection = Column(Boolean, default=False, nullable=False)
    maximum_selectable_receivers = Column(Integer, default=0, nullable=False)
    select_all_receivers = Column(Boolean, default=True, nullable=False)
    enable_comments = Column(Boolean, default=True, nullable=False)
    enable_messages = Column(Boolean, default=False, nullable=False)
    enable_two_way_comments = Column(Boolean, default=True, nullable=False)
    enable_two_way_messages = Column(Boolean, default=True, nullable=False)
    enable_attachments = Column(Boolean, default=True, nullable=False)
    enable_rc_to_wb_files = Column(Boolean, default=False, nullable=False)
    tip_timetolive = Column(Integer, default=30, nullable=False)
    name = Column(JSON, default=dict, nullable=False)
    description = Column(JSON, default=dict, nullable=False)
    recipients_clarification = Column(JSON, default=dict, nullable=False)
    status_page_message = Column(JSON, default=dict, nullable=False)
    show_receivers_in_alphabetical_order = Column(Boolean, default=True, nullable=False)
    presentation_order = Column(Integer, default=0, nullable=False)
    questionnaire_id = Column(UnicodeText(36), default=u'default', nullable=False)


class Field_v_44(Model):
    __tablename__ = 'field'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    tid = Column(Integer, default=1, nullable=False)
    x = Column(Integer, default=0, nullable=False)
    y = Column(Integer, default=0, nullable=False)
    width = Column(Integer, default=0, nullable=False)
    label = Column(JSON, nullable=False)
    description = Column(JSON, nullable=False)
    hint = Column(JSON, nullable=False)
    required = Column(Boolean, default=False, nullable=False)
    preview = Column(Boolean, default=False, nullable=False)
    multi_entry = Column(Boolean, default=False, nullable=False)
    multi_entry_hint = Column(JSON, nullable=False)
    stats_enabled = Column(Boolean, default=False, nullable=False)
    triggered_by_score = Column(Integer, default=0, nullable=False)
    template_id = Column(UnicodeText(36))
    fieldgroup_id = Column(UnicodeText(36))
    step_id = Column(UnicodeText(36))
    type = Column(UnicodeText, default=u'inputbox', nullable=False)
    instance = Column(UnicodeText, default=u'instance', nullable=False)
    editable = Column(Boolean, default=True, nullable=False)


class InternalTip_v_44(Model):
    __tablename__ = 'internaltip'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    tid = Column(Integer, default=1, nullable=False)
    content = Column(UnicodeText, default=u'')
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    update_date = Column(DateTime, default=datetime_now, nullable=False)
    context_id = Column(UnicodeText(36), nullable=False)
    questionnaire_hash = Column(UnicodeText(64), nullable=False)
    preview = Column(JSON, nullable=False)
    progressive = Column(Integer, default=0, nullable=False)
    https = Column(Boolean, default=False, nullable=False)
    total_score = Column(Integer, default=0, nullable=False)
    expiration_date = Column(DateTime, nullable=False)
    identity_provided = Column(Boolean, default=False, nullable=False)
    identity_provided_date = Column(DateTime, default=datetime_null, nullable=False)
    enable_two_way_comments = Column(Boolean, default=True, nullable=False)
    enable_two_way_messages = Column(Boolean, default=True, nullable=False)
    enable_attachments = Column(Boolean, default=True, nullable=False)
    enable_whistleblower_identity = Column(Boolean, default=False, nullable=False)
    wb_last_access = Column(DateTime, default=datetime_now, nullable=False)
    wb_access_counter = Column(Integer, default=0, nullable=False)
    status = Column(UnicodeText(36), nullable=False)
    substatus = Column(UnicodeText(36), nullable=True)


class ReceiverFile_v_44(Model):
    __tablename__ = 'receiverfile'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    internalfile_id = Column(UnicodeText(36), nullable=False)
    receivertip_id = Column(UnicodeText(36), nullable=False)
    filename = Column(UnicodeText(255), nullable=False)
    size = Column(Integer, nullable=False)
    downloads = Column(Integer, default=0, nullable=False)
    last_access = Column(DateTime, default=datetime_null, nullable=False)
    new = Column(Integer, default=True, nullable=False)
    status = Column(UnicodeText, nullable=False)


class ReceiverTip_v_44(Model):
    __tablename__ = 'receivertip'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    internaltip_id = Column(UnicodeText(36), nullable=False)
    receiver_id = Column(UnicodeText(36), nullable=False)
    last_access = Column(DateTime, default=datetime_null, nullable=False)
    access_counter = Column(Integer, default=0, nullable=False)
    label = Column(UnicodeText, default=u'', nullable=False)
    can_access_whistleblower_identity = Column(Boolean, default=False, nullable=False)
    new = Column(Integer, default=True, nullable=False)
    enable_notifications = Column(Boolean, default=True, nullable=False)


class Step_v_44(Model):
    __tablename__ = 'step'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    questionnaire_id = Column(UnicodeText(36), nullable=True)
    label = Column(JSON, nullable=False)
    description = Column(JSON, nullable=False)
    presentation_order = Column(Integer, default=0, nullable=False)


class User_v_44(Model):
    __tablename__ = 'user'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    tid = Column(Integer, default=1, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    username = Column(UnicodeText, default=u'', nullable=False)
    salt = Column(UnicodeText(24), nullable=False)
    password = Column(UnicodeText, default=u'', nullable=False)
    name = Column(UnicodeText, default=u'', nullable=False)
    description = Column(JSON, default=dict, nullable=False)
    role = Column(UnicodeText, default=u'receiver', nullable=False)
    state = Column(UnicodeText, default=u'enabled', nullable=False)
    last_login = Column(DateTime, default=datetime_null, nullable=False)
    mail_address = Column(UnicodeText, default=u'', nullable=False)
    language = Column(UnicodeText, nullable=False)
    password_change_needed = Column(Boolean, default=True, nullable=False)
    password_change_date = Column(DateTime, default=datetime_null, nullable=False)
    auth_token = Column(UnicodeText, default=u'', nullable=False)
    can_edit_general_settings = Column(Boolean, default=False, nullable=False)
    change_email_address = Column(UnicodeText, default=u'', nullable=False)
    change_email_token = Column(UnicodeText, unique=True, nullable=True)
    change_email_date = Column(DateTime, default=datetime_never, nullable=False)
    reset_password_token = Column(UnicodeText, unique=True, nullable=True)
    reset_password_date = Column(UnicodeText, default=datetime_never, nullable=False)
    pgp_key_fingerprint = Column(UnicodeText, default=u'', nullable=False)
    pgp_key_public = Column(UnicodeText, default=u'', nullable=False)
    pgp_key_expiration = Column(DateTime, default=datetime_null, nullable=False)


class WhistleblowerFile_v_44(Model):
    __tablename__ = 'whistleblowerfile'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    receivertip_id = Column(UnicodeText(36), nullable=False)
    name = Column(UnicodeText, nullable=False)
    filename = Column(UnicodeText(255), nullable=False)
    size = Column(Integer, nullable=False)
    content_type = Column(UnicodeText, nullable=False)
    downloads = Column(Integer, default=0, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    last_access = Column(DateTime, default=datetime_null, nullable=False)
    description = Column(UnicodeText, nullable=False)


class WhistleblowerTip_v_44(Model):
    __tablename__ = 'whistleblowertip'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    tid = Column(Integer, default=1, nullable=False)
    receipt_hash = Column(UnicodeText(128), nullable=False)


class MigrationScript(MigrationBase):
    def migrate_FieldAttr(self):
        old_objs = self.session_old.query(self.model_from['FieldAttr'])
        for old_obj in old_objs:
            new_obj = self.model_to['FieldAttr']()
            for key in [c.key for c in new_obj.__table__.columns]:
                setattr(new_obj, key, getattr(old_obj, key))

            if new_obj.type == 'bool':
                new_obj.value = new_obj.value == u'True'
                print(isinstance(new_obj.value, bool))

            self.session_new.add(new_obj)

    def migrate_User(self):
        old_objs = self.session_old.query(self.model_from['User'])
        for old_obj in old_objs:
            new_obj = self.model_to['User']()
            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'hash_alg':
                    new_obj.hash_alg = 'SCRYPT'
                elif key in ['crypto_pub_key', 'crypto_prv_key',]:
                    continue
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def migrate_WhistleblowerTip(self):
        old_objs = self.session_old.query(self.model_from['WhistleblowerTip'])
        for old_obj in old_objs:
            new_obj = self.model_to['WhistleblowerTip']()
            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'hash_alg':
                    new_obj.hash_alg = 'SCRYPT'
                elif key in ['crypto_pub_key', 'crypto_prv_key', 'crypto_tip_prv_key']:
                    continue
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def epilogue(self):
        if self.session_new.query(self.model_from['Tenant']).count() > 1:
            config = self.session_old.query(self.model_from['Config']).filter(self.model_from['Config'].var_name == u'multisite')
            config.value = True