# -*- coding: UTF-8
import base64
import os
from datetime import datetime

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.handlers.admin.file import special_files
from globaleaks.models import Model
from globaleaks.models.enums import *
from globaleaks.models.properties import *
from globaleaks.state import State
from globaleaks.utils.utility import uuid4


class ContextImg_v_53(Model):
    __tablename__ = 'contextimg'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    data = Column(UnicodeText, nullable=False)


class File_v_53(Model):
    __tablename__ = 'file'
    tid = Column(Integer, primary_key=True, default=1)
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    name = Column(UnicodeText, default='', nullable=False)
    data = Column(UnicodeText, nullable=False)


class UserImg_v_53(Model):
    __tablename__ = 'userimg'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    data = Column(UnicodeText, nullable=False)


class MigrationScript(MigrationBase):
    def migrate_File(self):
        for old_obj in self.session_old.query(self.model_from['File']):
            new_obj = self.model_to['File']()
            for key in new_obj.__table__.columns._data.keys():
                if hasattr(old_obj, key):
                    setattr(new_obj, key, getattr(old_obj, key))

            if old_obj.id in special_files:
                new_obj.id = uuid4()
                new_obj.name = old_obj.id

                data = base64.b64decode(old_obj.data)

                filepath = os.path.join(State.settings.files_path, new_obj.id)
                with open(filepath, 'wb') as out_file:
                    out_file.write(data)

            if not new_obj.name:
                new_obj.name = new_obj.id

            self.session_new.add(new_obj)

        for model in [('ContextImg', 'Context'), ('UserImg', 'User')]:
            for old_obj, tid in self.session_old.query(self.model_from[model[0]], self.model_from[model[1]].tid) \
                                                .filter(self.model_from[model[0]].id == self.model_from[model[1]].id):
                new_obj = self.model_to['File']()
                for key in new_obj.__table__.columns._data.keys():
                    new_obj.tid = tid
                    new_obj.id = old_obj.id
                    new_obj.name = old_obj.id

                    data = base64.b64decode(old_obj.data)

                    filepath = os.path.join(State.settings.files_path, old_obj.id)
                    with open(filepath, 'wb') as out_file:
                        out_file.write(data)

                self.session_new.add(new_obj)
                self.entries_count['File'] += 1
