# -*- coding: utf-8 -*-
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import Model
from globaleaks.models.properties import *


class Field_v_27(Model):
    __tablename__ = 'field'
    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)
    x = Column(Integer)
    y = Column(Integer)
    width = Column(Integer)
    key = Column(UnicodeText)
    label = Column(JSON)
    description = Column(JSON)
    hint = Column(JSON)
    required = Column(Boolean)
    preview = Column(Boolean)
    multi_entry = Column(Boolean)
    multi_entry_hint = Column(JSON)
    stats_enabled = Column(Boolean)
    activated_by_score = Column(Integer)
    template_id = Column(Unicode(36))
    type = Column(UnicodeText)
    instance = Column(UnicodeText)
    editable = Column(Boolean)


class Step_v_27(Model):
    __tablename__ = 'step'
    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)
    context_id = Column(Unicode(36))
    label = Column(JSON)
    description = Column(JSON)
    presentation_order = Column(Integer)


class FieldOption_v_27(Model):
    __tablename__ = 'fieldoption'
    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)
    field_id = Column(Unicode(36))
    presentation_order = Column(Integer)
    label = Column(JSON)
    score_points = Column(Integer)


class FieldField_v_27(Model):
    __tablename__ = 'field_field'

    parent_id = Column(Unicode(36), primary_key=True)
    child_id = Column(Unicode(36), primary_key=True)


class StepField_v_27(Model):
    __tablename__ = 'step_field'

    step_id = Column(Unicode(36), primary_key=True)
    field_id = Column(Unicode(36), primary_key=True)


class MigrationScript(MigrationBase):
    def migrate_Step(self):
        old_objs = self.session_old.query(self.model_from['Step'])
        for old_obj in old_objs:
            new_obj = self.model_to['Step']()
            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'triggered_by_score':
                    new_obj.triggered_by_score = 0
                    continue

                setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def migrate_Field(self):
        old_objs = self.session_old.query(self.model_from['Field'])
        for old_obj in old_objs:
            new_obj = self.model_to['Field']()
            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'preview':
                    if old_obj.preview is None:
                        new_obj.preview = False
                    else:
                        new_obj.preview = old_obj.preview

                elif key == 'step_id':
                    sf = self.session_old.query(self.model_from['StepField']).filter(self.model_from['StepField'].field_id == old_obj.id).one_or_none()
                    if sf is not None:
                        new_obj.step_id = sf.step_id

                elif key == 'fieldgroup_id':
                    ff = self.session_old.query(self.model_from['FieldField']).filter(self.model_from['FieldField'].child_id == old_obj.id).one_or_none()
                    if ff is not None:
                        new_obj.fieldgroup_id = ff.parent_id

                elif key == 'triggered_by_score':
                    new_obj.triggered_by_score = 0

                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def migrate_FieldOption(self):
        old_objs = self.session_old.query(self.model_from['FieldOption'])
        for old_obj in old_objs:
            new_obj = self.model_to['FieldOption']()
            for key in [c.key for c in new_obj.__table__.columns]:
                if key != 'trigger_field':
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)
