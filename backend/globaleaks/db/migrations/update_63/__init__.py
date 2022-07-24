# -*- coding: UTF-8
import os
import shutil

from globaleaks.models import Model
from globaleaks.settings import Settings
from globaleaks.db.migrations.update import MigrationBase


class MigrationScript(MigrationBase):
    def migrate_Config(self):
        for old_obj in self.session_old.query(self.model_from['Config']):
            new_obj = self.model_to['Config']()
            for key in new_obj.__mapper__.column_attrs.keys():
                setattr(new_obj, key, getattr(old_obj, key))

            if old_obj.var_name == 'mode':
                if old_obj.value == 'whistleblowing.it':
                    new_obj.value = 'wbpa'

                elif old_obj.value == 'eat':
                    new_obj.value = 'default'

            self.session_new.add(new_obj)

    def migrate_File(self):
        for old_obj in self.session_old.query(self.model_from['File']):
            if old_obj.name == 'script':
                self.entries_count['File'] -= 1
                try:
                    srcpath = os.path.abspath(os.path.join(Settings.files_path, old_obj.id))
                    dstpath = os.path.abspath(os.path.join(Settings.scripts_path, str(old_obj.tid)))
                    shutil.move(srcpath, dstpath)
                except:
                    pass
            else:
                new_obj = self.model_to['File']()
                for key in new_obj.__mapper__.column_attrs.keys():
                    setattr(new_obj, key, getattr(old_obj, key))

                self.session_new.add(new_obj)
