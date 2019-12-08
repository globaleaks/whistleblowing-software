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
    tip_timetolive = Column(Integer, default=90, nullable=False)
    tip_timetolive_override = Column(Boolean, default=False, nullable=False)
    receivers = Column(JSON, default=list, nullable=False)
    presentation_order = Column(Integer, default=0, nullable=False)


class SubmissionSubStatus_v_49(Model):
    __tablename__ = 'submissionsubstatus'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    submissionstatus_id = Column(UnicodeText(36), nullable=False)
    label = Column(JSON, default=dict, nullable=False)
    tip_timetolive = Column(Integer, default=90, nullable=False)
    tip_timetolive_override = Column(Boolean, default=False, nullable=False)
    receivers = Column(JSON, default=list, nullable=False)
    presentation_order = Column(Integer, default=0, nullable=False)


class User_v_49(Model):
    __tablename__ = 'user'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
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
    last_login = Column(DateTime, default=datetime_null, nullable=False)
    mail_address = Column(UnicodeText, default='', nullable=False)
    language = Column(UnicodeText, nullable=False)
    password_change_needed = Column(Boolean, default=True, nullable=False)
    password_change_date = Column(DateTime, default=datetime_null, nullable=False)
    crypto_prv_key = Column(LargeBinary(72), default=b'', nullable=False)
    crypto_pub_key = Column(LargeBinary(32), default=b'', nullable=False)
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
    pgp_key_fingerprint = Column(UnicodeText, default='', nullable=False)
    pgp_key_public = Column(UnicodeText, default='', nullable=False)
    pgp_key_expiration = Column(DateTime, default=datetime_null, nullable=False)

    binary_keys = ['crypto_prv_key', 'crypto_pub_key']


class MigrationScript(MigrationBase):
    status_map = {}

    def migrate_Signup(self):
        old_objs = self.session_old.query(self.model_from['Signup'])
        for old_obj in old_objs:
            new_obj = self.model_to['Signup']()
            for key in [c.key for c in new_obj.__table__.columns]:
                setattr(new_obj, key, getattr(old_obj, key))

            new_obj.activation_token = ''

            self.session_new.add(new_obj)

    def migrate_SubmissionStatus(self):
        old_objs = self.session_old.query(self.model_from['SubmissionStatus'])
        for old_obj in old_objs:
            new_obj = self.model_to['SubmissionStatus']()
            for key in [c.key for c in new_obj.__table__.columns]:
                setattr(new_obj, key, getattr(old_obj, key))

            if old_obj.system_defined:
                new_obj.id = old_obj.system_usage
                if old_obj.system_usage == 'open':
                    new_obj.id = 'opened'
                    new_obj.label = {'en': 'Opened'}

                self.status_map[old_obj.id] = new_obj.id

            self.session_new.add(new_obj)

    def migrate_SubmissionSubStatus(self):
        old_objs = self.session_old.query(self.model_from['SubmissionSubStatus'])
        for old_obj in old_objs:
            new_obj = self.model_to['SubmissionSubStatus']()
            for key in [c.key for c in new_obj.__table__.columns]:
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
        old_objs = self.session_old.query(self.model_from['User'])
        for old_obj in old_objs:
            new_obj = self.model_to['User']()
            old_keys = [c.key for c in old_obj.__table__.columns]
            for key in [c.key for c in new_obj.__table__.columns]:
                if key in old_keys:
                    setattr(new_obj, key, getattr(old_obj, key))

            if new_obj.recipient_configuration == 'unselectable':
                new_obj.state = 'disabled'
                new_obj.recipient_configuration = 'default'

            self.session_new.add(new_obj)

    def epilogue(self):
        objs = self.session_new.query(self.model_to['InternalTip'])
        for obj in objs:
            if obj.status in self.status_map:
                obj.status = self.status_map[obj.status]
