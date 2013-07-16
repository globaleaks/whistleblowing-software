# -*- encoding: utf-8 -*-

from globaleaks.db.base_updater import TableReplacer
from globaleaks.models import Node, Model
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


class Replacer34(TableReplacer):

    def migrate_Node(self):

        print "%s Node migration assistant (presentation, default_language)" % self.std_fancy

        old_node = self.store_old.find(Node_version_3).one()
        new_node = Node()

        # version 4 new entries!
        new_node.presentation = dict({ "en" : "Welcome @ %s" % old_node.name })
        new_node.default_language = 'en'

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
        new_node.description = old_node.description
        new_node.languages_enabled = old_node.languages_enabled
        new_node.languages_supported = old_node.languages_supported

        self.store_new.add(new_node)
        self.store_new.commit()


