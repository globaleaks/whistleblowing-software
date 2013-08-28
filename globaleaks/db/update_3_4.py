# -*- encoding: utf-8 -*-

from globaleaks.db.base_updater import TableReplacer
from globaleaks.models import Model, ReceiverFile, InternalFile, User
from globaleaks.utils import datetime_null
from storm.locals import Bool, Pickle, Unicode, Int, DateTime

class Node_version_3(Model):
    __storm_table__ = 'node'

    name = Unicode()
    public_site = Unicode()
    hidden_service = Unicode()
    email = Unicode()
    languages_supported = Pickle()
    languages_enabled = Pickle()
    salt = Unicode()
    receipt_salt = Unicode()
    password = Unicode()
    last_update = DateTime()
    database_version = Int()
    description = Pickle()
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

class ReceiverFile_version_3(Model):
    __storm_table__ = 'receiverfile'

    internaltip_id = Unicode()
    internalfile_id = Unicode()
    receiver_id = Unicode()
    file_path = Unicode()
    downloads = Int()
    last_access = DateTime()
    mark = Unicode()

class Replacer34(TableReplacer):

    def migrate_Node(self):

        print "%s Node migration assistant (presentation, default_language, support of User table)" % self.std_fancy

        old_node = self.store_old.find(self.get_right_model("Node", 3)).one()

        admin_dict = {
            'username': u'admin',
            'password': old_node.password,
            'salt': old_node.salt,
            'role': u'admin',
            'state': u'enabled',
            'failed_login_count': 0,
        }

        admin_user = self.get_right_model("User", 4)(admin_dict)
        admin_user.last_login = datetime_null()
        admin_user.first_failed = datetime_null()

        self.store_new.add(admin_user)

        new_node = self.get_right_model("Node", 4)()

        # version 4 new entries!
        new_node.presentation = dict({ "en" : "Welcome @ %s" % old_node.name })
        new_node.default_language = 'en'
        # salt and password do not exist anymore
        # new_node.salt = old_node.salt
        # new_node.password = old_node.password

        new_node.id = old_node.id
        new_node.name = old_node.name
        new_node.public_site = old_node.public_site
        new_node.hidden_service = old_node.hidden_service
        new_node.email = old_node.email
        new_node.receipt_salt = old_node.receipt_salt
        new_node.password = old_node.password
        new_node.database_version = 4
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
        new_node.description = old_node.description
        new_node.languages_enabled = old_node.languages_enabled
        new_node.languages_supported = old_node.languages_supported
        new_node.last_update = old_node.last_update
        new_node.creation_date = old_node.creation_date

        self.store_new.add(new_node)

        self.store_new.commit()

    def migrate_User(self):
        # the table is created here and filled in migrate_Node and migrate_Receiver
        pass

    def migrate_Receiver(self):
        print "%s Receiver migration assistant, (support for User table): #%d" % (
            self.std_fancy, self.store_old.find(self.get_right_model("Receiver", 3)).count() )

        old_rs = self.store_old.find(self.get_right_model("Receiver", 3))

        for old_r in old_rs:

            new_obj = self.get_right_model("Receiver", 4)()
            
            receiver_user_dict = {
                    'username': old_r.username,
                    'password': old_r.password,
                    'salt': old_r.username, # in this version the email
                                            # was used as salt
                    'role': u'receiver',
                    'state': u'enabled',
                    'failed_login_count': 0,
            }

            receiver_user = User(receiver_user_dict)
            receiver_user.last_login = datetime_null()
            receiver_user.first_failed = datetime_null()

            self.store_new.add(receiver_user)

            # version 5 new entry!
            new_obj.user = receiver_user

            # these fields do not exist anymore
            # new_obj.username = old_obj.username
            # new_obj.password = old_obj.password
            # new_obj.last_access = old_obj.last_access

            new_obj.creation_date = old_r.creation_date
            new_obj.name = old_r.name
            new_obj.description = old_r.description
            new_obj.gpg_key_info = old_r.gpg_key_info
            new_obj.gpg_key_fingerprint = old_r.gpg_key_fingerprint
            new_obj.gpg_key_status = old_r.gpg_key_status
            new_obj.gpg_key_armor = old_r.gpg_key_armor
            new_obj.gpg_enable_notification = old_r.gpg_enable_notification
            new_obj.gpg_enable_files = old_r.gpg_enable_files
            new_obj.notification_fields = old_r.notification_fields
            new_obj.can_delete_submission = old_r.can_delete_submission
            new_obj.receiver_level = old_r.receiver_level
            new_obj.failed_login = old_r.failed_login
            new_obj.last_update = old_r.last_update
            new_obj.tags = old_r.tags
            new_obj.tip_notification = old_r.tip_notification
            new_obj.comment_notification = old_r.comment_notification
            new_obj.file_notification = old_r.file_notification

            #self.store_new.add(new_obj)
        self.store_new.commit()

    def migrate_ReceiverFile(self):

        assert ReceiverFile._status_list[0] == 'cloned'
        assert ReceiverFile._status_list[1] == 'reference'
        assert ReceiverFile._status_list[2] == 'encrypted'

        print "%s ReceiverFile migration assistant, (supporting size, statuses): #%d" % (
            self.std_fancy, self.store_old.find(ReceiverFile_version_3).count() )

        old_rf = self.store_old.find(ReceiverFile_version_3)

        for orf in old_rf:

            new_obj = self.get_right_model("ReceiverFile", 4)()

            # the default status is reference, before encryption is enabled
            new_obj.status = ReceiverFile._status_list[1] # reference
            # and then, the length of the file remain the same (reference don't works in migration!)
            internal_related = self.store_old.find(InternalFile, InternalFile.id == orf.internalfile_id).one()
            new_obj.size = internal_related.size

            new_obj.id = orf.id
            new_obj.internaltip_id = orf.internaltip_id
            new_obj.internalfile_id = orf.internalfile_id
            new_obj.receiver_id = orf.receiver_id
            new_obj.file_path = orf.file_path
            new_obj.creation_date = orf.creation_date
            new_obj.mark = orf.mark
            new_obj.downloads = orf.downloads

            self.store_new.add(new_obj)
        self.store_new.commit()
