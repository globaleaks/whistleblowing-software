# -*- coding: UTF-8
# datainit.py: database initialization
#   ******************
import os
from storm.expr import And, Not, In

from globaleaks import models
from globaleaks.handlers.admin.field import db_create_field, db_import_fields
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import log, read_json_file


def load_appdata():
    return read_json_file(GLSettings.appdata_file)


def load_default_questionnaires(store):
    qfiles = [os.path.join(GLSettings.questionnaires_path, path) for path in os.listdir(GLSettings.questionnaires_path)]
    for qfile in qfiles:
        questionnaire = read_json_file(qfile)
        steps = questionnaire['steps']
        del questionnaire['steps']

        q = store.find(models.Questionnaire, models.Questionnaire.id == questionnaire['id']).one()
        if q is None:
            q = models.db_forge_obj(store, models.Questionnaire, questionnaire)
        else:
            for step in q.steps:
                store.remove(step)

        for step in steps:
            f_children = step['children']
            del step['children']
            s = models.db_forge_obj(store, models.Step, step)
            s.questionnaire_id = q.id
            db_import_fields(store, s, None, f_children)



def load_default_fields(store):
    ffiles = [os.path.join(GLSettings.questions_path, path) for path in os.listdir(GLSettings.questions_path)]
    for ffile in ffiles:
        question = read_json_file(ffile)
        store.find(models.Field, models.Field.id == question['id']).remove()
        db_create_field(store, question, None)


def db_update_defaults(store):
    load_default_questionnaires(store)
    load_default_fields(store)


def db_fix_fields_attrs(store):
    """
    Ensures that the current store and the field_attrs.json file correspond.
    The content of the field_attrs dict is used to add and remove all of the
    excepted forms of field_attrs for FieldAttrs in the db.
    """
    field_attrs = read_json_file(GLSettings.field_attrs_file)

    special_lst = ['whistleblower_identity']

    std_lst = ['inputbox', 'textarea', 'multichoice', 'checkbox', 'tos', 'date']

    for field_type, attrs_dict in field_attrs.iteritems():
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
        for attr_name, attr_dict in attrs.iteritems():
            if not store.find(models.FieldAttr,
                              And(models.FieldAttr.field_id == field.id,
                                  models.FieldAttr.name == attr_name)).one():
                log.debug("Adding new field attr %s.%s", typ, attr_name)
                attr_dict['name'] = attr_name
                field.attrs.add(models.db_forge_obj(store, models.FieldAttr, attr_dict))
