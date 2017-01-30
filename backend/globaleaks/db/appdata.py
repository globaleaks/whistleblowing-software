# -*- coding: UTF-8
# datainit.py: database initialization
#   ******************
import json
import os

from storm.expr import And, Not, In

from globaleaks import models
from globaleaks.handlers.admin.field import db_create_field, db_import_fields
from globaleaks.orm import transact
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import log


def read_appdata(p):
    with file(p, 'r') as f:
        json_string = f.read()
        appdata_dict = json.loads(json_string)
        return appdata_dict


def load_appdata():
    return read_appdata(GLSettings.appdata_file)


def load_archived_appdata(p):
    return read_appdata(p)


def load_default_questionnaires(store):
    appdata = store.find(models.ApplicationData).one()
    steps = appdata.default_questionnaire['steps']
    del appdata.default_questionnaire['steps']

    questionnaire = store.find(models.Questionnaire, models.Questionnaire.key == u'default').one()
    if questionnaire is None:
        questionnaire = models.db_forge_obj(store, models.Questionnaire, appdata.default_questionnaire)
    else:
        for step in questionnaire.steps:
            store.remove(step)

    for step in steps:
        f_children = step['children']
        del step['children']
        s = models.db_forge_obj(store, models.Step, step)
        db_import_fields(store, s, None, f_children)
        s.questionnaire_id = questionnaire.id


def load_default_fields(store):
    for fname in os.listdir(GLSettings.fields_path):
        fpath = os.path.join(GLSettings.fields_path, fname)
        with file(fpath, 'r') as f:
            json_string = f.read()
            field_dict = json.loads(json_string)
            old_field = store.find(models.Field, models.Field.key == field_dict['key']).one()

            if old_field is not None:
                field_dict['id'] = old_field.id
                store.remove(old_field)

            db_create_field(store, field_dict, None)


def db_update_appdata(store):
    # Load new appdata
    appdata_dict = load_appdata()

    # Drop old appdata
    store.find(models.ApplicationData).remove()

    # Load and setup new appdata
    store.add(models.ApplicationData(appdata_dict))

    load_default_questionnaires(store)
    load_default_fields(store)

    return appdata_dict


@transact
def update_appdata(store):
    return db_update_appdata(store)


def db_fix_fields_attrs(store):
    '''
    Ensures that the current store and the field_attrs.json file correspond.
    The content of the field_attrs dict is used to add and remove all of the
    excepted forms of field_attrs for FieldAttrs in the db.
    '''

    # Load the field attributes descriptors
    field_attrs = {}
    with file(GLSettings.field_attrs_file, 'r') as f:
        json_string = f.read()
        field_attrs = json.loads(json_string)

    std_lst = ['inputbox', 'textarea', 'multichoice', 'checkbox', 'tos', 'date']

    for field_type, attrs_dict in field_attrs.iteritems():
        attrs_to_keep_for_type = attrs_dict.keys()
        if field_type in std_lst:
            # Ensure that the standard field attrs do not have extra attr rows
            res = store.find(models.FieldAttr, Not(In(models.FieldAttr.name, attrs_to_keep_for_type)),
                                               models.FieldAttr.field_id == models.Field.id,
                                               models.Field.type == field_type,
                                               models.Field.key == unicode(''))
        else:
            # Look for dropped attrs in non-standard field_groups like whistleblower_identity
            res = store.find(models.FieldAttr, Not(In(models.FieldAttr.name, attrs_to_keep_for_type)),
                                               models.FieldAttr.field_id == models.Field.id,
                                               models.Field.key == field_type)

        count = res.count()
        if count:
            log.debug("Removing %d attributes from fields of type %s" % (count, field_type))
            for r in res:
                store.remove(r)

    # Add keys to the db that have been added to field_attrs
    for field in store.find(models.Field):
        typ = field.type if field.key == '' else field.key
        attrs = field_attrs.get(typ, {})
        for attr_name, attr_dict in attrs.iteritems():
            if not store.find(models.FieldAttr,
                              And(models.FieldAttr.field_id == field.id,
                                  models.FieldAttr.name == attr_name)).one():
                log.debug("Adding new field attr %s.%s" % (typ, attr_name))
                attr_dict['name'] = attr_name
                field.attrs.add(models.db_forge_obj(store, models.FieldAttr, attr_dict))
