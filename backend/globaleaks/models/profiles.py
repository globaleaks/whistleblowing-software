# -*- coding: utf-8 -*-
import json
import os

from globaleaks.models.config import NodeFactory
from globaleaks.settings import GLSettings


def load_profile(store, name):
    path = os.path.join(GLSettings.client_path, 'data/profiles', '{}.json'.format(name))
    with open(path, 'r') as f:
        prof = json.loads(f.read())

    if not set(prof['node'].keys()) <= NodeFactory.admin_node:
        raise ValueError('profile configuration key not in admin_node')

    nf = NodeFactory(store)
    nf.update(prof['node'])
