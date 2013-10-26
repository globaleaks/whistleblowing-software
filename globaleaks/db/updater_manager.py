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

    from globaleaks.db.update_5_6 import Replacer56
    from globaleaks.db.update_6_7 import Replacer67

    releases_supported = {
        "56" : Replacer56,
        "67" : Replacer67,
    }
    
    to_delete_on_fail = []
    to_delete_on_success = []

    if starting_ver < 5:
        print "Migration from DB version lower than 5 its no more supported!"
        print "asks for supports if you can't create your Node from scratch"
        quit()

    try:

        while starting_ver < ending_ver:

            if not starting_ver:
                old_db_file = os.path.abspath(os.path.join(
                    GLSetting.gldb_path, 'glbackend.db'))
                backup_file = os.path.abspath(os.path.join(
                    GLSetting.gldb_path, 'conversion_backup_%d_%d.bak' % (starting_ver, starting_ver + 1)))
            else:
                old_db_file = os.path.abspath(os.path.join(
                    GLSetting.gldb_path, 'glbackend-%d.db' % starting_ver))
                backup_file = os.path.abspath(os.path.join(
                    GLSetting.gldb_path, 'conversion_backup_%d_%d.bak' % (starting_ver, starting_ver + 1)))

            new_db_file = os.path.abspath(os.path.join(GLSetting.gldb_path, 'glbackend-%d.db' % (starting_ver + 1)))
            
            to_delete_on_fail.append(new_db_file)
            to_delete_on_success.append(old_db_file)
            
            print "  Updating DB from version %d to version %d" % (starting_ver, starting_ver + 1)

            update_key = "%d%d" % (starting_ver, starting_ver + 1)
            if not releases_supported.has_key(update_key):
                raise NotImplementedError("mistake detect! %s" % update_key)

            try:
                # Here is instanced the migration class
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

    except Exception as except_info:
        print "Internal error triggered: %s" % except_info
        # Remediate action on fail:
        #    created files during update must be deleted
        for f in to_delete_on_fail:
            try:
                os.remove(f)
            except Exception as excep:
                print "Error removing new db file on conversion fail: %s" % excep
                # we can't stop if one files removal fails
                # and we continue trying deleting others files
                pass
        # propagate the exception
        raise except_info

    # Finalize action on success:
    #    converted files must be renamed
    for f in to_delete_on_success:
        try:
            os.remove(f)
        except Exception as excep:
            print "Error removing old db file on conversion success: %s" % excep.message
            # we can't stop if one files removal fails
            # and we continue trying deleting others files
            pass
