# -*- encoding: utf-8 -*-

from storm.locals import Pickle, Int, Bool, Unicode, DateTime

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
    # in the 12 release are added two keys:
    # allow_unencrypted and receipt_regexp 
    # moved from Context

class Context_version_11(Model):
    __storm_table__ = 'context'
    unique_fields = Pickle()
    localized_fields = Pickle()
    selectable_receiver = Bool()
    escalation_threshold = Int()
    tip_max_access = Int()
    file_max_download = Int()
    file_required = Bool()
    tip_timetolive = Int()
    submission_timetolive = Int()
    last_update = DateTime()
    tags = Pickle()
    name = Pickle()
    description = Pickle()
    receiver_introduction = Pickle()
    fields_introduction = Pickle()
    select_all_receivers = Bool()
    postpone_superpower = Bool()
    can_delete_submission = Bool()
    maximum_selectable_receivers = Int()
    require_file_description = Bool()
    delete_consensus_percentage = Int()
    require_pgp = Bool()
    show_small_cards = Bool()
    presentation_order = Int()

class ApplicationData_version_11(Model):
    __storm_table__ = 'applicationdata'
    fields_version = Int()
    fields = Pickle()


class Replacer1112(TableReplacer):

    def migrate_Node(self):
        print "%s Node migration assistant: (receipt, encryption only)" % self.std_fancy

        old_node = self.store_old.find(self.get_right_model("Node", 11)).one()
        new_node = self.get_right_model("Node", 12)()

        for _, v in new_node._storm_columns.iteritems():

            if v.name == 'receipt_regexp':
                new_node.receipt_regexp = u'[0-9]{16}'
                continue

            if v.name == 'allow_unencrypted':
                # this is the default only for the migration, because the 
                # old Nodes has not to be broken.
                new_node.allow_unencrypted = True
                continue

            setattr(new_node, v.name, getattr(old_node, v.name) )

        self.store_new.add(new_node)
        self.store_new.commit()

    def migrate_ApplicationData(self):
        print "%s ApplicationData migration assistant: (fields_version rename)" % self.std_fancy

        old_ad = self.store_old.find(self.get_right_model("ApplicationData", 11)).one()
        new_ad = self.get_right_model("ApplicationData", 12)()

        for _, v in new_ad._storm_columns.iteritems():

            if v.name == 'version' :
                new_ad.version = old_ad.fields_version
                continue

            setattr(new_ad, v.name, getattr(old_ad, v.name))

        self.store_new.add(new_ad)
        self.store_new.commit()

    # Context migration: is removed the receipt by the default bahavior

