# -*- encoding: utf-8 -*-

from storm.locals import Pickle, Int, Bool, Pickle, Unicode, DateTime

from globaleaks.db.base_updater import TableReplacer
from globaleaks.models import Model

class Node_version_11(Model):
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
    subtitle = Pickle()

    stats_update_time = Int()

    maximum_namesize = Int()
    maximum_textsize = Int()
    maximum_filesize = Int()
    tor2web_admin = Bool()
    tor2web_submission = Bool()
    tor2web_receiver = Bool()
    tor2web_unauth = Bool()

    postpone_superpower = Bool()
    can_delete_submission = Bool()
    ahmia = Bool()
    wizard_done = Bool(default=False)
    anomaly_checks = Bool(default=False)

    exception_email = Unicode()

class Replacer1112(TableReplacer):

    def migrate_Node(self):
        old_node = self.store_old.find(self.get_right_model("Node", 11)).one()

        new_node = self.get_right_model("Node", 12)()

        new_node.name = old_node.name
        new_node.public_site = old_node.public_site
        new_node.hidden_service = old_node.hidden_service
        new_node.email = old_node.email
        new_node.receipt_salt = old_node.receipt_salt
        new_node.last_update = old_node.last_update

        new_node.languages_enabled = old_node.languages_enabled
        new_node.default_language = old_node.default_language

        new_node.description = old_node.description
        new_node.presentation = old_node.presentation
        new_node.footer = old_node.footer
        new_node.subtitle = old_node.subtitle

        new_node.stats_update_time = old_node.stats_update_time

        new_node.maximum_namesize = old_node.maximum_namesize
        new_node.maximum_textsize = old_node.maximum_textsize
        new_node.maximum_filesize = old_node.maximum_filesize
        new_node.tor2web_admin = old_node.tor2web_admin
        new_node.tor2web_submission = old_node.tor2web_submission
        new_node.tor2web_receiver = old_node.tor2web_receiver
        new_node.tor2web_unauth = old_node.tor2web_unauth

        new_node.postpone_superpower = old_node.postpone_superpower
        new_node.can_delete_submission = old_node.can_delete_submission
        new_node.ahmia = old_node.ahmia
        new_node.wizard_done = old_node.wizard_done
        new_node.anomaly_checks = old_node.anomaly_checks

        new_node.exception_email = old_node.exception_email

        # This is the additional value.
        new_node.allow_unencrypted = True

        self.store_new.add(new_node)

        self.store_new.commit()
