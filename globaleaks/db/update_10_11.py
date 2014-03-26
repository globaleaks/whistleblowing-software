# -*- encoding: utf-8 -*-

from storm.locals import Pickle, Int, Bool, Pickle, Unicode, DateTime

from globaleaks.db.base_updater import TableReplacer
from globaleaks.models import Model


# This migration script is quite fake and takes care only in a change of
# format inside a Pickle
#
# the fields format changes from:
#   {field1_id: field1_value, field2_id: field2_value }
#
# to:
#   {field1_id: {value: field1_value, answer_order: 0}, field2_id: {value: field2_value, answer_order: 1} }
#

class InternalTip_version_10(Model): # no change at all!
    __storm_table__ = 'internaltip'
    context_id = Unicode()
    wb_fields = Pickle()
    pertinence_counter = Int()
    expiration_date = DateTime()
    last_activity = DateTime()
    escalation_threshold = Int()
    access_limit = Int()
    download_limit = Int()
    mark = Unicode()

class InternalFile_version_10(Model):
    __storm_table__ = 'internalfile'
    internaltip_id = Unicode()
    name = Unicode()
    file_path = Unicode()
    content_type = Unicode()
    description = Unicode()
    size = Int()
    mark = Unicode()

class Replacer1011(TableReplacer):

    def migrate_InternalTip(self):
        print "%s InternalTip migration assistant: (presentation order added, format refactored)" % self.std_fancy

        old_itips = self.store_old.find(self.get_right_model("InternalTip", 10))

        for old_itip in old_itips:

            new_itip = self.get_right_model("InternalTip", 11)()

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

    def migrate_InternalFile(self):
        print "%s InternalFile migration assistant: (removed sha)" % self.std_fancy

        old_ifiles = self.store_old.find(self.get_right_model("InternalFile", 10))

        for old_ifile in old_ifiles:

            new_ifile = self.get_right_model("InternalFile", 11)()

            for k, v in new_ifile._storm_columns.iteritems():
                setattr(new_ifile, v.name, getattr(old_ifile, v.name))

            self.store_new.add(new_ifile)

        self.store_new.commit()

        
