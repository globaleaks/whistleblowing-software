# -*- encoding: utf-8 -*-

"""
  Changes

    Node table:
      - introduced default_language and default_timezone

    User table:
      - introduced language and timezone

    Context table:
      - fields refactored entirely adding Field and Step table;
      - all data is migrated.

    InternalTip table:
      - changed from wb_fields to wb_steps; all data is migrated.
"""

import copy
from storm.locals import Pickle, Int, Bool, Unicode, DateTime, JSON, ReferenceSet

from globaleaks import LANGUAGES_SUPPORTED_CODES
from globaleaks.db.base_updater import TableReplacer
from globaleaks.db.datainit import opportunistic_appdata_init
from globaleaks.models import Model, Field, FieldOption, Step, db_forge_obj
from globaleaks.utils.utility import datetime_null, uuid4

class Context_version_15(Model):
    __storm_table__ = 'context'
    selectable_receiver = Bool()
    show_small_cards = Bool()
    show_receivers = Bool()
    maximum_selectable_receivers = Int()
    select_all_receivers = Bool()
    tip_max_access = Int()
    file_max_download = Int()
    tip_timetolive = Int()
    submission_timetolive = Int()
    last_update = DateTime()
    name = JSON()
    description = JSON()
    receiver_introduction = JSON()
    postpone_superpower = Bool()
    can_delete_submission = Bool()
    show_small_cards = Bool()
    show_receivers = Bool()
    enable_private_messages = Bool()
    presentation_order = Int()

# this has never been performed during old migration script and will need
# to be done in situations like the one generated in this particular migration
Context_version_15.steps = ReferenceSet(Context_version_15.id,
                                        Step.context_id)


class Receiver_version_15(Model):
    __storm_table__ = 'receiver'
    user_id = Unicode()
    name = Unicode()
    description = JSON()
    configuration = Unicode()
    gpg_key_info = Unicode()
    gpg_key_fingerprint = Unicode()
    gpg_key_status = Unicode()
    gpg_key_armor = Unicode()
    gpg_enable_notification = Bool()
    mail_address = Unicode()
    can_delete_submission = Bool()
    postpone_superpower = Bool()
    last_update = DateTime()
    tip_notification = Bool()
    comment_notification = Bool()
    file_notification = Bool()
    message_notification = Bool()


class Replacer1516(TableReplacer):

    def migrate_Context(self):
        print "%s Context migration assistant" % self.std_fancy

        old_contexts = self.store_old.find(self.get_right_model("Context", 15))

        for old_context in old_contexts:

            new_context = self.get_right_model("Context", 16)()

            for _, v in new_context._storm_columns.iteritems():
                setattr(new_context, v.name, getattr(old_context, v.name))

            self.store_new.add(new_context)

        self.store_new.commit()

    def migrate_Receiver(self):
        print "%s Receiver migration assistant" % self.std_fancy

        old_receivers = self.store_old.find(self.get_right_model("Receiver", 15))

        for old_receiver in old_receivers:

            new_receiver = self.get_right_model("Receiver", 15)()

            for _, v in new_receiver._storm_columns.iteritems():

                if v.name == 'configuration':
                    if old_receiver.configuration == 'hidden':
                        new_receiver.configuration == 'forcefully_selected'
                    else:
                        new_receiver.configuration = old_receiver.configuration
                    continue

                if v.name == 'ping_mail_address':
                    new_receiver.ping_mail_address = ''
                    continue

                if v.name == 'presentation_order':
                    if old_receiver.presentation_order == 0:
                        new_receiver.presentation_order = 1
                    continue

                setattr(new_receiver, v.name, getattr(old_receiver, v.name))

            self.store_new.add(new_receiver)

        self.store_new.commit()

    def migrate_Field(self):
        print "%s Field migration assistant" % self.std_fancy

        old_fields = self.store_old.find(self.get_right_model("Field", 15))

        for old_field in old_fields:

            new_field = self.get_right_model("Field", 16)()

            for _, v in new_field._storm_columns.iteritems():
                if v.name == 'is_template':
                    if old_field.is_template is None:
                        new_field.is_template = False
                    else:
                        new_field.is_template = old_field.is_template
                    continue

                setattr(new_field, v.name, getattr(old_field, v.name))

            self.store_new.add(new_field)

        self.store_new.commit()

