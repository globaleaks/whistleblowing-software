# -*- encoding: utf-8 -*-

"""
  Changes

    Node table:
      - introduced x_frame_options_mode and x_frame_options_allow_from.

    Context table:
      - introduced enable_private_messages

"""

from storm.locals import Pickle, Int, Bool, Pickle, Unicode, DateTime

from globaleaks.db.base_updater import TableReplacer
from globaleaks.models import Model
from globaleaks.db.datainit import opportunistic_appdata_init

class Node_version_13(Model):
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
    terms_and_conditions = Pickle()
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

class Context_version_13(Model):
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
    show_receivers = Bool()
    presentation_order = Int()

class Replacer1314(TableReplacer):

    def migrate_Node(self):
        print "%s Node migration assistant: (x_frame_options_mode, x_frame_options_allow_from," \
                                            "disable_privacy_badge, disable_security_awareness_badge," \
                                            "disable_security_awareness_questions, security_awareness_title," \
                                            "security_awareness_text" % self.std_fancy

        appdata = opportunistic_appdata_init()

        old_node = self.store_old.find(self.get_right_model("Node", 13)).one()
        new_node = self.get_right_model("Node", 14)()

        for k, v in new_node._storm_columns.iteritems():

            if v.name == 'x_frame_options_mode':
                new_node.x_frame_options_mode = 'deny';
                continue

            if v.name == 'x_frame_options_allow_from':
                new_node.x_frame_options_allow_from = '';
                continue

            if v.name == 'disable_privacy_badge':
                new_node.disable_privacy_badge = False
                continue

            if v.name == 'disable_security_awareness_badge':
                new_node.disable_security_awareness_badge = False
                continue

            if v.name == 'disable_security_awareness_questions':
                new_node.disable_security_awareness_questions = False
                continue

            if v.name == 'security_awareness_title':
                new_node.security_awareness_title = appdata['node']['security_awareness_title']
                continue

            if v.name == 'security_awareness_text':
                new_node.security_awareness_text = appdata['node']['security_awareness_text']
                continue

            setattr(new_node, v.name, getattr(old_node, v.name))

        self.store_new.add(new_node)
        self.store_new.commit()

    def migrate_Context(self):
        print "%s Context migration assistant: (enable_private_messages)" % self.std_fancy

        old_contexts = self.store_old.find(self.get_right_model("Context", 13))

        for old_context in old_contexts:

            new_context = self.get_right_model("Context", 14)()

            for k, v in new_context._storm_columns.iteritems():

                if v.name == 'enable_private_messages':
                    new_context.enable_private_messages = True
                    continue

                setattr(new_context, v.name, getattr(old_context, v.name))

            self.store_new.add(new_context)

        self.store_new.commit()
