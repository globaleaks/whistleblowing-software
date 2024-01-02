# -*- coding: utf-8
import os
from sqlalchemy import not_

from globaleaks import models
from globaleaks.handlers.admin.field import db_create_field, db_update_fieldattrs
from globaleaks.handlers.admin.questionnaire import db_create_questionnaire
from globaleaks.orm import db_del
from globaleaks.settings import Settings
from globaleaks.utils.fs import read_json_file


def extract_ids(obj, ret=[]):
    """
    Utility function to extract ids from questionnaires
    and questions data structures.
    """
    if obj.get('id', None):
        ret.append(obj['id'])

    for c in obj['children']:
        ret = extract_ids(c, ret)

    return ret


def load_appdata():
    """
    Utility function to load the application data file

    :return: Return the parsed application data file
    """
    return read_json_file(Settings.appdata_file)


def db_load_default_questionnaires(session):
    """
    Transaction for loading default questionnaires
    :param session: An ORM session
    """
    qfiles = [os.path.join(Settings.questionnaires_path, path)
              for path in os.listdir(Settings.questionnaires_path)]
    questionnaires = []
    ids = []

    for qfile in qfiles:
        questionnaires.append(read_json_file(qfile))
        ids.append(questionnaires[-1]['id'])

        for s in questionnaires[-1]['steps']:
            extract_ids(s, ids)

    db_del(session, models.Questionnaire, models.Questionnaire.id.in_(ids))
    db_del(session, models.Step, models.Step.questionnaire_id.in_(ids))
    db_del(session, models.Field, models.Field.id.in_(ids))
    db_del(session, models.FieldAttr, models.FieldAttr.field_id.in_(ids))
    db_del(session, models.FieldOption, models.FieldOption.field_id.in_(ids))
    db_del(session, models.FieldOptionTriggerField, models.FieldOptionTriggerField.object_id.in_(ids))
    db_del(session, models.FieldOptionTriggerStep, models.FieldOptionTriggerStep.object_id.in_(ids))

    for questionnaire in questionnaires:
        db_create_questionnaire(session, 1, None, questionnaire, None)


def db_load_default_fields(session):
    """
    Transaction for loading default questions
    :param session: An ORM session
    """
    ffiles = [os.path.join(Settings.questions_path, path)
              for path in os.listdir(Settings.questions_path)]
    questions = []
    ids = []

    for ffile in ffiles:
        questions.append(read_json_file(ffile))
        extract_ids(questions[-1], ids)

    db_del(session, models.Field, models.Field.id.in_(ids))
    db_del(session, models.Field, models.Field.fieldgroup_id.in_(ids))
    db_del(session, models.FieldAttr, models.FieldAttr.field_id.in_(ids))
    db_del(session, models.FieldOption, models.FieldOption.field_id.in_(ids))
    db_del(session, models.FieldOptionTriggerField, models.FieldOptionTriggerField.object_id.in_(ids))
    db_del(session, models.FieldOptionTriggerStep, models.FieldOptionTriggerStep.object_id.in_(ids))

    for question in questions:
        db_create_field(session, 1, question, None)


def db_fix_fields_attrs(session):
    """
    Ensures that questions loaded into the database have the same structure of field_attrs.json

    :param session: An ORM session
    """
    field_attrs = read_json_file(Settings.field_attrs_file)

    std_lst = ['inputbox', 'textarea', 'checkbox', 'selectbox', 'fieldgroup', 'tos', 'date', 'daterange']

    for field_type, attrs_dict in field_attrs.items():
        attrs_to_keep_for_type = attrs_dict.keys()
        if field_type in std_lst:
            # Ensure that the standard field attrs do not have extra attr rows
            _filter = not_(models.FieldAttr.name.in_(attrs_to_keep_for_type)), \
                      models.FieldAttr.field_id == models.Field.id, \
                      models.Field.type == field_type, \
                      models.Field.template_id.is_(None)

            for x in session.query(models.FieldAttr).filter(*_filter):
                session.delete(x)

    # Add keys to the db that have been added to field_attrs
    attrs_name = set([attr_name[0] for attr_name in session.query(models.FieldAttr.name)])

    for x in field_attrs:
        for y in attrs_name:
            field_attrs[x].pop(y, None)

    for field in session.query(models.Field):
        type = field.type if field.template_id is None else field.template_id
        attrs = field_attrs.get(type, {})
        db_update_fieldattrs(session, field.id, attrs, None)


def db_fix_orphans_models(session):
    """
    Transaction for deleting orpans models related to old migrations run with disabled foreign keys checks

    :param session: An ORM session
    """
    steps_ids = session.query(models.Step.id)
    fields_ids = session.query(models.Field.id)
    session.query(models.Field).filter(models.Field.instance == 0, models.Field.step_id != None, not_(models.Field.step_id.in_(steps_ids))).delete(synchronize_session=False)
    session.query(models.Field).filter(models.Field.fieldgroup_id != None, not_(models.Field.fieldgroup_id.in_(fields_ids))).delete(synchronize_session=False)
    session.query(models.FieldOption).filter(not_(models.FieldOption.field_id.in_(fields_ids))).delete(synchronize_session=False)
    session.query(models.FieldAttr).filter(not_(models.FieldAttr.field_id.in_(fields_ids))).delete(synchronize_session=False)
    session.query(models.FieldOptionTriggerField).filter(not_(models.FieldOptionTriggerField.object_id.in_(fields_ids))).delete(synchronize_session=False)
    session.query(models.FieldOptionTriggerStep).filter(not_(models.FieldOptionTriggerStep.object_id.in_(steps_ids))).delete(synchronize_session=False)


def db_load_defaults(session):
    """
    Transaction for updating application defaults

    :param session: An ORM session
    """
    db_load_default_questionnaires(session)
    db_load_default_fields(session)
    db_fix_fields_attrs(session)
    db_fix_orphans_models(session)
