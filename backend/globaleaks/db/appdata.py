# -*- coding: utf-8
# datainit.py: database initialization
#   ******************
import os
from storm.expr import And, Not, In

from globaleaks import models
from globaleaks.handlers.admin.field import db_create_field
from globaleaks.handlers.admin.step import db_create_step
from globaleaks.orm import transact
from globaleaks.settings import Settings
from globaleaks.utils.utility import log, read_json_file


def load_appdata():
    return read_json_file(Settings.appdata_file)


def load_default_questionnaires(store, tid):
    qfiles = [os.path.join(Settings.questionnaires_path, path) for path in os.listdir(Settings.questionnaires_path)]
    for qfile in qfiles:
        questionnaire = read_json_file(qfile)
        questionnaire['tid'] = tid

        steps = questionnaire.pop('steps')

        q = store.find(models.Questionnaire, tid=tid, id=questionnaire['id']).one()
        if q is None:
            q = models.db_forge_obj(store, models.Questionnaire, questionnaire)
        else:
            store.find(models.Step, tid=tid, questionnaire_id=q.id).remove()

        for step in steps:
            step['tid'] = tid
            step['questionnaire_id'] = q.id
            db_create_step(store, tid, step, None)

def load_default_fields(store, tid):
    ffiles = [os.path.join(Settings.questions_path, path) for path in os.listdir(Settings.questions_path)]
    for ffile in ffiles:
        question = read_json_file(ffile)
        question['tid'] = tid
        store.find(models.Field, tid=tid, id=question['id']).remove()
        db_create_field(store, tid, question, None)


def db_fix_fields_attrs(store):
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
            res = store.find(models.FieldAttr, Not(In(models.FieldAttr.name, attrs_to_keep_for_type)),
                                               models.FieldAttr.field_id == models.Field.id,
                                               models.Field.type == field_type,
                                               Not(In(models.Field.id, special_lst)))
        else:
            # Look for dropped attrs in non-standard field_groups like whistleblower_identity
            res = store.find(models.FieldAttr, Not(In(models.FieldAttr.name, attrs_to_keep_for_type)),
                                               models.FieldAttr.field_id == models.Field.id,
                                               models.Field.id == field_type)

        count = res.count()
        if count:
            log.debug("Removing %d attributes from fields of type %s", count, field_type)
            for r in res:
                store.remove(r)

    # Add keys to the db that have been added to field_attrs
    for field in store.find(models.Field):
        typ = field.type if field.id not in special_lst else field.id
        attrs = field_attrs.get(typ, {})
        for attr_name, attr_dict in attrs.items():
            if not store.find(models.FieldAttr,
                              And(models.FieldAttr.field_id == field.id,
                                  models.FieldAttr.name == attr_name)).one():
                log.debug("Adding new field attr %s.%s", typ, attr_name)
                attr_dict['tid'] = field.tid
                attr_dict['name'] = attr_name
                attr_dict['field_id'] = field.id
                models.db_forge_obj(store, models.FieldAttr, attr_dict)


def db_update_defaults(store, tid):
    load_default_questionnaires(store, tid)
    load_default_fields(store, tid)
