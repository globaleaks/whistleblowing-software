# -*- coding: UTF-8
# GLBackend Database
#   ******************
from __future__ import with_statement

import json

import re
import os

from globaleaks import models
from globaleaks.orm import transact, transact_ro
from globaleaks.handlers.admin.user import db_create_admin
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
        fl10n_file = os.path.join(this_directory, path, 'data/appdata_l10n.json')

        if os.path.exists(fl10n_file):
            with file(fl10n_file, 'r') as f:
                json_string = f.read()
                appdata_dict = json.loads(json_string)
                return appdata_dict

    raise errors.InternalServerError("Unable to load application data")


def load_default_fields(store):
    appdata_dict = None

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


@transact
def init_appdata(store, result, appdata_dict):
    # Drop old appdata
    store.find(models.ApplicationData).remove()

    # Initialize the default data table evry time with
    # fresh data and fresh translations
    appdata = models.ApplicationData()
    appdata.version = appdata_dict['version']
    appdata.default_questionnaire = appdata_dict['default_questionnaire']
    store.add(appdata)


@transact
def init_db(store, result, node_dict, appdata_dict):
    """
    """
    node = models.Node(node_dict)
    node.languages_enabled = GLSettings.defaults.languages_enabled
    node.receipt_salt = get_salt(rstr.xeger('[A-Za-z0-9]{56}'))
    node.wizard_done = GLSettings.skip_wizard

    for k in appdata_dict['node']:
        setattr(node, k, appdata_dict['node'][k])

    store.add(node)

    admin_dict = {
        'username': u'admin',
        'password': u'globaleaks',
        'deeletable': False,
        'role': u'admin',
        'state': u'enabled',
        'deletable': False,
        'name': u'Admin',
        'description': u'',
        'mail_address': u'',
        'language': GLSettings.defaults.language,
        'timezone': GLSettings.defaults.timezone,
        'password_change_needed': False,
        'pgp_key_status': 'disabled',
        'pgp_key_info': '',
        'pgp_key_fingerprint': '',
        'pgp_key_public': '',
        'pgp_key_expiration': datetime_null()
    }

    admin = db_create_admin(store, admin_dict, GLSettings.defaults.language)
    admin.password_change_needed = False

    notification = models.Notification()
    for k in appdata_dict['templates']:
        setattr(notification, k, appdata_dict['templates'][k])

    load_default_fields(store)

    store.add(notification)
