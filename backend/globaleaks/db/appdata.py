# -*- coding: utf-8
import os
from sqlalchemy import not_

from globaleaks import models
from globaleaks.handlers.admin.field import db_create_field, db_update_fieldattrs
from globaleaks.handlers.admin.questionnaire import db_create_questionnaire
from globaleaks.settings import Settings
from globaleaks.utils.fs import read_json_file


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
    qids = []

    for qfile in qfiles:
        questionnaires.append(read_json_file(qfile))
        qids.append(questionnaires[-1]['id'])

    models.db_delete(session, models.Questionnaire, models.Questionnaire.id.in_(qids))
    models.db_delete(session, models.Step, models.Step.questionnaire_id.in_(qids))

    for questionnaire in questionnaires:
        db_create_questionnaire(session, 1, questionnaire, None)


def db_load_default_fields(session):
    """
    Transaction for loading default questions
    :param session: An ORM session
    """
    ffiles = [os.path.join(Settings.questions_path, path)
              for path in os.listdir(Settings.questions_path)]
    questions = []
    qids = []

    for ffile in ffiles:
        questions.append(read_json_file(ffile))
        qids.append(questions[-1]['id'])

    models.db_delete(session, models.Field, models.Field.id.in_(qids))
    models.db_delete(session, models.Field, models.Field.fieldgroup_id.in_(qids))
    models.db_delete(session, models.FieldAttr, models.FieldAttr.field_id.in_(qids))
    models.db_delete(session, models.FieldOption, models.FieldOption.field_id.in_(qids))

    for question in questions:
        db_create_field(session, 1, question, None)


def db_load_defaults(session):
    """
    Transaction for updating application defaults

    :param session: An ORM session
    """
    db_load_default_questionnaires(session)
    db_load_default_fields(session)


def db_fix_fields_attrs(session):
    """
    Ensures that questions loaded into the database have the same structure of field_attrs.json

    :param session: An ORM session
    """
    field_attrs = read_json_file(Settings.field_attrs_file)

    std_lst = ['inputbox', 'textarea', 'checkbox', 'selectbox', 'fieldgroup', 'tos', 'date', 'daterange', 'map']

    for field_type, attrs_dict in field_attrs.items():
        attrs_to_keep_for_type = attrs_dict.keys()
        if field_type in std_lst:
            # Ensure that the standard field attrs do not have extra attr rows
            _filter = not_(models.FieldAttr.name.in_(attrs_to_keep_for_type)), \
                      models.FieldAttr.field_id == models.Field.id, \
                      models.Field.type == field_type, \
                      models.Field.template_id.is_(None)
        else:
            # Look for dropped attrs in non-standard field_groups like whistleblower_identity
            _filter = not_(models.FieldAttr.name.in_(attrs_to_keep_for_type)), \
                      models.FieldAttr.field_id == models.Field.id, \
                      models.Field.template_id == field_type

        subquery = session.query(models.FieldAttr.id).filter(*_filter).subquery()

        models.db_delete(models.FieldAttr, models.FieldAttr.id.in_(subquery))

    # Add keys to the db that have been added to field_attrs
    for field in session.query(models.Field):
        type = field.type if field.template_id is None else field.template_id
        attrs = field_attrs.get(type, {})
        db_update_fieldattrs(session, field.id, attrs, None)
