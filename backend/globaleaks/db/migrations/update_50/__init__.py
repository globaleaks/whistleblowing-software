# -*- coding: UTF-8
from globaleaks.db.migrations.update import MigrationBase

from globaleaks.models import Model
from globaleaks.models.properties import *


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
                if old_obj.system_usage == u'open':
                    new_obj.id = 'opened'
                    new_obj.label = {'en': u'Opened'}

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

    def epilogue(self):
        objs = self.session_new.query(self.model_to['InternalTip'])
        for obj in objs:
            if obj.status in self.status_map:
                obj.status = self.status_map[obj.status]
