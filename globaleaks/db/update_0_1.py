# -*- encoding: utf-8 -*-

from storm.locals import Bool, Pickle, Unicode, Int, DateTime

from globaleaks.db.base_updater import TableReplacer
from globaleaks.models import Model, Receiver

class Node_version_0(Model):
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

class Receiver_version_0(Model):
    """
    Fields source from:
    https://github.com/globaleaks/GLBackend/blob/f9d5aa21b8472cc48f3fb3691c67f0d9b871db86/globaleaks/models.py
    """
    __storm_table__ = 'receiver'

    name = Unicode()
    description = Unicode()
    username = Unicode()
    password = Unicode()
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

class Replacer01(TableReplacer):

    def migrate_Node(self):

        print "%s Node migration assistant, now you can configure languages" % self.std_fancy

        old_node = self.store_old.find(Node_version_0).one()
        new_node = self.get_right_model("Node", 1)()

        new_node.id = old_node.id
        new_node.description = old_node.description
        new_node.name = old_node.name
        new_node.public_site = old_node.public_site
        new_node.hidden_service = old_node.hidden_service
        new_node.email = old_node.email
        new_node.languages = old_node.languages
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

        self.store_new.add(new_node)
        self.store_new.commit()

    def migrate_Receiver(self):
        from globaleaks.db.update_1_2 import Receiver_version_1

        print "%s Receivers migration assistant, extension with GPG capabilities: #%d" % (
              self.std_fancy, self.store_old.find(Receiver_version_0).count() )

        old_receivers = self.store_old.find(Receiver_version_0)

        for orcvr in old_receivers:

            new_obj = Receiver_version_1()

            new_obj.username = unicode(orcvr.username)
            new_obj.id = orcvr.id
            new_obj.name = unicode(orcvr.name)
            new_obj.password = unicode(orcvr.password)
            new_obj.description = unicode(orcvr.description)

            new_obj.can_delete_submission = orcvr.can_delete_submission
            new_obj.comment_notification = orcvr.comment_notification
            new_obj.tip_notification = orcvr.tip_notification
            new_obj.file_notification = orcvr.file_notification

            new_obj.creation_date = orcvr.creation_date
            new_obj.last_access = orcvr.last_access
            new_obj.last_update = orcvr.last_update

            new_obj.failed_login = orcvr.failed_login
            new_obj.receiver_level = orcvr.receiver_level
            new_obj.notification_fields = dict(orcvr.notification_fields)
            new_obj.tags = orcvr.tags

            # new fields
            new_obj.gpg_key_armor = None
            new_obj.gpg_key_fingerprint = None
            new_obj.gpg_key_info = None
            new_obj.gpg_key_status = Receiver._gpg_types[0] # Disable
            new_obj.gpg_enable_notification = False
            new_obj.gpg_enable_files = False

            self.store_new.add(new_obj)

        self.store_new.commit()
