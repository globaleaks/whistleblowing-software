# -*- coding: UTF-8
# datainit.py: database initialization
#   ******************
import copy
import json
import os

from globaleaks import models
from globaleaks.orm import transact
from globaleaks.handlers.admin.field import db_create_field, db_import_fields
from globaleaks.rest import errors
from globaleaks.settings import GLSettings


def load_appdata():
    if os.path.exists(GLSettings.appdata_file):
        with file(GLSettings.appdata_file, 'r') as f:
            json_string = f.read()
            appdata_dict = json.loads(json_string)
            return appdata_dict

    raise errors.InternalServerError("Unable to load application data")


def load_default_questionnaires(store):
    appdata = store.find(models.ApplicationData).one()
    steps = appdata.default_questionnaire['steps']
    del appdata.default_questionnaire['steps']

    questionnaire = store.find(models.Questionnaire, models.Questionnaire.key == u'default').one()
    if questionnaire is not None:
        store.remove(questionnaire.steps)
    else:
        questionnaire = models.db_forge_obj(store, models.Questionnaire, appdata.default_questionnaire)

    for step in steps:
        f_children = step['children']
        del step['children']
        s = models.db_forge_obj(store, models.Step, step)
        db_import_fields(store, s, None, f_children)
        s.questionnaire_id = questionnaire.id


def load_default_fields(store):
    try:
        if os.path.exists(GLSettings.fields_path):
            for fname in os.listdir(GLSettings.fields_path):
                fpath = os.path.join(GLSettings.fields_path, fname)
                with file(fpath, 'r') as f:
                    json_string = f.read()
                    field_dict = json.loads(json_string)
                    db_create_field(store, field_dict, None)
    except Exception as e:
        raise errors.InternalServerError("Unable to load default fields: %s" % e)


def db_init_appdata(store):
    # Load new appdata
    appdata_dict = load_appdata()

    # Drop old appdata
    store.find(models.ApplicationData).remove()

    # Load and setup new appdata
    store.add(models.ApplicationData(appdata_dict))

    return appdata_dict


@transact
def init_appdata(store):
    return db_init_appdata(store)
