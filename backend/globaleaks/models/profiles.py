# -*- coding: utf-8 -*-
import os

from globaleaks.models.config import ConfigFactory
from globaleaks.settings import Settings
from globaleaks.utils.fs import read_json_file


def load_profile(session, tid, name):
    """
    Transaction for loading a configuration profile

    :param session: An ORM session
    :param tid: The tenant id of the tenant to be configured
    :param name: The name of the profile to be used
    """
    path = os.path.join(Settings.client_path, 'data/profiles', '{}.json'.format(name))
    prof = read_json_file(path)

    ConfigFactory(session, tid).update('node', prof['node'])
