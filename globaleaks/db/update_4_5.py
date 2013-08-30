# -*- encoding: utf-8 -*-

from globaleaks.db.base_updater import TableReplacer
from globaleaks.models import Model, ReceiverTip, Notification
from storm.locals import Bool, Pickle, Unicode, Int, DateTime

class Context_version_2(Model):
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

class ReceiverFile_version_4(Model):
    __storm_table__ = 'receiverfile'

    internaltip_id = Unicode()
    internalfile_id = Unicode()
    receiver_id = Unicode()
    file_path = Unicode()
    size = Int()
    downloads = Int()
    last_access = DateTime()
    mark = Unicode()
    status = Unicode()

class Notification_version_2(Model):
    __storm_table__ = 'notification'

    server = Unicode()
    port = Int()
    username = Unicode()
    password = Unicode()
    security = Unicode()

    tip_template = Pickle()
    file_template = Pickle()
    comment_template = Pickle()
    activation_template = Pickle()
    tip_mail_title = Pickle()
    file_mail_title = Pickle()
    comment_mail_title = Pickle()
    activation_mail_title = Pickle()


class Replacer45(TableReplacer):

    def migrate_Context(self):

        print "%s Context migration assistant (added select_all_receivers field)" % self.std_fancy
        old_contexts = self.store_old.find(self.get_right_model("Context", 4))

        for old_context in old_contexts:

            new_context = self.get_right_model("Context", 5)()

            new_context.id = old_context.id
            new_context.creation_date = old_context.creation_date
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

            # that's the new field here
            new_context.select_all_receivers = True

            self.store_new.add(new_context)

        self.store_new.commit()

    def migrate_ReceiverFile(self):

        print "%s ReceiverFile migration assistante (added ReceiverTip reference)" % self.std_fancy
        old_rcfs = self.store_old.find(self.get_right_model("ReceiverFile", 4))

        for orf in old_rcfs:

            new_rf = self.get_right_model("ReceiverFile", 5)()

            new_rf.id = orf.id
            new_rf.creation_date = orf.creation_date
            new_rf.internaltip_id = orf.internaltip_id
            new_rf.internalfile_id =  orf.internalfile_id
            new_rf.receiver_id =  orf.receiver_id
            new_rf.file_path = orf.file_path
            new_rf.size = orf.size
            new_rf.downloads = orf.downloads
            new_rf.last_access =  orf.last_access
            new_rf.mark = orf.mark
            new_rf.status = orf.status

            # The first time ReceiverTip is changed, need to be used
            # self.get_right_model("ReceiverTip", 4) instead of ReceiverTip
            receiver_tip = self.store_old.find(ReceiverTip,
                    (
                        ReceiverTip.internaltip_id == orf.internaltip_id,
                        ReceiverTip.receiver_id == orf.receiver_id
                    ) ).one()
            new_rf.receiver_tip_id = receiver_tip.id

            self.store_new.add(new_rf)

        self.store_new.commit()

    def migrate_Notification(self):
        print "%s Notification migration assistante (added mail From: field)" % self.std_fancy

        on = self.store_old.find(self.get_right_model("Notification", 4)).one()

        # remind, need to be update when Notification became updated!
        new_obj = Notification()

        new_obj.id = on.id
        new_obj.creation_date = on.creation_date
        new_obj.password = on.password
        new_obj.port = on.port
        new_obj.security = on.security
        new_obj.server = on.server
        new_obj.username = on.username

        new_obj.comment_mail_title = on.comment_mail_title
        new_obj.comment_template = on.comment_template
        new_obj.file_mail_title = on.file_mail_title
        new_obj.file_template = on.file_template
        new_obj.tip_mail_title = on.tip_mail_title
        new_obj.tip_template = on.tip_template

        node_info = self.store_old.find(self.get_right_model("Node", 4)).one()
        # The two new fields, avail since version 5
        new_obj.source_name = node_info.name
        new_obj.source_email = on.username

        self.store_new.add(new_obj)
        self.store_new.commit()
