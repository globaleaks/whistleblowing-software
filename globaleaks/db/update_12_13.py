# -*- encoding: utf-8 -*-

"""
  Changes
    Node table:
      - introduced localized field terms_and_conditions;
        the migration script takes care of initializing the new field using the localized appdata.
"""

from storm.locals import Pickle, Int, Bool, Pickle, Unicode, DateTime

from globaleaks.db.base_updater import TableReplacer
from globaleaks.models import Model

from globaleaks.db.datainit import opportunistic_appdata_init

class Node_version_12(Model):
    __storm_table__ = 'node'
    name = Unicode()
    public_site = Unicode()
    hidden_service = Unicode()
    email = Unicode()
    receipt_salt = Unicode()
    last_update = DateTime()
    receipt_regexp = Unicode()
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
    allow_unencrypted = Bool()
    postpone_superpower = Bool()
    can_delete_submission = Bool()
    ahmia = Bool()
    wizard_done = Bool()
    anomaly_checks = Bool()
    exception_email = Unicode()

class Replacer1213(TableReplacer):

    def migrate_Node(self):
        print "%s Node migration assistant: (terms_and_conditions)" % self.std_fancy

        appdata = opportunistic_appdata_init()

        old_node = self.store_old.find(self.get_right_model("Node", 12)).one()
        new_node = self.get_right_model("Node", 13)()

        for k, v in new_node._storm_columns.iteritems():

            if v.name == 'terms_and_conditions':
                new_node.terms_and_conditions = appdata['node_terms_and_conditions'] 
                continue

            setattr(new_node, v.name, getattr(old_node, v.name) )

        self.store_new.add(new_node)
        self.store_new.commit()
