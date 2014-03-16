# -*- encoding: utf-8 -*-

from storm.locals import Pickle, Int, Bool, Pickle, Unicode, DateTime

from globaleaks.db.base_updater import TableReplacer
from globaleaks.models import Model

class Replacer1011(TableReplacer):


    def migrate_InternalTip(self):
        print "%s InternalTip migration assistant: (presentation order added, format refactored)" % self.std_fancy

        old_itips = self.store_old.find(self.get_right_model("InternalTip", 10))

        for old_itip in old_itips:

            new_itip = self.get_right_model("InternalTip", 10)()

            for k, v in new_itip._storm_columns.iteritems():

                if v.name == 'wb_fields':
                    new_itip.wb_fields = {}
                    i = 0
                    for key in old_itip.wb_fields:
                        new_itip.wb_fields[key] = {
                            u'value': old_itip.wb_fields[key],
                            u'answer_order': i
                        }
                        i += 1
                    continue

                setattr(new_itip, v.name, getattr(old_itip, v.name))

            self.store_new.add(new_itip)
            self.store_new.commit()
        
