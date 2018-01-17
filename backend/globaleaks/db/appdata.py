# -*- coding: utf-8
# datainit.py: database initialization
#   ******************
import os
from sqlalchemy import not_

from globaleaks import models
from globaleaks.handlers.admin.field import db_create_field
from globaleaks.handlers.admin.step import db_create_step
from globaleaks.orm import transact
from globaleaks.settings import Settings
from globaleaks.utils.utility import log, read_json_file


def load_appdata():
    return read_json_file(Settings.appdata_file)


def load_default_questionnaires(session, tid):
    qfiles = [os.path.join(Settings.questionnaires_path, path) for path in os.listdir(Settings.questionnaires_path)]
    for qfile in qfiles:
        questionnaire = read_json_file(qfile)
        questionnaire['tid'] = tid

        steps = questionnaire.pop('steps')

        q = session.query(models.Questionnaire).filter(models.Questionnaire.tid == tid, models.Questionnaire.id == questionnaire['id']).one_or_none()
        if q is None:
            q = models.db_forge_obj(session, models.Questionnaire, questionnaire)
        else:
            session.query(models.Step).filter(models.Step.tid == tid, models.Step.questionnaire_id == q.id).delete(synchronize_session='fetch')

        for step in steps:
            step['tid'] = tid
            step['questionnaire_id'] = q.id
            db_create_step(session, tid, step, None)

def load_default_fields(session, tid):
    ffiles = [os.path.join(Settings.questions_path, path) for path in os.listdir(Settings.questions_path)]
    for ffile in ffiles:
        question = read_json_file(ffile)
        question['tid'] = tid
        session.query(models.Field).filter(models.Field.tid == tid, models.Field.id == question['id']).delete(synchronize_session='fetch')
        db_create_field(session, tid, question, None)


def db_fix_fields_attrs(session):
    """
    Ensures that the current store and the field_attrs.json file correspond.
    The content of the field_attrs dict is used to add and remove all of the
    excepted forms of field_attrs for FieldAttrs in the db.
    """
    field_attrs = read_json_file(Settings.field_attrs_file)

    special_lst = ['whistleblower_identity']

    std_lst = ['inputbox', 'textarea', 'multichoice', 'checkbox', 'tos', 'date']

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
        typ = field.type if field.id not in special_lst else field.id
        attrs = field_attrs.get(typ, {})
        for attr_name, attr_dict in attrs.items():
            x = session.query(models.FieldAttr) \
                     .filter(models.FieldAttr.field_id == field.id,
                             models.FieldAttr.name == attr_name).one_or_none()
            if x is None:

                log.debug("Adding new field attr %s.%s", typ, attr_name)
                attr_dict['tid'] = field.tid
                attr_dict['name'] = attr_name
                attr_dict['field_id'] = field.id
                models.db_forge_obj(session, models.FieldAttr, attr_dict)


def db_update_defaults(session, tid):
    load_default_questionnaires(session, tid)
    load_default_fields(session, tid)
    db_fix_fields_attrs(session)
