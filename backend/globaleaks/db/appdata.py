# -*- coding: UTF-8
# datainit.py: database initialization
#   ******************
import json

import re
import os

from globaleaks import models
from globaleaks.orm import transact
from globaleaks.handlers.admin.user import db_create_admin
#from globaleaks.handlers.submission import db_assign_submission_sequence
from globaleaks.handlers.admin.field import db_create_field
from globaleaks.rest import errors, requests
from globaleaks.settings import GLSettings
from globaleaks.security import get_salt
from globaleaks.third_party import rstr
from globaleaks.utils.utility import datetime_null


possible_glclient_paths = [
    '/usr/share/globaleaks/glclient/',
    '../../../client/build/',
    '../../../client/app/'
]


def load_appdata():
    appdata_dict = None

    this_directory = os.path.dirname(__file__)

    for path in possible_glclient_paths:
        fl10n_file = os.path.join(this_directory, path, 'data/appdata.json')

        if os.path.exists(fl10n_file):
            with file(fl10n_file, 'r') as f:
                json_string = f.read()
                appdata_dict = json.loads(json_string)
                return appdata_dict

    raise errors.InternalServerError("Unable to load application data")


def load_default_fields(store):
    this_directory = os.path.dirname(__file__)

    for path in possible_glclient_paths:
        default_fields_path = os.path.join(this_directory, path, 'data/fields')

        if os.path.exists(default_fields_path):
            for fname in os.listdir(default_fields_path):
                fpath = os.path.join(default_fields_path, fname)
                with file(fpath, 'r') as f:
                    json_string = f.read()
                    field_dict = json.loads(json_string)
                    db_create_field(store, field_dict, None)

            return


def db_init_appdata(store):
    # Load new appdata
    appdata_dict = load_appdata()

    # Drop old appdata
    store.find(models.ApplicationData).remove()

    # Setup new appdata
    appdata = models.ApplicationData(appdata_dict)
    appdata.version = appdata_dict['version']
    appdata.default_questionnaire = appdata_dict['default_questionnaire']

    store.add(models.ApplicationData(appdata_dict))

    return appdata_dict


@transact
def init_appdata(store):
    return db_init_appdata(store)
