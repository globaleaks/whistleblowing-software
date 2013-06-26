# -*- encoding: utf-8 -*-

from storm.locals import Bool, Pickle, Unicode, Int, DateTime

from globaleaks.db.base_updater import TableReplacer
from globaleaks.models import Model, Node
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


class Replacer12(TableReplacer):

    def migrate_Node(self):

        print "%s Node migration assistant, now you can configure languages" % self.std_fancy

        old_node = self.store_old.find(Node_version_1).one()

        new_node = Node()

        new_node.description = old_node.description
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

        # The new fields, the last version of 'languages' is ignored
        new_node.languages_enabled = [ "en" ]
        new_node.languages_supported = LANGUAGES_SUPPORTED

        self.store_new.add(new_node)


