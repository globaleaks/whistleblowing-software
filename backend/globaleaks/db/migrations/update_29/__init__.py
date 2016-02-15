# -*- encoding: utf-8 -*-
import os
import shutil

from storm.locals import Int, Bool, Unicode, DateTime, JSON

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import Model, BaseModel
from globaleaks.settings import GLSettings


class Context_v_28(Model):
    __storm_table__ = 'context'
    show_small_cards = Bool()
    show_context = Bool()
    show_recipients_details = Bool()
    allow_recipients_selection = Bool()
    maximum_selectable_receivers = Int()
    select_all_receivers = Bool()
    enable_comments = Bool()
    enable_messages = Bool()
    enable_two_way_comments = Bool()
    enable_two_way_messages = Bool()
    enable_attachments = Bool()
    enable_whistleblower_identity = Bool()
    tip_timetolive = Int()
    name = JSON()
    description = JSON()
    recipients_clarification = JSON()
    questionnaire_layout = Unicode()
    show_receivers_in_alphabetical_order = Bool()
    presentation_order = Int()


class MigrationScript(MigrationBase):
    def migrate_Notification(self):
        # an other time fix templates by reloading updated translations
        old_notification = self.store_old.find(self.model_from['Notification']).one()
        new_notification = self.model_to['Notification']()

        for _, v in new_notification._storm_columns.iteritems():
            if self.update_model_with_new_templates(new_notification,
                                                    v.name,
                                                    self.appdata['templates'].keys(),
                                                    self.appdata['templates']):
                continue

        self.store_new.add(new_notification)

    def migrate_Context(self):
        old_objs = self.store_old.find(self.model_from['Context'])
        for old_obj in old_objs:
            new_obj = self.model_to['Context']()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'show_steps_navigation_bar':
                    new_obj.show_steps_navigation_bar = True
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)
