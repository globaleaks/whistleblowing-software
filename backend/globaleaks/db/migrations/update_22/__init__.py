# -*- encoding: utf-8 -*-

from storm.locals import Int, Bool, Unicode, DateTime, JSON

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import ModelWithID


class Context_v_21(ModelWithID):
    __storm_table__ = 'context'
    show_small_cards = Bool()
    show_receivers = Bool()
    maximum_selectable_receivers = Int()
    select_all_receivers = Bool()
    enable_comments = Bool()
    enable_private_messages = Bool()
    tip_timetolive = Int()
    last_update = DateTime()
    name = JSON()
    description = JSON()
    receiver_introduction = JSON()
    can_postpone_expiration = Bool()
    can_delete_submission = Bool()
    show_receivers_in_alphabetical_order = Bool()
    presentation_order = Int()


class InternalTip_v_21(ModelWithID):
    __storm_table__ = 'internaltip'
    creation_date = DateTime()
    context_id = Unicode()
    wb_steps = JSON()
    preview = JSON()
    expiration_date = DateTime()
    last_activity = DateTime()
    new = Int()


class MigrationScript(MigrationBase):
    def migrate_InternalTip(self):
        old_objs = self.store_old.find(self.model_from['InternalTip'])
        for old_obj in old_objs:
            new_obj = self.model_to['InternalTip']()
            for _, v in new_obj._storm_columns.items():
                if v.name == 'tor2web':
                    new_obj.tor2web = False
                    continue

                if v.name == 'progressive':
                    new_obj.progressive = 0
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)
