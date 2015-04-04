# -*- encoding: utf-8 -*-

"""
  Changes
    - node: header_title_receiptpage

"""

from storm.locals import Int, Bool, Unicode, DateTime, JSON
from globaleaks.db.base_updater import TableReplacer
from globaleaks.db.datainit import load_appdata
from globaleaks.models import Model
from globaleaks.utils.utility import every_language

class Node_v_18(Model):
    __storm_table__ = 'node'
    name = Unicode()
    public_site = Unicode()
    hidden_service = Unicode()
    email = Unicode()
    receipt_salt = Unicode()
    last_update = DateTime()
    receipt_regexp = Unicode()
    languages_enabled = JSON()
    default_language = Unicode()
    default_timezone = Int()
    description = JSON()
    presentation = JSON()
    footer = JSON()
    security_awareness_title = JSON()
    security_awareness_text = JSON()
    stats_update_time = Int()
    maximum_namesize = Int()
    maximum_textsize = Int()
    maximum_filesize = Int()
    tor2web_admin = Bool()
    tor2web_submission = Bool()
    tor2web_receiver = Bool()
    tor2web_unauth = Bool()
    allow_unencrypted = Bool()
    allow_iframes_inclusion = Bool()
    postpone_superpower = Bool()
    can_delete_submission = Bool()
    ahmia = Bool()
    wizard_done = Bool()
    disable_privacy_badge = Bool()
    disable_security_awareness_badge = Bool()
    disable_security_awareness_questions = Bool()
    whistleblowing_question = JSON()
    whistleblowing_button = JSON()
    enable_custom_privacy_badge = Bool()
    custom_privacy_badge_tor = JSON()
    custom_privacy_badge_none = JSON()
    header_title_homepage = JSON()
    header_title_submissionpage = JSON()
    landing_page = Unicode()
    exception_email = Unicode()


class Replacer1819(TableReplacer):

    def migrate_Node(self):
        print "%s Node migration assistant: header_title_receiptpage" % self.std_fancy

        appdata_dict = load_appdata()

        old_node = self.store_old.find(self.get_right_model("Node", 18)).one()
        new_node = self.get_right_model("Node", 19)()

        for _, v in new_node._storm_columns.iteritems():

            if v.name == 'header_title_receiptpage':
                # check needed to preserve funtionality if appdata will be altered in the future
                if v.name in appdata_dict['node']:
                    new_node.header_title_receiptpage = appdata_dict['node']['header_title_receiptpage']
                else:
                    new_node.header_title_receiptpage = every_language("")
                continue

            setattr(new_node, v.name, getattr(old_node, v.name))

        self.store_new.add(new_node)
        self.store_new.commit()
