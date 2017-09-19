# -*- encoding: utf-8 -*-


from storm.locals import Int, Unicode, DateTime

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import ModelWithID


class InternalFile_v_25(ModelWithID):
    __storm_table__ = 'internalfile'
    creation_date = DateTime()
    internaltip_id = Unicode()
    name = Unicode()
    file_path = Unicode()
    content_type = Unicode()
    size = Int()
    new = Int()
    processing_attempts = Int()


class MigrationScript(MigrationBase):
    def migrate_InternalFile(self):
        old_objs = self.store_old.find(self.model_from['InternalFile'])
        for old_obj in old_objs:
            new_obj = self.model_to['InternalFile']()
            for _, v in new_obj._storm_columns.items():
                if v.name == 'submission':
                    new_obj.submission = True
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)
