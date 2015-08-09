# -*- encoding: utf-8 -*-

from storm.locals import Int, Bool, Unicode, DateTime, JSON, Reference, ReferenceSet
from globaleaks.db.base_updater import TableReplacer
from globaleaks.models import BaseModel, Model


class Field_v_22(Model):
    __storm_table__ = 'field'
    label = JSON()
    description = JSON()
    hint = JSON()
    multi_entry = Bool()
    required = Bool()
    preview = Bool()
    stats_enabled = Bool()
    is_template = Bool()
    x = Int()
    y = Int()
    type = Unicode()


class InternalFile_v_22(Model):
    __storm_table__ = 'internalfile'
    internaltip_id = Unicode()
    name = Unicode()
    file_path = Unicode()
    content_type = Unicode()
    size = Int()
    new = Int()


class Comment_v_22(Model):
    __storm_table__ = 'comment'
    internaltip_id = Unicode()
    author = Unicode()
    content = Unicode()
    system_content = JSON()
    type = Unicode()
    new = Int(default=True)


class Context_v_22(Model):
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
    show_receivers_in_alphabetical_order = Bool()
    presentation_order = Int()


class Replacer2223(TableReplacer):
    def migrate_Field(self):
        print "%s Field migration assistant" % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("Field", 22))

        for old_obj in old_objs:
            new_obj = self.get_right_model("Field", 23)()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'min_len':
                    new_obj.min_len = -1
                    continue

                if v.name == 'max_len':
                    new_obj.max_len = -1
                    continue

                if v.name == 'regexp':
                    new_obj.regexp = u""
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()

    def migrate_InternalFile(self):
        print "%s InternalFile migration assistant" % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("InternalFile", 22))

        for old_obj in old_objs:
            new_obj = self.get_right_model("InternalFile", 23)()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'processing_attempts':
                    new_obj.processing_attempts = 0
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()

    def migrate_Comment(self):
        print "%s Comment migration assistant" % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("Comment", 22))

        for old_obj in old_objs:
            if old_obj.type == u'system':
                continue

            new_obj = self.get_right_model("Comment", 23)()
            for _, v in new_obj._storm_columns.iteritems():
                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

        self.store_new.commit()

    def migrate_Context(self):
        print "%s Context migration assistant" % self.std_fancy

        old_objs = self.store_old.find(self.get_right_model("Context", 22))

        for old_obj in old_objs:
            new_obj = self.get_right_model("Context", 23)()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'steps_arrangement':
                    new_obj.steps_arrangement = 'horizontal' if len(old_obj.steps) > 1 else 'vertical'
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)


        self.store_new.commit()
