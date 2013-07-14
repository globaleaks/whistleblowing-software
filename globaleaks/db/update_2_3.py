# -*- encoding: utf-8 -*-

from globaleaks.db.base_updater import TableReplacer
from globaleaks.models import Context
from globaleaks.db.update_form_fields import fields_conversion

class Replacer23(TableReplacer):

    def migrate_Context(self):

        print "%s Context migration assistant, extending : #%d" % (
            self.std_fancy, self.store_old.find(Context).count() )

        old_contexts = self.store_old.find(Context)

        for ocntx in old_contexts:

            new_obj = Context()

            # the only conversion in this revision, its here:
            new_obj.fields = fields_conversion(ocntx.fields)

            new_obj.id = ocntx.id
            new_obj.selectable_receiver = ocntx.selectable_receiver
            new_obj.escalation_threshold = ocntx.escalation_threshold
            new_obj.tip_max_access = ocntx.tip_max_access
            new_obj.file_max_download = ocntx.file_max_download
            new_obj.file_required = ocntx.file_required
            new_obj.tip_timetolive = ocntx.tip_timetolive
            new_obj.submission_timetolive = ocntx.submission_timetolive
            new_obj.last_update = ocntx.last_update
            new_obj.receipt_regexp = ocntx.receipt_regexp
            new_obj.file_required = ocntx.file_required
            new_obj.name = ocntx.name
            new_obj.description = ocntx.description
            new_obj.receipt_description = ocntx.receipt_description
            new_obj.submission_introduction =  ocntx.submission_introduction
            new_obj.submission_disclaimer = ocntx.submission_disclaimer
            new_obj.tags = ocntx.tags

            self.store_new.add(new_obj)
        self.store_new.commit()


