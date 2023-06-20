# -*- coding: UTF-8
from globaleaks.db.migrations.update import MigrationBase

from globaleaks.models import Model
from globaleaks.models.properties import *
from globaleaks.utils.utility import datetime_never, datetime_now


class Context_v_46(Model):
    __tablename__ = 'context'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    tid = Column(Integer, default=1, nullable=False)
    show_steps_navigation_interface = Column(Boolean, default=True, nullable=False)
    show_recipients_details = Column(Boolean, default=False, nullable=False)
    allow_recipients_selection = Column(Boolean, default=False, nullable=False)
    maximum_selectable_receivers = Column(Integer, default=0, nullable=False)
    select_all_receivers = Column(Boolean, default=True, nullable=False)
    enable_two_way_comments = Column(Boolean, default=True, nullable=False)
    enable_attachments = Column(Boolean, default=True, nullable=False)
    tip_timetolive = Column(Integer, default=30, nullable=False)
    name = Column(JSON, default=dict, nullable=False)
    description = Column(JSON, default=dict, nullable=False)
    show_receivers_in_alphabetical_order = Column(Boolean, default=True, nullable=False)
    presentation_order = Column(Integer, default=0, nullable=False)
    questionnaire_id = Column(UnicodeText(36), default='default', nullable=False)
    additional_questionnaire_id = Column(UnicodeText(36))
    status = Column(Integer, default=2, nullable=False)


class FieldOption_v_46(Model):
    __tablename__ = 'fieldoption'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    field_id = Column(UnicodeText(36), nullable=False)
    presentation_order = Column(Integer, default=0, nullable=False)
    label = Column(JSON, nullable=False)
    score_points = Column(Integer, default=0, nullable=False)
    score_type = Column(Integer, default=0, nullable=False)
    trigger_field = Column(UnicodeText(36), nullable=True)
    trigger_step = Column(UnicodeText(36), nullable=True)
    trigger_receiver = Column(JSON, default=list, nullable=True)


class InternalTip_v_46(Model):
    __tablename__ = 'internaltip'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    tid = Column(Integer, default=1, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    update_date = Column(DateTime, default=datetime_now, nullable=False)
    context_id = Column(UnicodeText(36), nullable=False)
    progressive = Column(Integer, default=0, nullable=False)
    https = Column(Boolean, default=False, nullable=False)
    total_score = Column(Integer, default=0, nullable=False)
    expiration_date = Column(DateTime, default=datetime_never, nullable=False)
    enable_two_way_comments = Column(Boolean, default=True, nullable=False)
    enable_attachments = Column(Boolean, default=True, nullable=False)
    enable_whistleblower_identity = Column(Boolean, default=False, nullable=False)
    wb_last_access = Column(DateTime, default=datetime_now, nullable=False)
    status = Column(UnicodeText(36), nullable=True)
    substatus = Column(UnicodeText(36), nullable=True)


class SubmissionStatus_v_46(Model):
    __tablename__ = 'submissionstatus'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    tid = Column(Integer, default=1, nullable=False)
    label = Column(JSON, nullable=False)
    system_defined = Column(Boolean, nullable=False, default=False)
    system_usage = Column(UnicodeText, nullable=True)
    presentation_order = Column(Integer, default=0, nullable=False)


class SubmissionSubStatus_v_46(Model):
    __tablename__ = 'submissionsubstatus'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    submissionstatus_id = Column(UnicodeText(36), nullable=False)
    label = Column(JSON, nullable=False)
    presentation_order = Column(Integer, default=0, nullable=False)


class MigrationScript(MigrationBase):
    def migrate_FieldOption(self):
        for old_obj in self.session_old.query(self.model_from['FieldOption']):
            new_obj = self.model_to['FieldOption']()
            for key in new_obj.__mapper__.column_attrs.keys():
                setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

            if old_obj.trigger_field is not None:
                x = self.model_to['FieldOptionTriggerField']()
                x.option_id = old_obj.id
                x.object_id = old_obj.trigger_field
                self.session_new.add(x)

            if old_obj.trigger_step is not None:
                x = self.model_to['FieldOptionTriggerStep']()
                x.option_id = old_obj.id
                x.object_id = old_obj.trigger_step
                self.session_new.add(x)
