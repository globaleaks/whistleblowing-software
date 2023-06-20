# -*- coding: UTF-8
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.handlers.rtip import db_update_submission_status
from globaleaks.models import Model
from globaleaks.models.properties import *
from globaleaks.utils.utility import datetime_now, datetime_null


class InternalTip_v_41(Model):
    __tablename__ = 'internaltip'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    tid = Column(Integer, default=1, nullable=False)
    encrypted = Column(Boolean, default=False, nullable=False)
    wb_prv_key = Column(UnicodeText, default='', nullable=False)
    wb_pub_key = Column(UnicodeText, default='', nullable=False)
    wb_tip_key = Column(UnicodeText, default='', nullable=False)
    enc_data = Column(UnicodeText, default='', nullable=False)
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
    enable_two_way_comments = Column(Boolean, default=True, nullable=False)
    enable_attachments = Column(Boolean, default=True, nullable=False)
    enable_whistleblower_identity = Column(Boolean, default=False, nullable=False)
    receipt_hash = Column(UnicodeText(128), nullable=False)
    wb_last_access = Column(DateTime, default=datetime_now, nullable=False)


class MigrationScript(MigrationBase):
    def migrate_FieldAttr(self):
        for old_obj in self.session_old.query(self.model_from['FieldAttr']):
            new_obj = self.model_to['FieldAttr']()
            for key in new_obj.__mapper__.column_attrs.keys():
                setattr(new_obj, key, getattr(old_obj, key))

            if old_obj.name == 'agreement_statement':
                new_obj.name = 'checkbox_label'

            self.session_new.add(new_obj)

    def migrate_InternalTip(self):
        for old_obj in self.session_old.query(self.model_from['InternalTip']):
            new_obj = self.model_to['InternalTip']()
            for key in new_obj.__mapper__.column_attrs.keys():
                if key == 'status' or key == 'substatus':
                    new_obj.status = 'new'
                elif key in old_obj.__mapper__.column_attrs.keys():
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

            if old_obj.receipt_hash:
                new_wbtip = self.model_to['WhistleblowerTip']()
                new_wbtip.id = old_obj.id
                new_wbtip.tid = old_obj.tid
                new_wbtip.receipt_hash = old_obj.receipt_hash
                self.session_new.add(new_wbtip)

    def epilogue(self):
        for tenant in self.session_old.query(self.model_from['Tenant']):
            for s in [{'label': {'en': 'New'}, 'system_usage': 'new'},
                      {'label': {'en': 'Opened'}, 'system_usage': 'opened'},
                      {'label': {'en': 'Closed'}, 'system_usage': 'closed'}]:
                state = self.model_to['SubmissionStatus']()
                state.tid = tenant.id
                state.label = s['label']
                state.system_defined = True
                state.system_usage = s['system_usage']
                self.session_new.add(state)

            self.session_new.flush()

            itips = self.session_new.query(self.model_to['InternalTip'])\
                                    .filter(self.model_to['InternalTip'].context_id == self.model_to['Context'].id,
                                            self.model_to['Context'].tid == tenant.id)
            for itip in itips:
                itip.status = 'opened'
                itip.substatus = ''
