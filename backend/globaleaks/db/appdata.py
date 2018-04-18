# -*- coding: utf-8
# datainit.py: database initialization
#   ******************
import os
from sqlalchemy import not_

from globaleaks import models
from globaleaks.handlers.admin.field import db_create_field, db_add_field_attrs
from globaleaks.handlers.admin.questionnaire import db_create_questionnaire
from globaleaks.orm import transact
from globaleaks.settings import Settings
from globaleaks.state import State
from globaleaks.utils.utility import log, read_json_file


def load_appdata():
    return read_json_file(Settings.appdata_file)


def load_default_questionnaires(session):
    qfiles = [os.path.join(Settings.questionnaires_path, path) for path in os.listdir(Settings.questionnaires_path)]
    questionnaires = []
    qids = []

    for qfile in qfiles:
        questionnaires.append(read_json_file(qfile))
        qids.append(questionnaires[-1]['id'])

    session.query(models.Questionnaire).filter(models.Questionnaire.id.in_(qids)).delete(synchronize_session='fetch')
    session.query(models.Step).filter(models.Step.questionnaire_id.in_(qids)).delete(synchronize_session='fetch')

    for questionnaire in questionnaires:
        db_create_questionnaire(session, State, 1, questionnaire, None)


def load_default_fields(session):
    ffiles = [os.path.join(Settings.questions_path, path) for path in os.listdir(Settings.questions_path)]
    questions = []
    qids = []

    for ffile in ffiles:
        questions.append(read_json_file(ffile))
        qids.append(questions[-1]['id'])

    session.query(models.Field).filter(models.Field.id.in_(qids)).delete(synchronize_session='fetch')
    session.query(models.Field).filter(models.Field.fieldgroup_id.in_(qids)).delete(synchronize_session='fetch')
    session.query(models.FieldAttr).filter(models.FieldAttr.field_id.in_(qids)).delete(synchronize_session='fetch')
    session.query(models.FieldOption).filter(models.FieldOption.field_id.in_(qids)).delete(synchronize_session='fetch')

    for question in questions:
        db_create_field(session, 1, question, None)


def db_fix_fields_attrs(session):
    """
    Ensures that the current store and the field_attrs.json file correspond.
    The content of the field_attrs dict is used to add and remove all of the
    excepted forms of field_attrs for FieldAttrs in the db.
    """
    field_attrs = read_json_file(Settings.field_attrs_file)

    std_lst = [u'inputbox', u'textarea', u'multichoice', u'checkbox', u'tos', u'date']

    for field_type, attrs_dict in field_attrs.items():
        attrs_to_keep_for_type = attrs_dict.keys()
        if field_type in std_lst:
            # Ensure that the standard field attrs do not have extra attr rows
            _filter = not_(models.FieldAttr.name.in_(attrs_to_keep_for_type)), \
                      models.FieldAttr.field_id == models.Field.id, \
                      models.Field.type == field_type, \
                      models.Field.template_id == None
        else:
            # Look for dropped attrs in non-standard field_groups like whistleblower_identity
            _filter = not_(models.FieldAttr.name.in_(attrs_to_keep_for_type)), \
                      models.FieldAttr.field_id == models.Field.id, \
                      models.Field.template_id == field_type

        for res in session.query(models.FieldAttr).filter(*_filter):
            session.delete(res)

    # Add keys to the db that have been added to field_attrs
    for field in session.query(models.Field):
        type = field.type if field.template_id is None else field.template_id
        attrs = field_attrs.get(type, {})
        db_add_field_attrs(session, field.id, attrs)



def db_update_defaults(session):
    load_default_questionnaires(session)
    load_default_fields(session)
    db_fix_fields_attrs(session)
