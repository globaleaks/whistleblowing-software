# -*- coding: UTF-8
import os

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import Model
from globaleaks.models.properties import *
from globaleaks.utils.utility import datetime_now, datetime_null


class InternalFile_v_40(Model):
    __tablename__ = 'internalfile'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    internaltip_id = Column(UnicodeText(36), nullable=False)
    name = Column(UnicodeText, nullable=False)
    file_path = Column(UnicodeText, nullable=False)
    content_type = Column(UnicodeText, nullable=False)
    size = Column(Integer, nullable=False)
    new = Column(Integer, default=True, nullable=False)
    submission = Column(Integer, default=False, nullable=False)


class InternalTip_v_40(Model):
    __tablename__ = 'internaltip'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    tid = Column(Integer, default=1, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    update_date = Column(DateTime, default=datetime_now, nullable=False)
    context_id = Column(UnicodeText(36), nullable=False)
    questionnaire_hash = Column(UnicodeText(64), nullable=False)
    progressive = Column(Integer, default=0, nullable=False)
    https = Column(Boolean, default=False, nullable=False)
    total_score = Column(Integer, default=0, nullable=False)
    expiration_date = Column(DateTime, nullable=False)
    identity_provided = Column(Boolean, default=False, nullable=False)
    identity_provided_date = Column(DateTime, default=datetime_null, nullable=False)
    enable_attachments = Column(Boolean, default=True, nullable=False)
    enable_whistleblower_identity = Column(Boolean, default=False, nullable=False)
    receipt_hash = Column(UnicodeText(128), nullable=False)
    wb_last_access = Column(DateTime, default=datetime_now, nullable=False)


class ReceiverFile_v_40(Model):
    __tablename__ = 'receiverfile'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    internalfile_id = Column(UnicodeText(36))
    receivertip_id = Column(UnicodeText(36))
    file_path = Column(UnicodeText)
    size = Column(Integer)
    last_access = Column(DateTime, default=datetime_null)
    new = Column(Integer, default=True)
    status = Column(UnicodeText)


class ReceiverTip_v_40(Model):
    __tablename__ = 'receivertip'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    internaltip_id = Column(UnicodeText(36), nullable=False)
    receiver_id = Column(UnicodeText(36), nullable=False)
    last_access = Column(DateTime, default=datetime_null, nullable=False)
    label = Column(UnicodeText, default='', nullable=False)
    can_access_whistleblower_identity = Column(Boolean, default=True, nullable=False)
    new = Column(Integer, default=True, nullable=False)
    enable_notifications = Column(Boolean, default=True, nullable=False)


class User_v_40(Model):
    __tablename__ = 'user'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    tid = Column(Integer, default=1, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    username = Column(UnicodeText, default='', nullable=False)
    password = Column(UnicodeText, default='', nullable=False)
    salt = Column(UnicodeText(24), nullable=False)
    name = Column(UnicodeText, default='', nullable=False)
    description = Column(JSON, default=dict, nullable=False)
    role = Column(UnicodeText, default='receiver', nullable=False)
    state = Column(UnicodeText, default='enabled', nullable=False)
    last_login = Column(DateTime, default=datetime_null, nullable=False)
    mail_address = Column(UnicodeText, default='', nullable=False)
    language = Column(UnicodeText, nullable=False)
    password_change_needed = Column(Boolean, default=True, nullable=False)
    password_change_date = Column(DateTime, default=datetime_null, nullable=False)
    pgp_key_fingerprint = Column(UnicodeText, default='', nullable=False)
    pgp_key_public = Column(UnicodeText, default='', nullable=False)
    pgp_key_expiration = Column(DateTime, default=datetime_null, nullable=False)


class WhistleblowerFile_v_40(Model):
    __tablename__ = 'whistleblowerfile'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    receivertip_id = Column(UnicodeText(36), nullable=False)
    name = Column(UnicodeText, nullable=False)
    file_path = Column(UnicodeText, nullable=False)
    size = Column(Integer, nullable=False)
    content_type = Column(UnicodeText, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    last_access = Column(DateTime, default=datetime_null, nullable=False)
    description = Column(UnicodeText, nullable=False)


class MigrationScript(MigrationBase):
    def migrate_InternalTip(self):
        for tenant in self.session_old.query(self.model_from['Tenant']):
            i = 0
            old_objs = self.session_old.query(self.model_from['InternalTip']) \
                                       .filter(self.model_from['InternalTip'].tid == tenant.id) \
                                       .order_by(self.model_from['InternalTip'].creation_date)
            for old_obj in old_objs:
                i += 1
                new_obj = self.model_to['InternalTip']()
                for key in new_obj.__mapper__.column_attrs.keys():
                    if key == 'progressive':
                        new_obj.progressive = i
                    elif key in old_obj.__mapper__.column_attrs.keys():
                        setattr(new_obj, key, getattr(old_obj, key))

                self.session_new.add(new_obj)

    def _migrateFile(self, model):
        for old_obj in self.session_old.query(self.model_from[model]):
            new_obj = self.model_to[model]()
            for key in new_obj.__mapper__.column_attrs.keys():
                if key == 'filename':
                    new_obj.filename = os.path.basename(old_obj.file_path)
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def migrate_InternalFile(self):
        self._migrateFile("InternalFile")

    def migrate_ReceiverFile(self):
        self._migrateFile("ReceiverFile")

    def migrate_WhistleblowerFile(self):
        self._migrateFile("WhistleblowerFile")

    def epilogue(self):
        for tenant in self.session_old.query(self.model_from['Tenant']):
            count = self.session_old.query(self.model_from['InternalTip']).filter(self.model_from['InternalTip'].tid == tenant.id).count()
            obj = self.model_to['Config']()
            obj.tid = tenant.id
            obj.var_name = 'counter_submissions'
            obj.value = count
            self.session_new.add(obj)
            self.entries_count['Config'] += 1
