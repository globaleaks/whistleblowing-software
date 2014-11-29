# -*- encoding: utf-8 -*-

"""
  Changes

    Node table:
      - introduced default_language and default_timezone

    User table:
      - introduced language and timezone
"""

import copy
from storm.locals import Pickle, Int, Bool, Pickle, Unicode, DateTime

from globaleaks import LANGUAGES_SUPPORTED_CODES
from globaleaks.models import Model
from globaleaks.db.base_updater import TableReplacer

class Node_version_14(Model):
    __storm_table__ = 'node'
    name = Unicode()
    public_site = Unicode()
    hidden_service = Unicode()
    email = Unicode()
    receipt_salt = Unicode()
    last_update = DateTime()
    receipt_regexp = Unicode()
    languages_enabled = Pickle()
    description = Pickle()
    presentation = Pickle()
    footer = Pickle()
    subtitle = Pickle()
    terms_and_conditions = Pickle()
    security_awareness_title = Pickle()
    security_awareness_text = Pickle()
    stats_update_time = Int()
    maximum_namesize = Int()
    maximum_textsize = Int()
    maximum_filesize = Int()
    tor2web_admin = Bool()
    tor2web_submission = Bool()
    tor2web_receiver = Bool()
    tor2web_unauth = Bool()
    allow_unencrypted = Bool()
    x_frame_options_mode = Unicode()
    x_frame_options_allow_from = Unicode()
    postpone_superpower = Bool()
    can_delete_submission = Bool()
    ahmia = Bool()
    wizard_done = Bool()
    anomaly_checks = Bool()
    exception_email = Unicode()
    disable_privacy_badge = Bool()
    disable_security_awareness_badge = Bool()
    disable_security_awareness_questions = Bool()

class User_version_14(Model):
    __storm_table__ = 'user'
    username = Unicode()
    password = Unicode()
    salt = Unicode()
    role = Unicode()
    state = Unicode()
    last_login = DateTime()


class Replacer1415(TableReplacer):

    def migrate_Node(self):
        print "%s Node migration assistant: added default_language and default_timezone" % self.std_fancy

        old_node = self.store_old.find(self.get_right_model("Node", 14)).one()
        new_node = self.get_right_model("Node", 15)()

        for k, v in new_node._storm_columns.iteritems():

            if v.name == 'default_timezone':
                new_node.default_timezone= 0;
                continue

            if v.name == 'default_language':
                new_node.default_language = u'en';
                continue

            setattr(new_node, v.name, getattr(old_node, v.name))

        self.store_new.add(new_node)
        self.store_new.commit()

    def migrate_User(self):
        print "%s User migration assistant: (language, timezone)" % self.std_fancy

        old_users = self.store_old.find(self.get_right_model("User", 14))

        for old_user in old_users:

            new_user = self.get_right_model("User", 15)()

            for k, v in new_user._storm_columns.iteritems():

                if v.name == 'language':
                    new_user.language = u'en'
                    continue

                if v.name == 'timezone':
                    new_user.timezone = 0
                    continue

                setattr(new_user, v.name, getattr(old_user, v.name))

            self.store_new.add(new_user)

        self.store_new.commit()
