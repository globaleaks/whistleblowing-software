# -*- encoding: utf-8 -*-

from storm.locals import Pickle, Int, Bool, Pickle, Unicode, DateTime

from globaleaks.db.base_updater import TableReplacer
from globaleaks.models import Model

class ApplicationData_version_10(Model):
    __storm_table__ = 'applicationdata'
    fields_version = Int()
    fields = Pickle()


class Node_version_9(Model):
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
    exception_email = Unicode()

    # is added wizard_done = Bool()



class Replacer910(TableReplacer):


    def migrate_Node(self):
        print "%s Node migration assistant: (privileges, subtitle)" % self.std_fancy

        old_node = self.store_old.find(self.get_right_model("Node", 9)).one()
        new_node = self.get_right_model("Node", 10)()

        for k, v in new_node._storm_columns.iteritems():

            if v.name == 'wizard_done':
                new_node.wizard_done = True
                continue

            setattr(new_node, v.name, getattr(old_node, v.name) )

        self.store_new.add(new_node)
        self.store_new.commit()


    def epilogue(self):
        print "%s Epilogue function in migration assistant: (stats, appdata)" % \
              self.std_fancy

        # first stats is not generated here, do not need
        appdata = ApplicationData_version_10()
        appdata.fields_version = 0
        appdata.fields = None

        self.store_new.add(appdata)
        self.store_new.commit()


