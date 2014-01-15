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

class Notification_version_8(Model):
    __storm_table__ = 'notification'
    server = Unicode()
    port = Int()
    username = Unicode()
    password = Unicode()
    source_name = Unicode()
    source_email = Unicode()
    security = Unicode()
    encrypted_tip_template = Pickle()
    encrypted_tip_mail_title = Pickle()
    plaintext_tip_template = Pickle()
    plaintext_tip_mail_title = Pickle()
    zip_description = Pickle()

    # - these existent templates are renamed and duplicated
    file_template = Pickle()
    file_mail_title = Pickle()
    comment_template = Pickle()
    comment_mail_title = Pickle()
    message_template = Pickle()
    message_mail_title = Pickle()

    # + these are the new ones:
    # encrypted_file_mail_template = Pickle()
    # encrypted_file_mail_title = Pickle()
    # plaintext_file_mail_template = Pickle()
    # plaintext_file_mail_title = Pickle()
    # encrypted_comment_template = Pickle()
    # encrypted_comment_mail_title = Pickle()
    # plaintext_comment_template = Pickle()
    # plaintext_comment_mail_title = Pickle()
    # encrypted_message_template = Pickle()
    # encrypted_message_mail_title = Pickle()
    # plaintext_message_template = Pickle()
    # plaintext_message_mail_title = Pickle()



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

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)
        self.store_new.commit()


    def migrate_Receiver(self):
        print "%s Receiver migration assistant: (presentation_order) #%d" % (
            self.std_fancy, self.store_old.find(self.get_right_model("Receiver", 8)).count() )

        old_receivers = self.store_old.find(self.get_right_model("Receiver", 8))

        for old_obj in old_receivers:

            new_obj = self.get_right_model("Receiver", 9)()

            for k, v in new_obj._storm_columns.iteritems():

                if v.name == 'presentation_order':
                    new_obj.presentation_order = 0
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)
        self.store_new.commit()


    def migrate_InternalFile(self):
        """
        The integration of 'description' happen between the v 7 and 8, but
        InternalFile.description has been set with storm validator after the
        release.

        This mean that old DB can't be converted anymore because description was
        accepted empty (at the moment, from the GLC UI, can't be set a file desc)

        This migrate_InternalFile do not require an update of the version table:
        self.get_right_model("InternalFile", 8)
        and
        self.get_right_model("InternalFile", 9)
        return the same object, and is fine so.
        """
        print "%s InternalFile migration assistant: (file description is mandatory !?) #%d" % (
            self.std_fancy, self.store_old.find(self.get_right_model("InternalFile", 8)).count() )

        old_ifiles = self.store_old.find(self.get_right_model("InternalFile", 8))

        for old_obj in old_ifiles:

            new_obj = self.get_right_model("InternalFile", 9)()

            for k, v in new_obj._storm_columns.iteritems():

                if v.name == 'description':
                    if not old_obj.description or not len(old_obj.description):
                        new_obj.description = "Descriptionless %s file" % old_obj.content_type
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)
        self.store_new.commit()


    def migrate_Notification(self):
        print "%s Notification migration assistant: (encrypted/plaintext duplication)" % self.std_fancy

        old_notification = self.store_old.find(self.get_right_model("Notification", 8)).one()
        new_notification = self.get_right_model("Notification", 9)()

        for k, v in new_notification._storm_columns.iteritems():

            if v.name == 'encrypted_file_template':
                new_notification.encrypted_file_template = old_notification.file_template
                continue
            if v.name == 'encrypted_file_mail_title':
                new_notification.encrypted_file_mail_title  = old_notification.file_mail_title
                continue
            if v.name == 'plaintext_file_template':
                new_notification.plaintext_file_template  = old_notification.file_template
                continue
            if v.name == 'plaintext_file_mail_title':
                new_notification.plaintext_file_mail_title  = old_notification.file_mail_title
                continue

            if v.name == 'encrypted_comment_template':
                new_notification.encrypted_comment_template = old_notification.comment_template
                continue
            if v.name == 'encrypted_comment_mail_title':
                new_notification.encrypted_comment_mail_title  = old_notification.comment_mail_title
                continue
            if v.name == 'plaintext_comment_template':
                new_notification.plaintext_comment_template  = old_notification.comment_template
                continue
            if v.name == 'plaintext_comment_mail_title':
                new_notification.plaintext_comment_mail_title  = old_notification.comment_mail_title
                continue

            if v.name == 'encrypted_message_template':
                new_notification.encrypted_message_template = old_notification.message_template
                continue
            if v.name == 'encrypted_message_mail_title':
                new_notification.encrypted_message_mail_title  = old_notification.message_mail_title
                continue
            if v.name == 'plaintext_message_template':
                new_notification.plaintext_message_template  = old_notification.message_template
                continue
            if v.name == 'plaintext_message_mail_title':
                new_notification.plaintext_message_mail_title  = old_notification.message_mail_title
                continue


            setattr(new_notification, v.name, getattr(old_notification, v.name))

        self.store_new.add(new_notification)
        self.store_new.commit()
