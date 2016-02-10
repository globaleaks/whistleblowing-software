# -*- encoding: utf-8 -*-
import os
import shutil

from storm.locals import Int, Bool, Unicode, DateTime, JSON

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import Model, BaseModel
from globaleaks.settings import GLSettings


class Field_v_27(Model):
    __storm_table__ = 'field'
    x = Int()
    y = Int()
    width = Int()
    key = Unicode()
    label = JSON()
    description = JSON()
    hint = JSON()
    required = Bool()
    preview = Bool()
    multi_entry = Bool()
    multi_entry_hint = JSON()
    stats_enabled = Bool()
    activated_by_score = Int()
    template_id = Unicode()
    type = Unicode()
    instance = Unicode()
    editable = Bool()


class Step_v_27(Model):
    __storm_table__ = 'step'
    context_id = Unicode()
    label = JSON()
    description = JSON()
    presentation_order = Int()


class FieldOption_v_27(Model):
    __storm_table__ = 'fieldoption'
    field_id = Unicode()
    presentation_order = Int()
    label = JSON()
    score_points = Int()


class FieldField_v_27(BaseModel):
    __storm_table__ = 'field_field'
    __storm_primary__ = 'parent_id', 'child_id'

    parent_id = Unicode()
    child_id = Unicode()


class StepField_v_27(BaseModel):
    __storm_table__ = 'step_field'
    __storm_primary__ = 'step_id', 'field_id'

    step_id = Unicode()
    field_id = Unicode()


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

    def migrate_Step(self):
        old_objs = self.store_old.find(self.model_from['Step'])
        for old_obj in old_objs:
            new_obj = self.model_to['Step']()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'triggered_by_score':
                    new_obj.triggered_by_score = 0
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

    def migrate_Field(self):
        old_objs = self.store_old.find(self.model_from['Field'])
        for old_obj in old_objs:
            new_obj = self.model_to['Field']()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'step_id':
                    sf = self.store_old.find(self.model_from['StepField'], self.model_from['StepField'].field_id == old_obj.id).one()
                    if sf is not None:
                        new_obj.step_id = sf.step_id
                    continue

                if v.name == 'fieldgroup_id':
                    ff = self.store_old.find(self.model_from['FieldField'], self.model_from['FieldField'].child_id == old_obj.id).one()
                    if ff is not None:
                        new_obj.fieldgroup_id = ff.parent_id
                    continue

                if v.name == 'triggered_by_score':
                    new_obj.triggered_by_score = 0
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

    def migrate_FieldOption(self):
        old_objs = self.store_old.find(self.model_from['FieldOption'])
        for old_obj in old_objs:
            new_obj = self.model_to['FieldOption']()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'option_id':
                    continue

                if v.name == 'trigger_field':
                    continue

                if v.name == 'trigger_step':
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)
