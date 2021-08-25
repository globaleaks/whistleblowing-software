# -*- coding: UTF-8
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import Model
from globaleaks.models.properties import *
from globaleaks.utils.utility import datetime_now

class SubmissionStatusChange_v_54(Model):
    __tablename__ = 'submissionstatuschange'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    internaltip_id = Column(UnicodeText(36), nullable=False)
    status = Column(UnicodeText(36), nullable=False)
    substatus = Column(UnicodeText(36), nullable=True)
    changed_on = Column(DateTime, default=datetime_now, nullable=False)
    changed_by = Column(UnicodeText(36), nullable=False)

class MigrationScript(MigrationBase):
    def epilogue(self):
        s_m = self.model_from['SubmissionStatusChange']
        t_m = self.model_from['InternalTip']
        for ssc, tid in self.session_old.query(s_m, t_m).filter(s_m.internaltip_id == t_m.id):
            log = self.model_to['AuditLog']()
            log.object_id = ssc.internaltip_id
            log.date = ssc.changed_on
            log.user_id = ssc.changed_by

            log.data = {
              'status': ssc.status,
              'substatus': ssc.substatus
            }

            self.session_new.add(log)
            self.entries_count['AuditLog'] += 1
