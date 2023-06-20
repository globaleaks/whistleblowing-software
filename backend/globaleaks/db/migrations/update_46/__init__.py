# -*- coding: UTF-8
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.handlers.submission import db_assign_submission_progressive
from globaleaks.models import Model
from globaleaks.models.properties import *
from globaleaks.utils.utility import datetime_never, datetime_now, datetime_null


class Config_v_45(Model):
    __tablename__ = 'config'
    tid = Column(Integer, primary_key=True, default=1, nullable=False)
    var_name = Column(UnicodeText(64), primary_key=True, nullable=False)
    value = Column(JSON, nullable=False)
    customized = Column(Boolean, default=False, nullable=False)


class ConfigL10N_v_45(Model):
    __tablename__ = 'config_l10n'
    tid = Column(Integer, primary_key=True, default=1, nullable=False)
    lang = Column(UnicodeText(5), primary_key=True)
    var_name = Column(UnicodeText(64), primary_key=True)
    value = Column(UnicodeText)
    customized = Column(Boolean, default=False)

    def __init__(self, values=None, migrate=False):
        return


class Context_v_45(Model):
    __tablename__ = 'context'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    tid = Column(Integer, default=1, nullable=False)
    show_steps_navigation_interface = Column(Boolean, default=True, nullable=False)
    show_context = Column(Boolean, default=True, nullable=False)
    show_recipients_details = Column(Boolean, default=False, nullable=False)
    allow_recipients_selection = Column(Boolean, default=False, nullable=False)
    maximum_selectable_receivers = Column(Integer, default=0, nullable=False)
    select_all_receivers = Column(Boolean, default=True, nullable=False)
    enable_two_way_comments = Column(Boolean, default=True, nullable=False)
    enable_attachments = Column(Boolean, default=True, nullable=False)
    tip_timetolive = Column(Integer, default=30, nullable=False)
    name = Column(JSON, default=dict, nullable=False)
    description = Column(JSON, default=dict, nullable=False)
    show_receivers_in_alphabetical_order = Column(Boolean, default=True, nullable=False)
    presentation_order = Column(Integer, default=0, nullable=False)
    questionnaire_id = Column(UnicodeText(36), default='default', nullable=False)
    additional_questionnaire_id = Column(UnicodeText(36))


class FieldOption_v_45(Model):
    __tablename__ = 'fieldoption'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    field_id = Column(UnicodeText(36), nullable=False)
    presentation_order = Column(Integer, default=0, nullable=False)
    label = Column(JSON, nullable=False)
    score_points = Column(Integer, default=0, nullable=False)
    trigger_field = Column(UnicodeText(36))


class Field_v_45(Model):
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
    triggered_by_score = Column(Integer, default=0, nullable=False)
    step_id = Column(UnicodeText(36))
    fieldgroup_id = Column(UnicodeText(36))
    type = Column(UnicodeText, default='inputbox', nullable=False)
    instance = Column(UnicodeText, default='instance', nullable=False)
    template_id = Column(UnicodeText(36))
    template_override_id = Column(UnicodeText(36))


class InternalFile_v_45(Model):
    __tablename__ = 'internalfile'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    internaltip_id = Column(UnicodeText(36), nullable=False)
    name = Column(UnicodeText, nullable=False)
    filename = Column(UnicodeText(255), nullable=False)
    content_type = Column(UnicodeText, nullable=False)
    size = Column(Integer, nullable=False)
    new = Column(Integer, default=True, nullable=False)
    submission = Column(Integer, default=False, nullable=False)


class InternalTip_v_45(Model):
    __tablename__ = 'internaltip'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    tid = Column(Integer, default=1, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    update_date = Column(DateTime, default=datetime_now, nullable=False)
    context_id = Column(UnicodeText(36), nullable=False)
    progressive = Column(Integer, default=0, nullable=False)
    https = Column(Boolean, default=False, nullable=False)
    total_score = Column(Integer, default=0, nullable=False)
    expiration_date = Column(DateTime, nullable=False)
    enable_two_way_comments = Column(Boolean, default=True, nullable=False)
    enable_attachments = Column(Boolean, default=True, nullable=False)
    enable_whistleblower_identity = Column(Boolean, default=False, nullable=False)
    wb_last_access = Column(DateTime, default=datetime_now, nullable=False)
    status = Column(UnicodeText(36), nullable=True)
    substatus = Column(UnicodeText(36), nullable=True)


class Receiver_v_45(Model):
    __tablename__ = 'receiver'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    configuration = Column(UnicodeText, default='default', nullable=False)
    can_delete_submission = Column(Boolean, default=False, nullable=False)
    can_postpone_expiration = Column(Boolean, default=False, nullable=False)


class User_v_45(Model):
    __tablename__ = 'user'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    tid = Column(Integer, default=1, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    username = Column(UnicodeText, default='', nullable=False)
    salt = Column(UnicodeText(24), nullable=False)
    hash_alg = Column(UnicodeText, default='SCRYPT', nullable=False)
    password = Column(UnicodeText, default='', nullable=False)
    name = Column(UnicodeText, default='', nullable=False)
    description = Column(JSON, default=dict, nullable=False)
    role = Column(UnicodeText, default='receiver', nullable=False)
    state = Column(UnicodeText, default='enabled', nullable=False)
    last_login = Column(DateTime, default=datetime_never, nullable=False)
    mail_address = Column(UnicodeText, default='', nullable=False)
    language = Column(UnicodeText, nullable=False)
    password_change_needed = Column(Boolean, default=True, nullable=False)
    password_change_date = Column(DateTime, default=datetime_never, nullable=False)
    change_email_address = Column(UnicodeText, default='', nullable=False)
    change_email_token = Column(UnicodeText, unique=True, nullable=True)
    change_email_date = Column(DateTime, default=datetime_never, nullable=False)
    notification = Column(Boolean, default=True, nullable=False)
    pgp_key_fingerprint = Column(UnicodeText, default='', nullable=False)
    pgp_key_public = Column(UnicodeText, default='', nullable=False)
    pgp_key_expiration = Column(DateTime, default=datetime_never, nullable=False)
    can_edit_general_settings = Column(Boolean, default=False, nullable=False)


class WhistleblowerFile_v_45(Model):
    __tablename__ = 'whistleblowerfile'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    receivertip_id = Column(UnicodeText(36), nullable=False)
    name = Column(UnicodeText, nullable=False)
    filename = Column(UnicodeText(255), nullable=False)
    size = Column(Integer, nullable=False)
    content_type = Column(UnicodeText, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    last_access = Column(DateTime, default=datetime_null, nullable=False)
    description = Column(UnicodeText, nullable=False)
    new = Column(Integer, default=True, nullable=True)


class MigrationScript(MigrationBase):
    def _migrate_Config(self, name):
        for old_obj in self.session_old.query(self.model_from[name]):
            new_obj = self.model_to[name]()
            for key in new_obj.__mapper__.column_attrs.keys():
                if key == 'update_date':
                    if old_obj.customized:
                        new_obj.update_date = datetime_now()
                    else:
                        new_obj.update_date = datetime_null()

                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def _migrate_File(self, name):
        filenames = {}
        for old_obj in self.session_old.query(self.model_from[name]):
            if old_obj.filename in filenames:
                self.entries_count[name] -= 1
                continue

            filenames[old_obj.filename] = True

            new_obj = self.model_to[name]()
            for key in new_obj.__mapper__.column_attrs.keys():
                setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def migrate_Config(self):
        self._migrate_Config('Config')

    def migrate_ConfigL10N(self):
        self._migrate_Config('ConfigL10N')

    def migrate_Context(self):
        for old_obj in self.session_old.query(self.model_from['Context']):
            new_obj = self.model_to['Context']()
            for key in new_obj.__mapper__.column_attrs.keys():
                if key == 'status':
                    new_obj.status = 1 if old_obj.show_context else 2
                elif hasattr(old_obj, key):
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def migrate_InternalTip(self):
        ids = {}
        for old_obj in self.session_old.query(self.model_from['InternalTip']):
            new_obj = self.model_to['InternalTip']()
            for key in new_obj.__mapper__.column_attrs.keys():
                setattr(new_obj, key, getattr(old_obj, key))

            if new_obj.progressive in ids:
                new_obj.progressive = db_assign_submission_progressive(self.session_new, new_obj.tid)

            ids[new_obj.progressive] = True

            self.session_new.add(new_obj)

    def migrate_InternalFile(self):
        self._migrate_File('InternalFile')

    def migrate_WhistleblowerFile(self):
        self._migrate_File('WhistleblowerFile')

    def migrate_User(self):
        for old_obj in self.session_old.query(self.model_from['User']):
            receiver = self.session_old.query(self.model_from['Receiver']).filter(self.model_from['Receiver'].id == old_obj.id).one_or_none()
            new_obj = self.model_to['User']()
            for key in new_obj.__mapper__.column_attrs.keys():
                if key in ['can_delete_submission', 'can_postpone_expiration']:
                    if receiver is not None:
                        setattr(new_obj, key, getattr(receiver, key))
                elif key == 'recipient_configuration':
                    if receiver is not None:
                        setattr(new_obj, key, receiver.configuration)
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def epilogue(self):
        for t in self.session_new.query(self.model_to['Tenant']):
            m = self.model_to['Config']
            a = self.session_new.query(m.value).filter(m.tid == t.id, m.var_name == 'ip_filter_authenticated_enable').one_or_none()
            b = self.session_new.query(m.value).filter(m.tid == t.id, m.var_name == 'ip_filter_authenticated').one_or_none()

            if a is not None or b is not None:
                for c in ['admin', 'custodian', 'receiver']:
                    self.session_new.add(self.model_to['Config']({'tid': t.id, 'var_name': 'ip_filter_' + c + '_enable', 'value': a[0]}))
                    self.session_new.add(self.model_to['Config']({'tid': t.id, 'var_name': 'ip_filter_' + c, 'value': b[0]}))
                    self.entries_count['Config'] += 2

        for obj in self.session_new.query(self.model_to['FieldOption']).filter(self.model_to['FieldOption'].score_points != 0):
            obj.score_type = 1
