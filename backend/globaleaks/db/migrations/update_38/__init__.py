# -*- coding: UTF-8
from storm.locals import Int, Bool, Unicode, JSON

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import *


class Field_v_37(ModelWithID):
    __storm_table__ = 'field'
    x = Int(default=0)
    y = Int(default=0)
    width = Int(default=0)
    key = Unicode(default=u'')
    label = JSON(validator=longlocal_v)
    description = JSON(validator=longlocal_v)
    hint = JSON(validator=longlocal_v)
    required = Bool(default=False)
    preview = Bool(default=False)
    multi_entry = Bool(default=False)
    multi_entry_hint = JSON(validator=shortlocal_v)
    stats_enabled = Bool(default=False)
    triggered_by_score = Int(default=0)
    fieldgroup_id = Unicode()
    step_id = Unicode()
    template_id = Unicode()
    type = Unicode(default=u'inputbox')
    instance = Unicode(default=u'instance')
    editable = Bool(default=True)


class Questionnaire_v_37(ModelWithID):
    __storm_table__ = 'questionnaire'
    key = Unicode(default=u'')
    name = Unicode()
    show_steps_navigation_bar = Bool(default=False)
    steps_navigation_requires_completion = Bool(default=False)
    enable_whistleblower_identity = Bool(default=False)
    editable = Bool(default=True)


class MigrationScript(MigrationBase):
    def migrate_Context(self):
        questionnaire_default = self.store_old.find(self.model_from['Questionnaire'], self.model_from['Questionnaire'].key == u'default').one()
        questionnaire_default_id = questionnaire_default.id if questionnaire_default is not None else 'hack'

        old_objs = self.store_old.find(self.model_from['Context'])
        for old_obj in old_objs:
            new_obj = self.model_to['Context']()
            for _, v in new_obj._storm_columns.iteritems():
                setattr(new_obj, v.name, getattr(old_obj, v.name))

            if old_obj.questionnaire_id == questionnaire_default_id:
                setattr(new_obj, 'questionnaire_id', questionnaire_default_id)

            self.store_new.add(new_obj)

    def migrate_Field(self):
        field_wbi = self.store_old.find(self.model_from['Field'], self.model_from['Field'].key == u'whistleblower_identity').one()
        field_wbi_id = field_wbi.id if field_wbi is not None else 'hack'

        old_objs = self.store_old.find(self.model_from['Field'])
        for old_obj in old_objs:
            new_obj = self.model_to['Field']()
            for _, v in new_obj._storm_columns.iteritems():
                setattr(new_obj, v.name, getattr(old_obj, v.name))

            if old_obj.key == 'whistleblower_identity':
                setattr(new_obj, 'id', 'whistleblower_identity')

            if old_obj.fieldgroup_id == field_wbi_id:
                setattr(new_obj, 'fieldgroup_id', 'whistleblower_identity')

            if old_obj.template_id == field_wbi_id:
                setattr(new_obj, 'template_id', 'whistleblower_identity')

            self.store_new.add(new_obj)

    def migrate_Questionnaire(self):
        old_objs = self.store_old.find(self.model_from['Questionnaire'])
        for old_obj in old_objs:
            new_obj = self.model_to['Questionnaire']()
            for _, v in new_obj._storm_columns.iteritems():
                setattr(new_obj, v.name, getattr(old_obj, v.name))

            if old_obj.key == 'default':
                setattr(new_obj, 'id', 'default')

            self.store_new.add(new_obj)
