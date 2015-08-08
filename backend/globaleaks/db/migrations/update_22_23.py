# -*- encoding: utf-8 -*-

from storm.locals import Int, Bool, Unicode, DateTime, JSON, Reference, ReferenceSet
from globaleaks.db.base_updater import TableReplacer
from globaleaks.models import BaseModel, Model


class InternalFile_v_22(Model):
    __storm_table__ = 'internalfile'
    internaltip_id = Unicode()
    name = Unicode()
    file_path = Unicode()
    content_type = Unicode()
    size = Int()
    new = Int()


class Replacer2223(TableReplacer):
    def migrate_InternalFile(self):
        print "%s InternalFile migration assistant" % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("InternalFile", 22))

        for old_obj in old_objs:
            new_obj = self.get_right_model("InternalFile", 23)()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'processing_attempts':
                    new_obj.processing_attempts = 0
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()
