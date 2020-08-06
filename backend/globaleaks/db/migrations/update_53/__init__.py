# -*- coding: UTF-8
from datetime import datetime

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models.config import ConfigFactory
from globaleaks.models.enums import EnumFieldAttrType
from globaleaks.models import Model
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
