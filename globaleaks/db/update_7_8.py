# -*- encoding: utf-8 -*-

from storm.locals import Bool, Pickle, Unicode, Int, DateTime

from globaleaks.db.base_updater import TableReplacer
from globaleaks.models import Model
from globaleaks import LANGUAGES_SUPPORTED_CODES

def every_language(default_text):
    return_dict = {}

    for code in LANGUAGES_SUPPORTED_CODES:
        return_dict.update({code : default_text})

    return return_dict

ENCRYPTED_TIP_BODY = ""
ENCRYPTED_TIP_TITLE = ""
PLAINTEXT_TIP_BODY = ""
PLAINTEXT_TIP_TITLE = ""
ZIP_DESCRIPTION = ""


class Context_version_7(Model):
    __storm_table__ = 'context'
    unique_fields = Pickle()
    localized_fields = Pickle()
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
    selectable_receiver = Bool()
    select_all_receivers = Bool()

    # these three fields are now removed
    receipt_description = Pickle()
    submission_introduction = Pickle()
    submission_disclaimer = Pickle()
    # and added
    # + receiver_introduction
    # + fields_introduction

    # + are added granular privileges on:
    # postpone_superpower = Bool()
    # can_delete_submission = Bool()

    # + is added maximum number of selected receiver:
    # maximum_selected_receiver = Int()

    # + is added
    # require_file_description = Bool()

    # + is added
    # delete_consensus_percentage = Int()

    # + is added
    # require_pgp = Bool()


class Node_version_7(Model):
    __storm_table__ = 'node'
    name = Unicode()
    public_site = Unicode()
    hidden_service = Unicode()
    email = Unicode()
    receipt_salt = Unicode()
    last_update = DateTime()
    languages_enabled = Pickle()
    default_language = Unicode()
    description = Pickle()
    presentation = Pickle()
    footer = Pickle()
    stats_update_time = Int()
    maximum_namesize = Int()
    maximum_textsize = Int()
    maximum_filesize = Int()
    tor2web_admin = Bool()
    tor2web_submission = Bool()
    tor2web_tip = Bool()
    tor2web_receiver = Bool()
    tor2web_unauth = Bool()
    exception_email = Unicode()
    postpone_superpower = Bool()
    # + is added granular privileges with:
    # can_delete_submission = Bool()
    # + is added
    # subtitle = Unicode()


class Notification_version_7(Model):
    __storm_table__ = 'notification'
    server = Unicode()
    port = Int()
    username = Unicode()
    password = Unicode()
    source_name = Unicode()
    source_email = Unicode()
    security = Unicode()
    file_template = Pickle()
    comment_template = Pickle()
    file_mail_title = Pickle()
    comment_mail_title = Pickle()

    # those four template are removed
    tip_template = Pickle()
    tip_mail_title = Pickle()
    activation_template = Pickle()
    activation_mail_title = Pickle()

    # + these 5 new templates are added:
    # encrypted_tip_template = Pickle()
    # encrypted_tip_mail_title = Pickle()
    # plaintext_tip_template = Pickle()
    # plaintext_tip_mail_title = Pickle()
    # zip_description = Pickle()


class Receiver_version_7(Model):
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
    receiver_level = Int()
    last_update = DateTime()
    tags = Pickle()
    tip_notification = Bool()
    file_notification = Bool()
    comment_notification = Bool()
    # + is added
    # message_notification = Bool()

    # this is going to be removed
    notification_fields = Pickle()
    # + and substituted without being a dict
    # mail_address = Unicode()

    can_delete_submission = Bool()
    # + are added granular privileges with:
    # postpone_superpower = Bool()


class InternalFile_version_7(Model):
    __storm_table__ = 'internalfile'

    internaltip_id = Unicode()
    name = Unicode()
    sha2sum = Unicode()
    file_path = Unicode()
    content_type = Unicode()
    size = Int()
    mark = Unicode()

    # + is added
    # description = Unicode()


class Replacer78(TableReplacer):


    def migrate_Context(self):
        print "%s Context migration assistant: (privileges, introductions, PGP enforcing) #%d" % (
            self.std_fancy, self.store_old.find(self.get_right_model("Context", 7)).count() )

        old_contexts = self.store_old.find(self.get_right_model("Context", 7))

        for old_obj in old_contexts:

            new_obj = self.get_right_model("Context", 8)()

            for k, v in new_obj._storm_columns.iteritems():

                if v.name == 'receiver_introduction':
                    new_obj.receiver_introduction = every_language(u"Here you can optionally put info on Receivers, policies, etc")
                    continue
                if v.name == 'fields_introduction':
                    new_obj.fields_introduction = every_language(u"You can optionally describe your submission here!")
                    continue
                if v.name == 'postpone_superpower':
                    new_obj.postpone_superpower = False
                    continue
                if v.name == 'can_delete_submission':
                    new_obj.can_delete_submission = False
                    continue
                if v.name == 'maximum_selected_receiver':
                    new_obj.maximum_selected_receiver = 0
                    continue
                if v.name == 'require_file_description':
                    new_obj.require_file_description = False
                    continue
                if v.name == 'delete_consensus_percentage':
                    new_obj.delete_consensus_percentage = 0
                    continue
                if v.name == 'require_pgp':
                    new_obj.require_pgp = False
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name) )

            self.store_new.add(new_obj)
        self.store_new.commit()

    def migrate_InternalFile(self):
        print "%s InternalFile migration assistant: (file description) #%d" % (
            self.std_fancy, self.store_old.find(self.get_right_model("InternalFile", 7)).count() )

        old_internalfiles = self.store_old.find(self.get_right_model("InternalFile", 7))

        for old_obj in old_internalfiles:

            new_obj = self.get_right_model("InternalFile", 8)()

            for k, v in new_obj._storm_columns.iteritems():

                if v.name == 'description':
                    new_obj.description = u''
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name) )

            self.store_new.add(new_obj)
        self.store_new.commit()

    def migrate_Receiver(self):
        print "%s Receiver migration assistant: (privileges, mail address) #%d" % (
            self.std_fancy, self.store_old.find(self.get_right_model("Receiver", 7)).count() )

        old_receivers = self.store_old.find(self.get_right_model("Receiver", 7))

        for old_obj in old_receivers:

            new_obj = self.get_right_model("Receiver", 8)()

            for k, v in new_obj._storm_columns.iteritems():

                if v.name == 'mail_address':
                    new_obj.mail_address = old_obj.notification_fields['mail_address']
                    continue
                if v.name == 'message_notification':
                    new_obj.message_notification = True
                    continue
                if v.name == 'can_delete_submission':
                    new_obj.can_delete_submission = False
                    continue
                if v.name == 'postpone_superpower':
                    new_obj.postpone_superpower = False
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name) )

            self.store_new.add(new_obj)
        self.store_new.commit()


    def migrate_Notification(self):
        print "%s Notification migration assistant: (encrypted/plaintext Tip, zip)" % self.std_fancy

        old_notification = self.store_old.find(self.get_right_model("Notification", 7)).one()
        new_notification = self.get_right_model("Notification", 8)()

        for k, v in new_notification._storm_columns.iteritems():

            if v.name == 'encrypted_tip_template':
                new_notification.encrypted_tip_template = every_language(ENCRYPTED_TIP_BODY)
                continue
            if v.name == 'encrypted_tip_mail_title':
                new_notification.encrypted_tip_mail_title = every_language(ENCRYPTED_TIP_TITLE)
                continue
            if v.name == 'plaintext_tip_template':
                new_notification.plaintext_tip_template  = every_language(PLAINTEXT_TIP_BODY)
                continue
            if v.name == 'plaintext_tip_mail_title':
                new_notification.plaintext_tip_mail_title = every_language(PLAINTEXT_TIP_TITLE)
                continue
            if v.name == 'zip_description':
                new_notification.zip_description = every_language(ZIP_DESCRIPTION)
                continue

            setattr(new_notification, v.name, getattr(old_notification, v.name) )

        self.store_new.add(new_notification)
        self.store_new.commit()


    def migrate_Node(self):
        print "%s Node migration assistant: (privileges, subtitle)" % self.std_fancy

        old_node = self.store_old.find(self.get_right_model("Node", 7)).one()
        new_node = self.get_right_model("Node", 8)()

        for k, v in new_node._storm_columns.iteritems():

            if v.name == 'can_delete_submission':
                new_node.can_delete_submission = False
                continue
            if v.name == 'subtitle':
                new_node.subtitle = every_language(u"Optionally you can put a subtitle")
                continue

            setattr(new_node, v.name, getattr(old_node, v.name) )

        self.store_new.add(new_node)
        self.store_new.commit()



