# -*- encoding: utf-8 -*-

from storm.locals import Pickle, Int

from globaleaks.db.base_updater import TableReplacer
from globaleaks.models import Model

class ApplicationData_version_10(Model):
    __storm_table__ = 'applicationdata'
    fields_version = Int()
    fields = Pickle()


class Replacer910(TableReplacer):

    def epilogue(self):
        print "%s Epilogue function in migration assistant: (stats, appdata)" %\
            self.std_fancy

        # first stats is not generated here, do not need
        appdata = ApplicationData_version_10()
        appdata.fields_version = 0
        appdata.fields = None

        self.store_new.add(appdata)
        self.store_new.commit()


