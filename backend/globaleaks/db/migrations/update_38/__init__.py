# -*- coding: utf-8
from globaleaks import models
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models.properties import *


old_keys = ["%NodeName%", "%HiddenService%", "%PublicSite%", "%ContextName%", "%RecipientName%", "%TipID%", "%TipNum%", "%TipLabel%", "%EventTime%", "%SubmissionDate%", "%ExpirationDate%", "%ExpirationWatch%", "%QuestionnaireAnswers%", "%Comments%", "%Messages%", "%TorURL%", "%T2WURL%", "%FileName%", "%FileSize%", "%Content%", "%ExpiringSubmissionCount%", "%EarliestExpirationDate%", "%PGPKeyInfoList%", "%PGPKeyInfo%", "%AnomalyDetailDisk%", "%AnomalyDetailActivities%", "%ActivityAlarmLevel%", "%ActivityDump%", "%NodeName%", "%FreeMemory%", "%TotalMemory%", "%ExpirationDate%", "%TipTorURL", "TipT2WURL"]


new_keys = ["{NodeName}", "{HiddenService}", "{PublicSite}", "{ContextName}", "{RecipientName}", "{TipID}", "{TipNum}", "{TipLabel}", "{EventTime}", "{SubmissionDate}", "{ExpirationDate}", "{ExpirationWatch}", "{QuestionnaireAnswers}", "{Comments}", "{Messages}", "{TorUrl}", "{HTTPSUrl}", "{FileName}", "{FileSize}", "{Content}", "{ExpiringSubmissionCount}", "{EarliestExpirationDate}", "{PGPKeyInfoList}", "{PGPKeyInfo}", "{AnomalyDetailDisk}", "{AnomalyDetailActivities}", "{ActivityAlarmLevel}", "{ActivityDump}", "{NodeName}", "{FreeMemory}", "{TotalMemory}", "{ExpirationDate}", "{TorUrl}", "{HTTPSUrl}"]


class Field_v_37(models.Model):
    __tablename__ = 'field'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    x = Column(Integer, default=0)
    y = Column(Integer, default=0)
    width = Column(Integer, default=0)
    key = Column(UnicodeText, default='')
    label = Column(JSON)
    description = Column(JSON)
    hint = Column(JSON)
    required = Column(Boolean, default=False)
    preview = Column(Boolean, default=False)
    multi_entry = Column(Boolean, default=False)
    multi_entry_hint = Column(JSON)
    triggered_by_score = Column(Integer, default=0)
    fieldgroup_id = Column(UnicodeText(36))
    step_id = Column(UnicodeText(36))
    template_id = Column(UnicodeText(36))
    type = Column(UnicodeText, default='inputbox')
    instance = Column(UnicodeText, default='instance')
    editable = Column(Boolean, default=True)


class Questionnaire_v_37(models.Model):
    __tablename__ = 'questionnaire'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    key = Column(UnicodeText, default='')
    name = Column(UnicodeText, default='')
    show_steps_navigation_bar = Column(Boolean, default=False)
    steps_navigation_requires_completion = Column(Boolean, default=False)
    enable_whistleblower_identity = Column(Boolean, default=False)
    editable = Column(Boolean, default=True)


def replace_templates_variables(value):
    for elem in enumerate(old_keys):
        value = value.replace(elem[1], new_keys[elem[0]])

    return value


class MigrationScript(MigrationBase):
    def migrate_ConfigL10N(self):
        for old_obj in self.session_old.query(self.model_from['ConfigL10N']):
            new_obj = self.model_to['ConfigL10N']()
            for key in new_obj.__mapper__.column_attrs.keys():
                value = getattr(old_obj, key)
                if key == 'value':
                    value = replace_templates_variables(value)

                setattr(new_obj, key, value)

            self.session_new.add(new_obj)

    def migrate_Context(self):
        questionnaire_default = self.session_old.query(self.model_from['Questionnaire']).filter(self.model_from['Questionnaire'].key == 'default').one_or_none()
        questionnaire_default_id = questionnaire_default.id if questionnaire_default is not None else 'hack'

        for old_obj in self.session_old.query(self.model_from['Context']):
            new_obj = self.model_to['Context']()
            for key in new_obj.__mapper__.column_attrs.keys():
                if key == 'questionnaire_id':
                    if old_obj.questionnaire_id is None or old_obj.questionnaire_id == questionnaire_default_id:
                        setattr(new_obj, 'questionnaire_id', 'default')
                        continue

                setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def migrate_Field(self):
        field_wbi = self.session_old.query(self.model_from['Field']).filter(self.model_from['Field'].key == 'whistleblower_identity').one()
        field_wbi_id = field_wbi.id if field_wbi is not None else 'hack'

        for old_obj in self.session_old.query(self.model_from['Field']):
            new_obj = self.model_to['Field']()
            for key in new_obj.__mapper__.column_attrs.keys():
                setattr(new_obj, key, getattr(old_obj, key))

            if old_obj.key == 'whistleblower_identity':
                setattr(new_obj, 'id', 'whistleblower_identity')

            if old_obj.fieldgroup_id == field_wbi_id:
                setattr(new_obj, 'fieldgroup_id', 'whistleblower_identity')

            if old_obj.template_id == field_wbi_id:
                setattr(new_obj, 'template_id', 'whistleblower_identity')

            self.session_new.add(new_obj)

    def migrate_Questionnaire(self):
        for old_obj in self.session_old.query(self.model_from['Questionnaire']):
            new_obj = self.model_to['Questionnaire']()
            for key in new_obj.__mapper__.column_attrs.keys():
                if old_obj.key == 'default':
                    setattr(new_obj, 'id', 'default')
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)
