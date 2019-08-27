from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import Model
from globaleaks.models.properties import *
from globaleaks.utils.utility import datetime_now, datetime_null

class Field_v_50(Model):
    __tablename__ = 'field'
    id = Column((UnicodeText(36)), primary_key=True, default=uuid4)
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
    template_override_id = Column((UnicodeText(36)), nullable=True)
    encrypt = Column(Boolean, default=True, nullable=False)


class InternalFile_v_50(Model):
    __tablename__ = 'internalfile'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    internaltip_id = Column(UnicodeText(36), nullable=False)
    name = Column(UnicodeText, nullable=False)
    filename = Column(UnicodeText(255), unique=True, nullable=False)
    content_type = Column(UnicodeText, nullable=False)
    size = Column(Integer, nullable=False)
    new = Column(Boolean, default=True, nullable=False)
    submission = Column(Integer, default=False, nullable=False)


class User_v_50(Model):
    __tablename__ = 'user'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    tid = Column(Integer, default=1, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    username = Column(UnicodeText, default=u'', nullable=False)
    salt = Column(UnicodeText(24), nullable=False)
    hash_alg = Column(UnicodeText, default=u'SCRYPT', nullable=False)
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
    crypto_prv_key = Column(LargeBinary(72), default=b'', nullable=False)
    crypto_pub_key = Column(LargeBinary(32), default=b'', nullable=False)
    crypto_rec_key = Column(LargeBinary(80), default=b'', nullable=False)
    crypto_bkp_key = Column(LargeBinary(72), default=b'', nullable=False)
    change_email_address = Column(UnicodeText, default=u'', nullable=False)
    change_email_token = Column(UnicodeText, unique=True, nullable=True)
    change_email_date = Column(DateTime, default=datetime_null, nullable=False)
    reset_password_token = Column(UnicodeText, unique=True, nullable=True)
    reset_password_date = Column(UnicodeText, default=datetime_null, nullable=False)
    notification = Column(Boolean, default=True, nullable=False)
    recipient_configuration = Column(UnicodeText, default=u'default', nullable=False)
    can_delete_submission = Column(Boolean, default=False, nullable=False)
    can_postpone_expiration = Column(Boolean, default=False, nullable=False)
    can_grant_permissions = Column(Boolean, default=False, nullable=False)
    can_edit_general_settings = Column(Boolean, default=False, nullable=False)
    pgp_key_fingerprint = Column(UnicodeText, default=u'', nullable=False)
    pgp_key_public = Column(UnicodeText, default=u'', nullable=False)
    pgp_key_expiration = Column(DateTime, default=datetime_null, nullable=False)

    binary_keys = ['crypto_prv_key', 'crypto_pub_key']


class MigrationScript(MigrationBase):
    def migrate_InternalFile(self):
        old_objs = self.session_old.query(self.model_from['InternalFile'])
        for old_obj in old_objs:
            new_obj = self.model_to['InternalFile']()
            old_keys = [c.key for c in old_obj.__table__.columns]
            for key in [c.key for c in new_obj.__table__.columns]:
                print(key)
                if key in old_keys:
                    print(key)
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)
