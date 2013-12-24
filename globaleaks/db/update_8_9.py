# -*- encoding: utf-8 -*-

from storm.locals import Bool, Pickle, Unicode, Int, DateTime

from globaleaks.db.base_updater import TableReplacer
from globaleaks.db import acquire_email_templates
from globaleaks.models import Model
from globaleaks import LANGUAGES_SUPPORTED_CODES

class Context_version_8(Model):
    """
    This model keeps track of specific contexts settings
    """
    __storm_table__ = 'context'
    unique_fields = Pickle()
    localized_fields = Pickle()
    selectable_receiver = Bool()
    escalation_threshold = Int()
    tip_max_access = Int()
    file_max_download = Int()
    file_required = Bool()
    tip_timetolive = Int()
    submission_timetolive = Int()
    receipt_regexp = Unicode()
    last_update = DateTime()
    tags = Pickle()
    name = Pickle()
    description = Pickle()
    receiver_introduction = Pickle()
    fields_introduction = Pickle()
    select_all_receivers = Bool()
    postpone_superpower = Bool()
    can_delete_submission = Bool()
    maximum_selectable_receivers = Int()
    require_file_description = Bool()
    delete_consensus_percentage = Int()
    require_pgp = Bool()
    show_small_cards = Bool()
    
    # + is added
    # presentation_order = Int()


class Receiver_version_8(Model):
    __storm_table__ = 'receiver'

    user_id = Unicode()
    name = Unicode()
    description = Pickle()
    gpg_key_info = Unicode()
    gpg_key_fingerprint = Unicode()
    gpg_key_status = Unicode()
    gpg_key_armor = Unicode()
    gpg_enable_notification = Bool()
    gpg_enable_files = Bool()
    mail_address = Unicode()
    can_delete_submission = Bool()
    postpone_superpower = Bool()
    receiver_level = Int()
    last_update = DateTime()
    tags = Pickle()
    tip_notification = Bool()
    comment_notification = Bool()
    file_notification = Bool()
    message_notification = Bool()

    # + is added
    # presentation_order = Int()


class Replacer89(TableReplacer):

    def migrate_Context(self):
        print "%s Context migration assistant: (presentation_order) #%d" % (
            self.std_fancy, self.store_old.find(self.get_right_model("Context", 8)).count() )

        old_contexts = self.store_old.find(self.get_right_model("Context", 8))

        for old_obj in old_contexts:

            new_obj = self.get_right_model("Context", 9)()

            for k, v in new_obj._storm_columns.iteritems():

                if v.name == 'presentation_order':
                    new_obj.presentation_order = 0
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name) )

            self.store_new.add(new_obj)
        self.store_new.commit()


    def migrate_Receiver(self):
        print "%s Receiver migration assistant: (presentation_order) #%d" % (
            self.std_fancy, self.store_old.find(self.get_right_model("Receiver", 8)).count() )

        old_contexts = self.store_old.find(self.get_right_model("Receiver", 8))

        for old_obj in old_contexts:

            new_obj = self.get_right_model("Receiver", 9)()

            for k, v in new_obj._storm_columns.iteritems():

                if v.name == 'presentation_order':
                    new_obj.presentation_order = 0
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name) )

            self.store_new.add(new_obj)
        self.store_new.commit()
