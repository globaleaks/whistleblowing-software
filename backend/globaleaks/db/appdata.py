# -*- coding: utf-8
# datainit.py: database initialization
#   ******************
import os
from sqlalchemy import not_

from globaleaks import models
from globaleaks.handlers.admin.field import db_create_field, db_add_field_attrs
from globaleaks.handlers.admin.step import db_create_step
from globaleaks.orm import transact
from globaleaks.settings import Settings
from globaleaks.utils.utility import log, read_json_file


def load_appdata():
    return read_json_file(Settings.appdata_file)


def load_default_questionnaires(session):
    qfiles = [os.path.join(Settings.questionnaires_path, path) for path in os.listdir(Settings.questionnaires_path)]
    for qfile in qfiles:
        questionnaire = read_json_file(qfile)

        steps = questionnaire.pop('steps')

        q = session.query(models.Questionnaire).filter(models.Questionnaire.id == questionnaire['id']).one_or_none()
        if q is None:
            q = models.db_forge_obj(session, models.Questionnaire, questionnaire)
        else:
            session.query(models.Step).filter(models.Step.questionnaire_id == q.id).delete(synchronize_session='fetch')

        for step in steps:
            step['questionnaire_id'] = q.id
            db_create_step(session, 1, step, None)

def load_default_fields(session):
    ffiles = [os.path.join(Settings.questions_path, path) for path in os.listdir(Settings.questions_path)]
    for ffile in ffiles:
        question = read_json_file(ffile)
        question['tid'] = 1
        session.query(models.Field).filter(models.Field.id == question['id']).delete(synchronize_session='fetch')
        db_create_field(session, 1, question, None)


def db_fix_fields_attrs(session):
    """
    Ensures that the current store and the field_attrs.json file correspond.
    The content of the field_attrs dict is used to add and remove all of the
    excepted forms of field_attrs for FieldAttrs in the db.
    """
    field_attrs = read_json_file(Settings.field_attrs_file)

    special_lst = [u'whistleblower_identity']

    std_lst = [u'inputbox', u'textarea', u'multichoice', u'checkbox', u'tos', u'date']

    for field_type, attrs_dict in field_attrs.items():
        attrs_to_keep_for_type = attrs_dict.keys()
        if field_type in std_lst:
            # Ensure that the standard field attrs do not have extra attr rows
            res = session.query(models.FieldAttr).filter(not_(models.FieldAttr.name.in_(attrs_to_keep_for_type)),
                                                       models.FieldAttr.field_id == models.Field.id,
                                                       models.Field.type == field_type,
                                                       not_(models.Field.id.in_(special_lst)))
        else:
            # Look for dropped attrs in non-standard field_groups like whistleblower_identity
            res = session.query(models.FieldAttr).filter(not_(models.FieldAttr.name.in_(attrs_to_keep_for_type)),
                                                       models.FieldAttr.field_id == models.Field.id,
                                                       models.Field.id == field_type)

        for r in res:
            session.delete(r)

    # Add keys to the db that have been added to field_attrs
    for field in session.query(models.Field):
        type = field.type if field.template_id not in special_lst else field.template_id
        attrs = field_attrs.get(type, {})
        db_add_field_attrs(session, field.id, attrs)



def db_update_defaults(session):
    load_default_questionnaires(session)
    load_default_fields(session)
    db_fix_fields_attrs(session)
