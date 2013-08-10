# -*- encoding: utf-8 -*-

from globaleaks.db.base_updater import TableReplacer
from globaleaks.models import Model, ReceiverFile, InternalFile, User
from globaleaks.utils import datetime_null
from storm.locals import Bool, Pickle, Unicode, Int, DateTime

class Context_version_3(Model):
    __storm_table__ = 'context'

    fields = Pickle()
    selectable_receiver = Bool()
    escalation_threshold = Int()
    tip_max_access = Int()
    file_max_download = Int()
    file_required = Bool()
    tip_timetolive = Int()
    submission_timetolive = Int()
    receipt_regexp = Unicode()
    last_update = DateTime()
    file_required = Bool()
    tags = Pickle()
    name = Pickle()
    description = Pickle()
    receipt_description = Pickle()
    submission_introduction = Pickle()
    submission_disclaimer = Pickle()
    select_all_receivers = Bool()


class Replacer45(TableReplacer):

    def migrate_Context(self):

        print "%s Context migration assistant (added select_all_receivers field)" % self.std_fancy

        old_contexts = self.store_old.find(self.get_right_model("Context", 4))
        
        for old_context in old_contexts:

            new_context = self.get_right_model("Context", 5)()

            new_context.id = old_context.id
            new_context.selectable_receiver = old_context.selectable_receiver
            new_context.escalation_threshold = old_context.escalation_threshold
            new_context.tip_max_access = old_context.tip_max_access
            new_context.file_max_download = old_context.file_max_download
            new_context.file_required = old_context.file_required
            new_context.tip_timetolive = old_context.tip_timetolive
            new_context.submission_timetolive = old_context.submission_timetolive
            new_context.last_update = old_context.last_update
            new_context.receipt_regexp = old_context.receipt_regexp
            new_context.file_required = old_context.file_required
            new_context.name = old_context.name
            new_context.description = old_context.description
            new_context.receipt_description = old_context.receipt_description
            new_context.submission_introduction =  old_context.submission_introduction
            new_context.submission_disclaimer = old_context.submission_disclaimer
            new_context.tags = old_context.tags
            new_context.fields = old_context.fields
            new_context.select_all_receivers = True

            self.store_new.add(new_context)

        self.store_new.commit()
