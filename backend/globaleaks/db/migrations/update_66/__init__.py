# -*- coding: UTF-8
from datetime import timedelta

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import Model
from globaleaks.models.enums import EnumVisibility
from globaleaks.utils.onion import generate_onion_service_v3
from globaleaks.models.properties import *
from globaleaks.utils.utility import datetime_never, datetime_now, datetime_null


class ReceiverFile_v_65(Model):
    __tablename__ = 'whistleblowerfile'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    internaltip_id = Column(UnicodeText(36), nullable=False, index=True)
    name = Column(UnicodeText, nullable=False)
    size = Column(Integer, nullable=False)
    content_type = Column(UnicodeText, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    access_date = Column(DateTime, default=datetime_null, nullable=False)
    description = Column(UnicodeText, default="", nullable=False)
    visibility = Column(Enum(EnumVisibility), default='public', nullable=False)
    new = Column(Boolean, default=True, nullable=False)


class SubmissionStatus_v_65(Model):
    __tablename__ = 'submissionstatus'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    tid = Column(Integer, primary_key=True, default=1)
    label = Column(JSON, default=dict, nullable=False)
    order = Column(Integer, default=0, nullable=False)


class SubmissionSubStatus_v_65(Model):
    __tablename__ = 'submissionsubstatus'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    tid = Column(Integer, primary_key=True, default=1)
    submissionstatus_id = Column(UnicodeText(36), nullable=False)
    label = Column(JSON, default=dict, nullable=False)
    order = Column(Integer, default=0, nullable=False)


class WhistleblowerFile_v_65(Model):
    __tablename__ = 'receiverfile'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    internalfile_id = Column(UnicodeText(36), nullable=False, index=True)
    receivertip_id = Column(UnicodeText(36), nullable=False, index=True)
    access_date = Column(DateTime, default=datetime_null, nullable=False)
    new = Column(Boolean, default=True, nullable=False)


class MigrationScript(MigrationBase):
    def migrate_InternalTipData(self):
        for old_obj, old_tip in self.session_old.query(self.model_from['InternalTipData'], self.model_from['InternalTip']) \
                                       .filter(self.model_from['InternalTipData'].internaltip_id == self.model_from['InternalTip'].id):
            new_obj = self.model_to['InternalTipData']()
            for key in new_obj.__mapper__.column_attrs.keys():
                if key in old_obj.__mapper__.column_attrs.keys():
                    setattr(new_obj, key, getattr(old_obj, key))

            if old_obj.creation_date < old_tip.creation_date + timedelta(minutes=1):
                new_obj.creation_date = old_tip.creation_date

            self.session_new.add(new_obj)

    def epilogue(self):
        m = self.model_to['Config']

        tids = self.session_new.query(m.tid).filter(m.var_name == 'mode', m.value == 'default')

        for c in self.session_new.query(m).filter(m.tid.in_(tids), m.var_name == 'onionservice'):
            if len(c.value) == 62:
                continue

            hostname, key = generate_onion_service_v3()

            self.session_new.query(m) \
                            .filter(m.tid == c.tid,
                                    m.var_name == 'onionservice') \
                            .update({'value': hostname})

            self.session_new.query(m) \
                            .filter(m.tid == c.tid,
                                    m.var_name == 'tor_onion_key') \
                            .update({'value': key})
