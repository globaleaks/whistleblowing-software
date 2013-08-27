# -*- encoding: utf-8 -*-

from globaleaks.db.base_updater import TableReplacer
from globaleaks.models import Model, User
from globaleaks.utils import datetime_null
from storm.locals import Bool, Pickle, Unicode, Int, DateTime
from globaleaks import DATABASE_VERSION

class User_version_4(Model):
    __storm_table__ = 'user'

    username = Unicode()
    password = Unicode()
    salt = Unicode()
    role = Unicode()
    state = Unicode()
    last_login = DateTime()
    first_failed = DateTime()
    failed_login_count = Int()

class Node_version_4(Model):
    __storm_table__ = 'node'

    name = Unicode()
    public_site = Unicode()
    hidden_service = Unicode()
    email = Unicode()
    receipt_salt = Unicode()
    last_update = DateTime()
    database_version = Int()
    languages_supported = Pickle()
    languages_enabled = Pickle()
    default_language = Unicode()
    description = Pickle()
    presentation = Pickle()
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

class Comment_version_0(Model):
    __storm_table__ = 'comment'

    internaltip_id = Unicode()
    author = Unicode()
    content = Unicode()
    type = Unicode()
    mark = Unicode()

class Replacer56(TableReplacer):

    def migrate_User(self):
        print "%s User migration, enhancement anti bruteforce techniques: #%d" % (
              self.debug_info, self.store_old.find(self.get_right_model("User", 5)).count() )

        old_users = self.store_old.find(self.get_right_model("User", 5))

        for old_user in old_users:

            new_obj = self.get_right_model("User", 6)()
            new_obj.id = old_user.id
            new_obj.username = old_user.username
            new_obj.password = old_user.password
            new_obj.salt = old_user.salt
            new_obj.role = old_user.role
            new_obj.state = old_user.state
            new_obj.last_login = old_user.last_login
            
            # first_failed field has been removed
            # new_obj.first_failed = old_user.first_failed
            
            # last_failed_attempt has been introduced
            new_obj.last_failed_attempt = datetime_null()

            new_obj.failed_login_count = old_user.failed_login_count

            self.store_new.add(new_obj)
        self.store_new.commit()

    def migrate_Node(self):
        print "%s Node migration assistant: (Supports or receiver with postpone superpower) #%d" % (
            self.debug_info, self.store_old.find(self.get_right_model("Node", 5)).count() )

        old_node = self.store_old.find(self.get_right_model("Node", 5)).one()

        new_node = self.get_right_model("Node", 6)()

        # the new entry!
        new_node.postpone_superpower = False #default

        new_node.id = old_node.id
        new_node.name = old_node.name
        new_node.public_site = old_node.public_site
        new_node.hidden_service = old_node.hidden_service
        new_node.email = old_node.email

        new_node.database_version = DATABASE_VERSION
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

        new_node.receipt_salt = old_node.receipt_salt

        new_node.presentation = old_node.presentation
        new_node.description = old_node.description
        new_node.default_language = old_node.default_language
        new_node.languages_enabled = old_node.languages_enabled
        new_node.languages_supported = old_node.languages_supported

        new_node.last_update = old_node.last_update
        new_node.creation_date = old_node.creation_date

        self.store_new.add(new_node)
        self.store_new.commit()

    def migrate_Comment(self):
        """
        add the system_content = Pickle() field
        """

        print "%s Comments migration (added system_content): #%d" % (
            self.debug_info, self.store_old.find(self.get_right_model("Comment", 5)).count())

        old_comments = self.store_old.find(self.get_right_model("Comment", 5))

        for oc in old_comments:

            new_obj = self.get_right_model("Comment", 6)()

            new_obj.author = oc.author
            new_obj.content = oc.content
            new_obj.creation_date = oc.creation_date
            new_obj.id = oc.id
            new_obj.internaltip_id = oc.internaltip_id
            new_obj.mark = oc.mark
            new_obj.type = oc.type
            # system_content can also be not initialized

            self.store_new.add(new_obj)
        self.store_new.commit()

