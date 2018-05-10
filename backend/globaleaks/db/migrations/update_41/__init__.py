# -*- coding: UTF-8
import os

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import Model
from globaleaks.models.properties import *
from globaleaks.utils.utility import datetime_now, datetime_null


class InternalFile_v_40(Model):
    __tablename__ = 'internalfile'
    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    internaltip_id = Column(Unicode(36), nullable=False)
    name = Column(UnicodeText, nullable=False)
    file_path = Column(UnicodeText, nullable=False)
    content_type = Column(UnicodeText, nullable=False)
    size = Column(Integer, nullable=False)
    new = Column(Integer, default=True, nullable=False)
    submission = Column(Integer, default = False, nullable=False)
    processing_attempts = Column(Integer, default=0, nullable=False)


class ReceiverFile_v_40(Model):
    __tablename__ = 'receiverfile'
    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)
    internalfile_id = Column(Unicode(36))
    receivertip_id = Column(Unicode(36))
    file_path = Column(UnicodeText)
    size = Column(Integer)
    downloads = Column(Integer, default=0)
    last_access = Column(DateTime, default=datetime_null)
    new = Column(Integer, default=True)
    status = Column(UnicodeText)


class WhistleblowerFile_v_40(Model):
    __tablename__ = 'whistleblowerfile'
    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)
    receivertip_id = Column(Unicode(36), nullable=False)
    name = Column(UnicodeText, nullable=False)
    file_path = Column(UnicodeText, nullable=False)
    size = Column(Integer, nullable=False)
    content_type = Column(UnicodeText, nullable=False)
    downloads = Column(Integer, default=0, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    last_access = Column(DateTime, default=datetime_null, nullable=False)
    description = Column(UnicodeText, nullable=False)


class MigrationScript(MigrationBase):
    def migrate_InternalFile(self):
        old_objs = self.session_old.query(self.model_from['InternalFile'])
        for old_obj in old_objs:
            new_obj = self.model_to['InternalFile'](migrate=True)
            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'filename':
                    new_obj.filename = os.path.basename(old_obj.file_path)
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def migrate_ReceiverFile(self):
        old_objs = self.session_old.query(self.model_from['ReceiverFile'])
        for old_obj in old_objs:
            new_obj = self.model_to['ReceiverFile'](migrate=True)
            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'filename':
                    new_obj.filename = os.path.basename(old_obj.file_path)
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def migrate_WhistleblowerFile(self):
        old_objs = self.session_old.query(self.model_from['WhistleblowerFile'])
        for old_obj in old_objs:
            new_obj = self.model_to['WhistleblowerFile'](migrate=True)
            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'filename':
                    new_obj.filename = os.path.basename(old_obj.file_path)
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)
