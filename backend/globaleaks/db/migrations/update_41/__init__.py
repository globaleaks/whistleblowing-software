# -*- coding: UTF-8
import os

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import Model
from globaleaks.models.properties import *
from globaleaks.utils.utility import datetime_now, datetime_null


class InternalFile_v_40(Model):
    __tablename__ = 'internalfile'
    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    internaltip_id = Column(Unicode(36), nullable=False)
    name = Column(UnicodeText, nullable=False)
    file_path = Column(UnicodeText, nullable=False)
    content_type = Column(UnicodeText, nullable=False)
    size = Column(Integer, nullable=False)
    new = Column(Integer, default=True, nullable=False)
    submission = Column(Integer, default = False, nullable=False)
    processing_attempts = Column(Integer, default=0, nullable=False)


class InternalTip_v_40(Model):
    __tablename__ = 'internaltip'
    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)
    tid = Column(Integer, default=1, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    update_date = Column(DateTime, default=datetime_now, nullable=False)
    context_id = Column(Unicode(36), nullable=False)
    questionnaire_hash = Column(Unicode(64), nullable=False)
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
    receipt_hash = Column(Unicode(128), nullable=False)
    wb_last_access = Column(DateTime, default=datetime_now, nullable=False)
    wb_access_counter = Column(Integer, default=0, nullable=False)


class ReceiverFile_v_40(Model):
    __tablename__ = 'receiverfile'
    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)
    internalfile_id = Column(Unicode(36))
    receivertip_id = Column(Unicode(36))
    file_path = Column(UnicodeText)
    size = Column(Integer)
    downloads = Column(Integer, default=0)
    last_access = Column(DateTime, default=datetime_null)
    new = Column(Integer, default=True)
    status = Column(UnicodeText)


class ReceiverTip_v_40(Model):
    __tablename__ = 'receivertip'
    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)
    internaltip_id = Column(Unicode(36), nullable=False)
    receiver_id = Column(Unicode(36), nullable=False)
    last_access = Column(DateTime, default=datetime_null, nullable=False)
    access_counter = Column(Integer, default=0, nullable=False)
    label = Column(UnicodeText, default=u'', nullable=False)
    can_access_whistleblower_identity = Column(Boolean, default=False, nullable=False)
    new = Column(Integer, default=True, nullable=False)
    enable_notifications = Column(Boolean, default=True, nullable=False)


class Signup_v_40(Model):
    __tablename__ = 'signup'
    id = Column(Integer, primary_key=True, nullable=False)
    tid = Column(Integer, nullable=True)
    subdomain = Column(UnicodeText, unique=True, nullable=False)
    name = Column(UnicodeText, nullable=False)
    surname = Column(UnicodeText, nullable=False)
    email = Column(UnicodeText, nullable=False)
    use_case = Column(UnicodeText, nullable=False)
    use_case_other = Column(UnicodeText, nullable=False)
    language = Column(UnicodeText, nullable=False)
    activation_token = Column(UnicodeText, nullable=False)
    registration_date = Column(DateTime, default=datetime_now, nullable=False)


class User_v_40(Model):
    __tablename__ = 'user'
    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)
    tid = Column(Integer, default=1, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    username = Column(UnicodeText, default=u'', nullable=False)
    password = Column(UnicodeText, default=u'', nullable=False)
    salt = Column(Unicode(24), nullable=False)
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
    pgp_key_fingerprint = Column(UnicodeText, default=u'', nullable=False)
    pgp_key_public = Column(UnicodeText, default=u'', nullable=False)
    pgp_key_expiration = Column(DateTime, default=datetime_null, nullable=False)


class WhistleblowerFile_v_40(Model):
    __tablename__ = 'whistleblowerfile'
    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)
    receivertip_id = Column(Unicode(36), nullable=False)
    name = Column(UnicodeText, nullable=False)
    file_path = Column(UnicodeText, nullable=False)
    size = Column(Integer, nullable=False)
    content_type = Column(UnicodeText, nullable=False)
    downloads = Column(Integer, default=0, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    last_access = Column(DateTime, default=datetime_null, nullable=False)
    description = Column(UnicodeText, nullable=False)



class MigrationScript(MigrationBase):
    def migrate_InternalTip(self):
        tenants = self.session_old.query(self.model_from['Tenant'])
        for tenant in tenants:
            old_objs = self.session_old.query(self.model_from['InternalTip']) \
                                       .filter(self.model_from['InternalTip'].tid == tenant.id) \
                                       .order_by(self.model_from['InternalTip'].creation_date)
            i = 0
            for old_obj in old_objs:
                i += 1
                new_obj = self.model_to['InternalTip'](migrate=True)
                for key in [c.key for c in new_obj.__table__.columns]:
                    if key in ['encrypted', 'wb_prv_key', 'wb_pub_key', 'wb_tip_key', 'enc_data']:
                        new_obj.encrypted = False
                    elif key == 'progressive':
                        new_obj.progressive = i
                    else:
                        setattr(new_obj, key, getattr(old_obj, key))

                self.session_new.add(new_obj)

    def migrate_InternalFile(self):
        old_objs = self.session_old.query(self.model_from['InternalFile'])
        for old_obj in old_objs:
            new_obj = self.model_to['InternalFile'](migrate=True)
            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'filename':
                    new_obj.filename = os.path.basename(old_obj.file_path)
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def migrate_ReceiverFile(self):
        old_objs = self.session_old.query(self.model_from['ReceiverFile'])
        for old_obj in old_objs:
            new_obj = self.model_to['ReceiverFile'](migrate=True)
            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'filename':
                    new_obj.filename = os.path.basename(old_obj.file_path)
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def migrate_WhistleblowerFile(self):
        old_objs = self.session_old.query(self.model_from['WhistleblowerFile'])
        for old_obj in old_objs:
            new_obj = self.model_to['WhistleblowerFile'](migrate=True)
            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'filename':
                    new_obj.filename = os.path.basename(old_obj.file_path)
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def epilogue(self):
        tenants = self.session_old.query(self.model_from['Tenant'])
        for tenant in tenants:
            count = self.session_old.query(self.model_from['InternalTip']).filter(self.model_from['InternalTip'].tid == tenant.id).count()
            self.session_new.add(self.model_to['Config'](tenant.id, u'counter_submissions', count))
            self.entries_count['Config'] += 1
