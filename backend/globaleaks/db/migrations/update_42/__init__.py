# -*- coding: UTF-8
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import Model
from globaleaks.models.properties import *
from globaleaks.utils.utility import datetime_now, datetime_null

class Signup_v_41(Model):
    __tablename__ = 'signup'

    id = Column(Integer, primary_key=True, nullable=False)
    tid = Column(Integer, nullable=True)
    subdomain = Column(UnicodeText, unique=True, nullable=False)
    language = Column(UnicodeText, nullable=False)
    name = Column(UnicodeText, nullable=False)
    surname = Column(UnicodeText, nullable=False)
    role = Column(UnicodeText, default=u'', nullable=False)
    email = Column(UnicodeText, nullable=False)
    secondary_email = Column(UnicodeText, default=u'', nullable=False)
    phone = Column(UnicodeText, default=u'', nullable=False)
    use_case = Column(UnicodeText, default=u'', nullable=False)
    use_case_other = Column(UnicodeText, default=u'', nullable=False)
    organization_name = Column(UnicodeText, default=u'', nullable=False)
    organization_type = Column(UnicodeText, default=u'', nullable=False)
    organization_city = Column(UnicodeText, default=u'', nullable=False)
    organization_province = Column(UnicodeText, default=u'', nullable=False)
    organization_region = Column(UnicodeText, default=u'', nullable=False)
    organization_country = Column(UnicodeText, default=u'', nullable=False)
    organization_number_employee = Column(UnicodeText, default=u'', nullable=False)
    organization_number_users = Column(UnicodeText, default=u'', nullable=False)
    activation_token = Column(UnicodeText, nullable=False)
    registration_date = Column(DateTime, default=datetime_now, nullable=False)
    tos = Column(UnicodeText, default=u'', nullable=False)

class MigrationScript(MigrationBase):
    def migrate_FieldAttr(self):
        old_objs = self.session_old.query(self.model_from['FieldAttr'])
        for old_obj in old_objs:
            new_obj = self.model_to['FieldAttr']()
            for key in [c.key for c in new_obj.__table__.columns]:
                setattr(new_obj, key, getattr(old_obj, key))

            if old_obj.name == 'text_of_confirmation_question_upon_negative_answer':
                setattr(new_obj, 'name', 'text_shown_upon_negative_answer')

            self.session_new.add(new_obj)
