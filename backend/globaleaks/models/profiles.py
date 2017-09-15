# -*- coding: utf-8 -*-
import os

from globaleaks.models.config import NodeFactory
from globaleaks.settings import Settings
from globaleaks.utils.utility import read_json_file


def load_profile(store, tid, name):
    path = os.path.join(Settings.client_path, 'data/profiles', '{}.json'.format(name))
    prof = read_json_file(path)

    if not set(prof['node'].keys()) <= NodeFactory.admin_node:
        raise ValueError('profile configuration key not in admin_node')

    NodeFactory(store, tid).update(prof['node'])
