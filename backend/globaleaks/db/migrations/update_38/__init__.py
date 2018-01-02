# -*- coding: utf-8
from storm.locals import Int, Bool, Unicode, JSON

from globaleaks import models
from globaleaks.db.migrations.update import MigrationBase


old_keys = ["%NodeName%", "%HiddenService%", "%PublicSite%", "%ContextName%", "%RecipientName%", "%TipID%", "%TipNum%", "%TipLabel%", "%EventTime%", "%SubmissionDate%", "%ExpirationDate%", "%ExpirationWatch%", "%QuestionnaireAnswers%", "%Comments%", "%Messages%", "%TorURL%", "%T2WURL%", "%FileName%", "%FileSize%", "%Content%", "%ExpiringSubmissionCount%", "%EarliestExpirationDate%", "%PGPKeyInfoList%", "%PGPKeyInfo%", "%AnomalyDetailDisk%", "%AnomalyDetailActivities%", "%ActivityAlarmLevel%", "%ActivityDump%", "%NodeName%", "%FreeMemory%", "%TotalMemory%", "%ExpirationDate%", "%TipTorURL", "TipT2WURL"]


new_keys = ["{NodeName}", "{HiddenService}", "{PublicSite}", "{ContextName}", "{RecipientName}", "{TipID}", "{TipNum}", "{TipLabel}", "{EventTime}", "{SubmissionDate}", "{ExpirationDate}", "{ExpirationWatch}", "{QuestionnaireAnswers}", "{Comments}", "{Messages}", "{TorUrl}", "{HTTPSUrl}", "{FileName}", "{FileSize}", "{Content}", "{ExpiringSubmissionCount}", "{EarliestExpirationDate}", "{PGPKeyInfoList}", "{PGPKeyInfo}", "{AnomalyDetailDisk}", "{AnomalyDetailActivities}", "{ActivityAlarmLevel}", "{ActivityDump}", "{NodeName}", "{FreeMemory}", "{TotalMemory}", "{ExpirationDate}", "{TorUrl}", "{HTTPSUrl}"]


class Field_v_37(models.ModelWithID):
    __storm_table__ = 'field'
    x = Int(default=0)
    y = Int(default=0)
    width = Int(default=0)
    key = Unicode(default=u'')
    label = JSON()
    description = JSON()
    hint = JSON()
    required = Bool(default=False)
    preview = Bool(default=False)
    multi_entry = Bool(default=False)
    multi_entry_hint = JSON()
    stats_enabled = Bool(default=False)
    triggered_by_score = Int(default=0)
    fieldgroup_id = Unicode()
    step_id = Unicode()
    template_id = Unicode()
    type = Unicode(default=u'inputbox')
    instance = Unicode(default=u'instance')
    editable = Bool(default=True)


class Questionnaire_v_37(models.ModelWithID):
    __storm_table__ = 'questionnaire'
    key = Unicode(default=u'')
    name = Unicode(default=u'')
    show_steps_navigation_bar = Bool(default=False)
    steps_navigation_requires_completion = Bool(default=False)
    enable_whistleblower_identity = Bool(default=False)
    editable = Bool(default=True)


def replace_templates_variables(value):
    for elem in enumerate(old_keys):
        value = value.replace(elem[1], new_keys[elem[0]])

    return value


class MigrationScript(MigrationBase):
    def migrate_ConfigL10N(self):
        old_objs = self.store_old.find(self.model_from['ConfigL10N'])
        for old_obj in old_objs:
            new_obj = self.model_to['ConfigL10N']()
            for _, v in new_obj._storm_columns.items():
                value = getattr(old_obj, v.name)
                if v.name == 'value':
                    value = replace_templates_variables(value)

                setattr(new_obj, v.name, value)

            self.store_new.add(new_obj)

    def migrate_Context(self):
        questionnaire_default = self.store_old.find(self.model_from['Questionnaire'], self.model_from['Questionnaire'].key == u'default').one()
        questionnaire_default_id = questionnaire_default.id if questionnaire_default is not None else 'hack'

        old_objs = self.store_old.find(self.model_from['Context'])
        for old_obj in old_objs:
            new_obj = self.model_to['Context']()
            for _, v in new_obj._storm_columns.items():
                if v.name == 'questionnaire_id':
                    if old_obj.questionnaire_id is None or old_obj.questionnaire_id == questionnaire_default_id:
                        setattr(new_obj, 'questionnaire_id', u'default')
                    else:
                        setattr(new_obj, v.name, getattr(old_obj, v.name))
                else:
                    setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

    def migrate_Field(self):
        field_wbi = self.store_old.find(self.model_from['Field'], self.model_from['Field'].key == u'whistleblower_identity').one()
        field_wbi_id = field_wbi.id if field_wbi is not None else 'hack'

        old_objs = self.store_old.find(self.model_from['Field'])
        for old_obj in old_objs:
            new_obj = self.model_to['Field']()
            for _, v in new_obj._storm_columns.items():
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
            for _, v in new_obj._storm_columns.items():
                setattr(new_obj, v.name, getattr(old_obj, v.name))

            if old_obj.key == 'default':
                setattr(new_obj, 'id', 'default')

            self.store_new.add(new_obj)
