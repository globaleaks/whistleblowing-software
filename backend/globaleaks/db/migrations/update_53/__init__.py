# -*- coding: UTF-8
from datetime import datetime

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models.config import ConfigFactory
from globaleaks.models.enums import EnumFieldAttrType
from globaleaks.models import Model
from globaleaks.models.enums import *
from globaleaks.models.properties import *
from globaleaks.utils.crypto import Base32Encoder
from globaleaks.utils.utility import datetime_now, datetime_never, datetime_null


class Subscriber_v_52(Model):
    __tablename__ = 'signup'

    id = Column(Integer, primary_key=True)
    tid = Column(Integer, nullable=False)
    subdomain = Column(UnicodeText, unique=True, nullable=False)
    language = Column(UnicodeText(12), nullable=False)
    name = Column(UnicodeText, nullable=False)
    surname = Column(UnicodeText, nullable=False)
    role = Column(UnicodeText, default='', nullable=False)
    phone = Column(UnicodeText, default='', nullable=False)
    email = Column(UnicodeText, nullable=False)
    use_case = Column(UnicodeText, default='', nullable=False)
    use_case_other = Column(UnicodeText, default='', nullable=False)
    organization_name = Column(UnicodeText, default='', nullable=False)
    organization_type = Column(UnicodeText, default='', nullable=False)
    organization_location1 = Column(UnicodeText, default='', nullable=False)
    organization_location2 = Column(UnicodeText, default='', nullable=False)
    organization_location3 = Column(UnicodeText, default='', nullable=False)
    organization_location4 = Column(UnicodeText, default='', nullable=False)
    organization_site = Column(UnicodeText, default='', nullable=False)
    organization_number_employees = Column(UnicodeText, default='', nullable=False)
    organization_number_users = Column(UnicodeText, default='', nullable=False)
    hear_channel = Column(UnicodeText, default='', nullable=False)
    activation_token = Column(UnicodeText, unique=True, nullable=True)
    client_ip_address = Column(UnicodeText, default='', nullable=False)
    client_user_agent = Column(UnicodeText, default='', nullable=False)
    registration_date = Column(DateTime, default=datetime_now, nullable=False)
    tos1 = Column(UnicodeText, default='', nullable=False)
    tos2 = Column(UnicodeText, default='', nullable=False)


class Tenant_v_52(Model):
    __tablename__ = 'tenant'

    id = Column(Integer, primary_key=True, nullable=False)
    label = Column(UnicodeText, default='', nullable=False)
    active = Column(Boolean, default=False, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    subdomain = Column(UnicodeText, default='', nullable=False)


class User_v_52(Model):
    __tablename__ = 'user'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    tid = Column(Integer, default=1, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    username = Column(UnicodeText, default='', nullable=False)
    salt = Column(UnicodeText(24), default='', nullable=False)
    hash_alg = Column(UnicodeText, default='ARGON2', nullable=False)
    password = Column(UnicodeText, default='', nullable=False)
    name = Column(UnicodeText, default='', nullable=False)
    description = Column(JSON, default=dict, nullable=False)
    public_name = Column(UnicodeText, default='', nullable=False)
    role = Column(Enum(EnumUserRole), default='receiver', nullable=False)
    state = Column(Enum(EnumUserState), default='enabled', nullable=False)
    last_login = Column(DateTime, default=datetime_null, nullable=False)
    mail_address = Column(UnicodeText, default='', nullable=False)
    language = Column(UnicodeText(12), nullable=False)
    password_change_needed = Column(Boolean, default=True, nullable=False)
    password_change_date = Column(DateTime, default=datetime_null, nullable=False)
    crypto_prv_key = Column(UnicodeText(84), default='', nullable=False)
    crypto_pub_key = Column(UnicodeText(56), default='', nullable=False)
    crypto_rec_key = Column(UnicodeText(80), default='', nullable=False)
    crypto_bkp_key = Column(UnicodeText(84), default='', nullable=False)
    crypto_escrow_prv_key = Column(UnicodeText(84), default='', nullable=False)
    crypto_escrow_bkp1_key = Column(UnicodeText(84), default='', nullable=False)
    crypto_escrow_bkp2_key = Column(UnicodeText(84), default='', nullable=False)
    change_email_address = Column(UnicodeText, default='', nullable=False)
    change_email_token = Column(UnicodeText, unique=True, nullable=True)
    change_email_date = Column(DateTime, default=datetime_null, nullable=False)
    reset_password_token = Column(UnicodeText, unique=True, nullable=True)
    reset_password_date = Column(UnicodeText, default=datetime_null, nullable=False)
    notification = Column(Boolean, default=True, nullable=False)
    recipient_configuration = Column(Enum(EnumRecipientConfiguration), default='default', nullable=False)
    can_delete_submission = Column(Boolean, default=False, nullable=False)
    can_postpone_expiration = Column(Boolean, default=False, nullable=False)
    can_grant_permissions = Column(Boolean, default=False, nullable=False)
    can_edit_general_settings = Column(Boolean, default=False, nullable=False)
    readonly = Column(Boolean, default=False, nullable=False)
    two_factor_enable = Column(Boolean, default=False, nullable=False)
    two_factor_secret = Column(UnicodeText(16), default='', nullable=False)
    pgp_key_fingerprint = Column(UnicodeText, default='', nullable=False)
    pgp_key_public = Column(UnicodeText, default='', nullable=False)
    pgp_key_expiration = Column(DateTime, default=datetime_null, nullable=False)


class MigrationScript(MigrationBase):
    def migrate_Tenant(self):
        for old_obj in self.session_old.query(self.model_from['Tenant']):
            self.entries_count['Config'] += 2
            node = ConfigFactory(self.session_new, old_obj.id)

            new_obj = self.model_to['Tenant']()
            for key in new_obj.__table__.columns._data.keys():
                setattr(new_obj, key, getattr(old_obj, key))

            for key in ['active', 'subdomain']:
                x = self.model_to['Config']()
                x.tid = old_obj.id
                x.var_name = key
                x.value = getattr(old_obj, key)
                self.session_new.add(x)

            self.session_new.add(new_obj)

    def migrate_Subscriber(self):
        for old_obj in self.session_old.query(self.model_from['Subscriber']):
            new_obj = self.model_to['Subscriber']()
            for key in new_obj.__table__.columns._data.keys():
                if key == 'activation_token' and old_obj.activation_token == '':
                    new_obj.activation_token = None

                if key in old_obj.__table__.columns._data.keys():
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)


    def epilogue(self):
        for t in self.session_new.query(self.model_to['Tenant']):
            m = self.model_to['Config']
            self.session_new.query(m).filter(m.tid == t.id, m.var_name == 'https_key').update({'var_name': 'https_key'})
