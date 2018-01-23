# -*- coding: utf-8 -*-
import os

from globaleaks.models.config import ConfigFactory
from globaleaks.settings import Settings
from globaleaks.utils.utility import read_json_file


def load_profile(session, tid, name):
    path = os.path.join(Settings.client_path, 'data/profiles', '{}.json'.format(name))
    prof = read_json_file(path)

    ConfigFactory(session, tid, 'node').update(prof['node'])
