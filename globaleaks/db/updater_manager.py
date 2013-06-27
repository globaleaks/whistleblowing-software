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

    from globaleaks.db.update_0_1 import Replacer01
    from globaleaks.db.update_1_2 import Replacer12

    releases_supported = {
        "01" : Replacer01,
        "12" : Replacer12
    }

    while starting_ver < ending_ver:

        if not starting_ver:
            old_db_file = os.path.abspath(os.path.join(
                GLSetting.gldb_path, 'glbackend.db'))
            backup_file = os.path.abspath(os.path.join(
                GLSetting.gldb_path, 'old_glbackend.db'))
        else:
            old_db_file = os.path.abspath(os.path.join(
                GLSetting.gldb_path, 'glbackend-%d.db' % starting_ver))
            backup_file = os.path.abspath(os.path.join(
                GLSetting.gldb_path, 'old_glbackend-%d.db' % starting_ver))

        new_db_file = os.path.abspath(os.path.join(GLSetting.gldb_path, 'glbackend-%d.db' % (starting_ver +1)))
        print "  Updating DB from version %d to version %d" % (starting_ver, starting_ver +1)

        update_key = "%d%d" % (starting_ver, starting_ver + 1)
        if not releases_supported.has_key(update_key):
            raise NotImplementedError

        try:
            updater_code = releases_supported[update_key](old_db_file, new_db_file, starting_ver)
        except Exception as excep:
            print "__init__ updater_code: %s " % excep.message
            raise excep

        try:
            updater_code.initialize()
        except Exception as excep:
            print "initialize of updater class: %s " % excep.message
            raise excep

        for model_name in orm_classes_list:

            migrate_function = 'migrate_%s' % model_name.__name__
            function_pointer = getattr(updater_code, migrate_function)

            try:
                function_pointer()
            except Exception as excep:
                print "Failure in %s: %s " % (migrate_function, excep)
                raise excep

        # epilogue can be used to perform operation once, not related to the tables
        updater_code.epilogue()
        updater_code.close()

        starting_ver += 1

        if os.path.isfile(backup_file):
            try:
                os.unlink(backup_file)
            except Exception as excep:
                print "Error in unlink and old version backup files: %s" % excep.message
                raise excep

        os.rename(old_db_file, backup_file)



