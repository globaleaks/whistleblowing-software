# -*- encoding: utf-8 -*-

from storm.locals import Bool, Pickle, Unicode, Int, DateTime

from globaleaks.db.base_updater import TableReplacer
from globaleaks.models import Model, Node, Context, Receiver, Notification
from globaleaks import LANGUAGES_SUPPORTED

class Node_version_1(Model):
    __storm_table__ = 'node'

    description = Unicode()
    name = Unicode()
    public_site = Unicode()
    hidden_service = Unicode()
    email = Unicode()
    languages = Pickle()
    salt = Unicode()
    receipt_salt = Unicode()
    password = Unicode()
    last_update = DateTime()
    database_version = Int()
    stats_update_time = Int()
    maximum_namesize = Int()
    maximum_descsize = Int()
    maximum_textsize = Int()
    maximum_filesize = Int()
    tor2web_admin = Bool()
    tor2web_submission = Bool()
    tor2web_tip = Bool()
    tor2web_receiver = Bool()
    tor2web_unauth = Bool()
    exception_email = Unicode()

class Context_version_1(Model):
    __storm_table__ = 'context'

    name = Unicode()
    description = Unicode()
    fields = Pickle()
    selectable_receiver = Bool()
    escalation_threshold = Int()
    tip_max_access = Int()
    file_max_download = Int()
    tip_timetolive = Int()
    submission_timetolive = Int()
    file_required = Bool()
    last_update = DateTime()
    receipt_regexp = Unicode()
    receipt_description = Unicode()
    submission_introduction = Unicode()
    submission_disclaimer = Unicode()
    file_required = Bool()
    tags = Pickle()

class Receiver_version_1(Model):
    __storm_table__ = 'receiver'

    name = Unicode()
    description = Unicode()
    username = Unicode()
    password = Unicode()
    gpg_key_info = Unicode()
    gpg_key_fingerprint = Unicode()
    gpg_key_status = Unicode()
    gpg_key_armor = Unicode()
    gpg_enable_notification = Bool()
    gpg_enable_files = Bool()
    notification_fields = Pickle()
    can_delete_submission = Bool()
    receiver_level = Int()
    failed_login = Int()
    last_update = DateTime()
    last_access = DateTime()
    tags = Pickle()
    tip_notification = Bool()
    comment_notification = Bool()
    file_notification = Bool()

class Notification_version_1(Model):
    __storm_table__ = 'notification'

    server = Unicode()
    port = Int()
    username = Unicode()
    password = Unicode()
    security = Unicode()
    tip_template = Unicode()
    file_template = Unicode()
    comment_template = Unicode()
    activation_template = Unicode()
    tip_mail_title = Unicode()
    file_mail_title = Unicode()
    comment_mail_title = Unicode()
    activation_mail_title = Unicode()


class Replacer12(TableReplacer):

    def migrate_Node(self):

        print "%s Node migration assistant, now you can configure languages" % self.std_fancy

        old_node = self.store_old.find(Node_version_1).one()
        new_node = self.get_right_model("Node", 2)()

        new_node.id = old_node.id
        new_node.name = old_node.name
        new_node.public_site = old_node.public_site
        new_node.hidden_service = old_node.hidden_service
        new_node.email = old_node.email
        new_node.salt = old_node.salt
        new_node.receipt_salt = old_node.receipt_salt
        new_node.password = old_node.password
        new_node.last_update = old_node.last_update
        new_node.database_version = 2
        new_node.stats_update_time = old_node.stats_update_time
        new_node.maximum_descsize = old_node.maximum_descsize
        new_node.maximum_filesize = old_node.maximum_filesize
        new_node.maximum_namesize = old_node.maximum_namesize
        new_node.maximum_textsize = old_node.maximum_textsize
        new_node.tor2web_admin = old_node.tor2web_admin
        new_node.tor2web_receiver = old_node.tor2web_receiver
        new_node.tor2web_submission = old_node.tor2web_submission
        new_node.tor2web_tip = old_node.tor2web_tip
        new_node.tor2web_unauth = old_node.tor2web_unauth
        new_node.exception_email = old_node.exception_email

        new_node.description = { "en" : old_node.description }

        # The new fields, the last version of 'languages' is ignored
        new_node.languages_enabled = [ "en" ]
        new_node.languages_supported = LANGUAGES_SUPPORTED

        self.store_new.add(new_node)
        self.store_new.commit()

    def migrate_Context(self):

        print "%s Context migration assistant, extending with languages supports: #%d" % (
            self.std_fancy, self.store_old.find(Context_version_1).count() )

        old_contexts = self.store_old.find(Context_version_1)

        for ocntx in old_contexts:

            new_obj = self.get_right_model("Context", 2)()

            new_fields = []
            for single_lf in ocntx.fields:
                localized_f = {
                    "key": single_lf['name'],
                    "name": { "en" : single_lf['name'] },
                    "presentation_order" : single_lf['presentation_order'],
                    "required" : single_lf['required'],
                    "hint" : { "en" : single_lf['hint'] },
                    "type" : single_lf['type']
                }
                new_fields.append(localized_f)
            new_obj.fields = new_fields

            new_obj.name = {
                    "en" : ocntx.name
            }
            new_obj.description = {
                    "en" : ocntx.description
            }
            new_obj.receipt_description = {
                    "en" : ocntx.receipt_description
            }
            new_obj.submission_introduction = {
                    "en" : ocntx.submission_introduction
            }
            new_obj.submission_disclaimer = {
                    "en" : ocntx.submission_disclaimer
            }

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
            new_obj.tags = ocntx.tags

            self.store_new.add(new_obj)
        self.store_new.commit()

    def migrate_Receiver(self):

        print "%s Receivers migration assistant, extension with languages supports: #%d" % (
            self.std_fancy, self.store_old.find(Receiver_version_1).count() )

        old_receivers = self.store_old.find(Receiver_version_1)

        for orcvr in old_receivers:

            new_obj = self.get_right_model("Receiver", 2)()

            new_obj.username = orcvr.username
            new_obj.id = orcvr.id
            new_obj.name = orcvr.name
            new_obj.password = orcvr.password
            new_obj.can_delete_submission = orcvr.can_delete_submission
            new_obj.comment_notification = orcvr.comment_notification
            new_obj.tip_notification = orcvr.tip_notification
            new_obj.file_notification = orcvr.file_notification
            new_obj.creation_date = orcvr.creation_date
            new_obj.last_access = orcvr.last_access
            new_obj.last_update = orcvr.last_update
            new_obj.failed_login = orcvr.failed_login
            new_obj.receiver_level = orcvr.receiver_level
            new_obj.notification_fields = orcvr.notification_fields
            new_obj.tags = orcvr.tags
            new_obj.gpg_key_armor = orcvr.gpg_key_armor
            new_obj.gpg_key_fingerprint = orcvr.gpg_key_fingerprint
            new_obj.gpg_key_info = orcvr.gpg_key_info
            new_obj.gpg_key_status = orcvr.gpg_key_status

            new_obj.description = { "en" : orcvr.description }

            self.store_new.add(new_obj)
        self.store_new.commit()

    def migrate_Notification(self):

        print "%s Notification migration assistant, extension with languages supports" % self.std_fancy

        old_notif= self.store_old.find(Notification_version_1).one()
        new_notif= self.get_right_model("Notification", 2)()

        new_notif.id = old_notif.id
        new_notif.server = old_notif.server
        new_notif.port = old_notif.port
        new_notif.username  = old_notif.username
        new_notif.password = old_notif.password
        new_notif.security = old_notif.security

        new_notif.tip_template =  { "en" : old_notif.tip_template }
        new_notif.file_template =  { "en" : old_notif.file_template }
        new_notif.comment_template = { "en" : old_notif.comment_template }
        new_notif.activation_template = { "en" : old_notif.activation_template }
        new_notif.tip_mail_title = { "en" : old_notif.tip_mail_title }
        new_notif.file_mail_title = { "en" : old_notif.file_mail_title }
        new_notif.comment_mail_title = { "en" : old_notif.comment_mail_title }
        new_notif.activation_mail_title = { "en" : old_notif.activation_mail_title }

        self.store_new.add(new_notif)
        self.store_new.commit()


