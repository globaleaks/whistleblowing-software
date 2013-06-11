# -*- encoding: utf-8 -*-
import os

from globaleaks.utils import GLSetting
from globaleaks.models import models as orm_classes_list

def perform_version_update(starting_ver, ending_ver, start_path):
    """
    @param starting_ver:
    @param ending_ver:
    @param start_path:
    @return:
    """
    assert os.path.isfile(start_path)
    assert starting_ver < ending_ver

    if not starting_ver:
        old_db_file = os.path.abspath(os.path.join(
            GLSetting.gldb_path, 'glbackend.db'))
    else:
        old_db_file = os.path.abspath(os.path.join(
            GLSetting.gldb_path, 'glbackend-%d.db' % starting_ver))

    from globaleaks.db.update_0_1 import Replacer01

    releases_supported= {
        "01" : Replacer01,
    }

    aimed_version = 0
    while starting_ver < ending_ver:
        aimed_version = starting_ver + 1
        new_db_file = os.path.abspath(os.path.join(GLSetting.gldb_path, 'glbackend-%d.db' % aimed_version))
        print "Updating DB from version %d to version %d" % (starting_ver, aimed_version)
        update_key = "%d%d" % (starting_ver, aimed_version)

        if not releases_supported.has_key(update_key):
            raise NotImplementedError

        updater_code = releases_supported[update_key](old_db_file, new_db_file)

        updater_code.initialize()

        for model_name in orm_classes_list:
            migrate_function = 'migrate_%s' % model_name.__name__
            print "version %s - single method: is calling %s" % (update_key, migrate_function)
            getattr(updater_code, migrate_function)()

        updater_code.epilogue()
        updater_code.close()

        starting_ver += 1

    print "Latest db version used in: %s" % aimed_version
    print "Goal: %s" % GLSetting.file_versioned_db


