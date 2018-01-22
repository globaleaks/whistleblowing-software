# -*- coding: utf-8 -*-
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import Model
from globaleaks.models.properties import *


class InternalFile_v_25(Model):
    __tablename__ = 'internalfile'
    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)
    creation_date = Column(DateTime)
    internaltip_id = Column(Unicode(36))
    name = Column(UnicodeText)
    file_path = Column(UnicodeText)
    content_type = Column(UnicodeText)
    size = Column(Integer)
    new = Column(Integer)
    processing_attempts = Column(Integer)


class MigrationScript(MigrationBase):
    def migrate_InternalFile(self):
        old_objs = self.session_old.query(self.model_from['InternalFile'])
        for old_obj in old_objs:
            new_obj = self.model_to['InternalFile']()
            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'submission':
                    new_obj.submission = True
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)
