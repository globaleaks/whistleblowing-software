# -*- coding: UTF-8
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import Model
from globaleaks.models.properties import *
from globaleaks.utils.crypto import Base64Encoder
from globaleaks.utils.utility import datetime_now, datetime_never, datetime_null


class Field_v_51(Model):
    __tablename__ = 'field'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    tid = Column(Integer, default=1, nullable=False)
    x = Column(Integer, default=0, nullable=False)
    y = Column(Integer, default=0, nullable=False)
    width = Column(Integer, default=0, nullable=False)
    label = Column(JSON, default=dict, nullable=False)
    description = Column(JSON, default=dict, nullable=False)
    hint = Column(JSON, default=dict, nullable=False)
    placeholder = Column(JSON, default=dict, nullable=False)
    required = Column(Boolean, default=False, nullable=False)
    preview = Column(Boolean, default=False, nullable=False)
    multi_entry = Column(Boolean, default=False, nullable=False)
    multi_entry_hint = Column(JSON, default=dict, nullable=False)
    triggered_by_score = Column(Integer, default=0, nullable=False)
    step_id = Column(UnicodeText(36))
    fieldgroup_id = Column(UnicodeText(36))
    type = Column(UnicodeText, default='inputbox', nullable=False)
    instance = Column(UnicodeText, default='instance', nullable=False)
    editable = Column(Boolean, default=True, nullable=False)
    template_id = Column(UnicodeText(36))
    template_override_id = Column(UnicodeText(36), nullable=True)


class InternalTip_v_51(Model):
    __tablename__ = 'internaltip'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    tid = Column(Integer, default=1, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    update_date = Column(DateTime, default=datetime_now, nullable=False)
    context_id = Column(UnicodeText(36), nullable=False)
    preview = Column(JSON, default=dict, nullable=False)
    progressive = Column(Integer, default=0, nullable=False)
    https = Column(Boolean, default=False, nullable=False)
    mobile = Column(Boolean, default=False, nullable=False)
    total_score = Column(Integer, default=0, nullable=False)
    expiration_date = Column(DateTime, default=datetime_never, nullable=False)
    enable_two_way_comments = Column(Boolean, default=True, nullable=False)
    enable_two_way_messages = Column(Boolean, default=True, nullable=False)
    enable_attachments = Column(Boolean, default=True, nullable=False)
    enable_whistleblower_identity = Column(Boolean, default=False, nullable=False)
    additional_questionnaire_id = Column(UnicodeText(36))
    wb_last_access = Column(DateTime, default=datetime_now, nullable=False)
    wb_access_counter = Column(Integer, default=0, nullable=False)
    status = Column(UnicodeText(36), nullable=True)
    substatus = Column(UnicodeText(36), nullable=True)


class SubmissionStatus_v_51(Model):
    __tablename__ = 'submissionstatus'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    tid = Column(Integer, primary_key=True, default=1, nullable=False)
    label = Column(JSON, default=dict, nullable=False)
    system_defined = Column(Boolean, nullable=False, default=False)
    tip_timetolive = Column(Integer, default=90, nullable=False)
    tip_timetolive_override = Column(Boolean, default=False, nullable=False)
    receivers = Column(JSON, default=list, nullable=False)
    presentation_order = Column(Integer, default=0, nullable=False)


class User_v_51(Model):
    __tablename__ = 'user'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    tid = Column(Integer, default=1, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    username = Column(UnicodeText, default='', nullable=False)
    salt = Column(UnicodeText(24), nullable=False)
    hash_alg = Column(UnicodeText, default='ARGON2', nullable=False)
    password = Column(UnicodeText, default='', nullable=False)
    name = Column(UnicodeText, default='', nullable=False)
    description = Column(JSON, default=dict, nullable=False)
    role = Column(UnicodeText, default='receiver', nullable=False)
    state = Column(UnicodeText, default='enabled', nullable=False)
    last_login = Column(DateTime, default=datetime_null, nullable=False)
    mail_address = Column(UnicodeText, default='', nullable=False)
    language = Column(UnicodeText, nullable=False)
    password_change_needed = Column(Boolean, default=True, nullable=False)
    password_change_date = Column(DateTime, default=datetime_null, nullable=False)
    change_email_address = Column(UnicodeText, default='', nullable=False)
    change_email_token = Column(UnicodeText, unique=True, nullable=True)
    change_email_date = Column(DateTime, default=datetime_null, nullable=False)
    reset_password_token = Column(UnicodeText, unique=True, nullable=True)
    reset_password_date = Column(UnicodeText, default=datetime_null, nullable=False)
    notification = Column(Boolean, default=True, nullable=False)
    recipient_configuration = Column(UnicodeText, default='default', nullable=False)
    can_delete_submission = Column(Boolean, default=False, nullable=False)
    can_postpone_expiration = Column(Boolean, default=False, nullable=False)
    can_grant_permissions = Column(Boolean, default=False, nullable=False)
    can_edit_general_settings = Column(Boolean, default=False, nullable=False)
    two_factor_enable = Column(Boolean, default=False, nullable=False)
    two_factor_secret = Column(LargeBinary(64), default=b'', nullable=False)
    pgp_key_fingerprint = Column(UnicodeText, default='', nullable=False)
    pgp_key_public = Column(UnicodeText, default='', nullable=False)
    pgp_key_expiration = Column(DateTime, default=datetime_null, nullable=False)


class MigrationScript(MigrationBase):
    skip_count_check = {
        'Config': True
    }

    def migrate_Signup(self):
        for old_obj in self.session_old.query(self.model_from['Signup']):
            new_obj = self.model_to['Signup']()
            for key in new_obj.__table__.columns._data.keys():
                if key == 'activation_token' and old_obj.activation_token == '':
                    new_obj.activation_token = None
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def migrate_User(self):
        x = self.session_old.query(self.model_from['Config'].value).filter(self.model_from['Config'].tid == 1, self.model_from['Config'].var_name == 'do_not_expose_users_names').one_or_none()
        x = x[0] if x is not None else False

        platform_name = self.session_new.query(self.model_from['Config'].value).filter(self.model_from['Config'].tid == 1, self.model_from['Config'].var_name == 'name').one()[0]

        for old_obj in self.session_old.query(self.model_from['User']):
            new_obj = self.model_to['User']()
            for key in new_obj.__table__.columns._data.keys():
                if key.startswith('crypto_') or key == 'readonly':
                    continue
                elif key == 'two_factor_secret':
                    if old_obj.two_factor_secret:
                        new_obj.two_factor_secret = Base64Encoder.encode(old_obj.two_factor_secret)
                elif key == 'public_name':
                    if x:
                        new_obj.public_name = platform_name
                    else:
                        new_obj.public_name = old_obj.name
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)


    def epilogue(self):
        # This migration epilogue is necessary because the default variable of the variables is
        # the opposite of what it is necessary to be configured on migrated nodes
        self.session_new.query(self.model_to['Config']).filter(self.model_to['Config'].var_name.in_(['encryption'])).delete(synchronize_session='fetch')

        for t in self.session_new.query(self.model_from['Tenant']):
            self.session_new.add(self.model_to['Config']({'tid': t.id, 'var_name': 'encryption', 'value': False}))
            self.session_new.add(self.model_to['Config']({'tid': t.id, 'var_name': 'escrow', 'value': False}))
