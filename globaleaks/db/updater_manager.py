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

    print starting_ver, ending_ver

    if not starting_ver:
        old_db_file = os.path.abspath(os.path.join(
            GLSetting.gldb_path, 'glbackend.db'))
    else:
        old_db_file = os.path.abspath(os.path.join(
            GLSetting.gldb_path, 'glbackend-%d.db' % starting_ver))

    new_db_file = os.path.abspath(os.path.join(GLSetting.gldb_path, 'glbackend-%d.db' % ending_ver))

    from globaleaks.db.update_0_1 import Replacer01

    UpdateDict = {
        "01" : Replacer01,
    }

    while starting_ver < ending_ver:
        print "Updating DB from version %d to version %d" % (starting_ver, starting_ver +1)
        update_key = "%d%d" % (starting_ver, starting_ver +1)

        if not UpdateDict.has_key(update_key):
            raise NotImplementedError

        updater_code = UpdateDict[update_key](old_db_file, new_db_file)

        updater_code.initialize()

        for model_name in orm_classes_list:
            migrate_function = 'migrate_%s' % model_name.__name__
            getattr(updater_code, migrate_function)()

        updater_code.epilogue()

        starting_ver += 1

    GLSetting.db_file = 'sqlite:' + new_db_file
    print "New database file: %s" % GLSetting.db_file


