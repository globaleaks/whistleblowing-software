# -*- encoding: utf-8 -*-

from storm.locals import Bool, Pickle, Unicode, Int, DateTime

from globaleaks.db.base_updater import TableReplacer
from globaleaks.models import Model, ReceiverTip
from globaleaks import DATABASE_VERSION

class Node_version_6(Model):
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
    postpone_superpower = Bool()
    exception_email = Unicode()

class Replacer67(TableReplacer):

    def migrate_Node(self):
        print "%s Node migration assistant: (footer and theme supports)" % self.debug_info

        old_node = self.store_old.find(self.get_right_model("Node", 6)).one()

        new_node = self.get_right_model("Node", 7)()

        # the new entries
        new_node.footer = { 'en' : u"Copyright 2011-2013 Hermes Center for Transparency and Digital Human Rights" }

        new_node.id = old_node.id
        new_node.name = old_node.name
        new_node.public_site = old_node.public_site
        new_node.hidden_service = old_node.hidden_service
        new_node.email = old_node.email

        new_node.postpone_superpower = old_node.postpone_superpower
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

