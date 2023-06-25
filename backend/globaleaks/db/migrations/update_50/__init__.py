# -*- coding: UTF-8
from globaleaks.db.migrations.update import MigrationBase

from globaleaks.models import Model
from globaleaks.models.properties import *
from globaleaks.utils.utility import datetime_now, datetime_null


class SubmissionStatus_v_49(Model):
    __tablename__ = 'submissionstatus'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    tid = Column(Integer, default=1, nullable=False)
    label = Column(JSON, default=dict, nullable=False)
    system_defined = Column(Boolean, nullable=False, default=False)
    system_usage = Column(UnicodeText, nullable=True)
    presentation_order = Column(Integer, default=0, nullable=False)


class SubmissionSubStatus_v_49(Model):
    __tablename__ = 'submissionsubstatus'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    submissionstatus_id = Column(UnicodeText(36), nullable=False)
    label = Column(JSON, default=dict, nullable=False)
    presentation_order = Column(Integer, default=0, nullable=False)


class User_v_49(Model):
    __tablename__ = 'user'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    tid = Column(Integer, default=1, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    username = Column(UnicodeText, default='', nullable=False)
    salt = Column(UnicodeText(24), nullable=False)
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
    notification = Column(Boolean, default=True, nullable=False)
    recipient_configuration = Column(UnicodeText, default='default', nullable=False)
    can_delete_submission = Column(Boolean, default=False, nullable=False)
    can_postpone_expiration = Column(Boolean, default=False, nullable=False)
    can_edit_general_settings = Column(Boolean, default=False, nullable=False)
    pgp_key_fingerprint = Column(UnicodeText, default='', nullable=False)
    pgp_key_public = Column(UnicodeText, default='', nullable=False)
    pgp_key_expiration = Column(DateTime, default=datetime_null, nullable=False)


class MigrationScript(MigrationBase):
    status_map = {}

    def migrate_SubmissionStatus(self):
        for old_obj in self.session_old.query(self.model_from['SubmissionStatus']):
            new_obj = self.model_to['SubmissionStatus']()
            for key in new_obj.__mapper__.column_attrs.keys():
                setattr(new_obj, key, getattr(old_obj, key))

            if old_obj.system_defined:
                new_obj.id = old_obj.system_usage
                if old_obj.system_usage == 'open':
                    new_obj.id = 'opened'
                    new_obj.label = {'en': 'Opened'}

                self.status_map[old_obj.id] = new_obj.id

            self.session_new.add(new_obj)

    def migrate_SubmissionSubStatus(self):
        for old_obj in self.session_old.query(self.model_from['SubmissionSubStatus']):
            new_obj = self.model_to['SubmissionSubStatus']()
            for key in new_obj.__mapper__.column_attrs.keys():
                if key == 'tid':
                    p_model = self.model_from['SubmissionStatus']
                    p = self.session_old.query(p_model).filter(p_model.id == old_obj.submissionstatus_id).one()
                    new_obj.tid = p.tid
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            if old_obj.submissionstatus_id in self.status_map:
                new_obj.submissionstatus_id = 'closed'

            self.session_new.add(new_obj)

    def migrate_User(self):
        for old_obj in self.session_old.query(self.model_from['User']):
            new_obj = self.model_to['User']()
            for key in new_obj.__mapper__.column_attrs.keys():
                if hasattr(old_obj, key):
                    setattr(new_obj, key, getattr(old_obj, key))

            if new_obj.recipient_configuration == 'unselectable':
                new_obj.state = 'disabled'
                new_obj.recipient_configuration = 'default'

            self.session_new.add(new_obj)

    def epilogue(self):
        for obj in self.session_new.query(self.model_to['InternalTip']):
            if obj.status in self.status_map:
                obj.status = self.status_map[obj.status]
