# -*- coding: UTF-8
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.handlers.admin.tenant import initialize_submission_states
from globaleaks.handlers.submission import db_update_submission_state
from globaleaks.models import Model
from globaleaks.models.properties import *
from globaleaks.utils.utility import datetime_now, datetime_null


class InternalTip_v_41(Model):
    __tablename__ = 'internaltip'

    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)
    tid = Column(Integer, default=1, nullable=False)
    encrypted = Column(Boolean, default=False, nullable=False)
    wb_prv_key = Column(Unicode, default=u'', nullable=False)
    wb_pub_key = Column(Unicode, default=u'', nullable=False)
    wb_tip_key = Column(Unicode, default=u'', nullable=False)
    enc_data = Column(Unicode, default=u'', nullable=False)
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
                new_obj.name = 'text_shown_upon_negative_answer'
            elif old_obj.name == 'clause':
                new_obj.name = 'text'
            elif old_obj.name == 'agreement_statement':
                new_obj.name = 'checkbox_label'

            self.session_new.add(new_obj)


class MigrationScript(MigrationBase):
    def migrate_InternalTip(self):
        old_objs = self.session_old.query(self.model_from['InternalTip'])
        for old_obj in old_objs:
            new_obj = self.model_to['InternalTip']()
            for key in [c.key for c in new_obj.__table__.columns]:
                new_obj.state = 'antani!'
                if key == 'state' or key =='substate':
                    pass
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)


    def epilogue(self):
        tenants = self.session_old.query(self.model_from['Tenant'])
        for tenant in tenants:
            initialize_submission_states(self.session_new, tenant.id)

        self.session_new.flush()

        for tenant in tenants:
            itips = self.session_new.query(self.model_to['InternalTip'])\
                                    .filter(self.model_to['InternalTip'].context_id == self.model_to['Context'].id,
                                            self.model_to['Context'].tid == tenant.id)
            for itip in itips:
                open_state_id = self.session_new.query(self.model_to['SubmissionState'].id)\
                                                .filter(self.model_to['SubmissionState'].tid == tenant.id,
                                                        self.model_to['SubmissionState'].system_usage == 'open').one()[0]

                first_rtip = self.session_new.query(self.model_to['ReceiverTip'])\
                                         .filter(self.model_to['ReceiverTip'].internaltip_id == itip.id).first()
                db_update_submission_state(self.session_new, tenant.id, first_rtip.receiver_id, itip, open_state_id, u'')
