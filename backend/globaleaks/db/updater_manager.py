# -*- encoding: utf-8 -*-
import os

from globaleaks.settings import GLSetting
from globaleaks import models, FIRST_DATABASE_VERSION_SUPPORTED

from globaleaks.db.migrations.update_11_12 import Replacer1112, Node_v_11, Context_v_11
from globaleaks.db.migrations.update_12_13 import Replacer1213, Node_v_12, Context_v_12
from globaleaks.db.migrations.update_13_14 import Replacer1314, Node_v_13, Context_v_13
from globaleaks.db.migrations.update_14_15 import Replacer1415, Node_v_14, User_v_14, Context_v_14, Receiver_v_14, \
    InternalTip_v_14, Notification_v_14, Stats_v_14, Comment_v_14
from globaleaks.db.migrations.update_15_16 import Replacer1516, Receiver_v_15, Notification_v_15
from globaleaks.db.migrations.update_16_17 import Replacer1617, Node_v_16, Receiver_v_16, Notification_v_16, Stats_v_16
from globaleaks.db.migrations.update_17_18 import Replacer1718, Node_v_17
from globaleaks.db.migrations.update_18_19 import Replacer1819, Node_v_18
from globaleaks.db.migrations.update_19_20 import Replacer1920, Node_v_19, Notification_v_19, Comment_v_19, Message_v_19, \
    InternalTip_v_19, ReceiverTip_v_19, InternalFile_v_19, ReceiverFile_v_19, Receiver_v_19, Context_v_19
from globaleaks.db.migrations.update_20_21 import Replacer2021, Node_v_20, Notification_v_20, Receiver_v_20, User_v_20, \
    Context_v_20, Step_v_20, Field_v_20, FieldOption_v_20, InternalTip_v_20
from globaleaks.db.migrations.update_21_22 import Replacer2122, Context_v_21, InternalTip_v_21
from globaleaks.db.migrations.update_22_23 import Replacer2223, InternalFile_v_22, Comment_v_22, Context_v_22, \
    Field_v_22, FieldOption_v_22


table_history = {
    'Node': [Node_v_11, Node_v_12, Node_v_13, Node_v_14, Node_v_16, None, Node_v_17, Node_v_18, Node_v_19, Node_v_20, models.Node, None, None],
    'User': [User_v_14, None, None, None, User_v_20, None, None, None, None, None, models.User, None, None],
    'Context': [Context_v_11, Context_v_12, Context_v_13, Context_v_14, Context_v_19, None, None, None, None, Context_v_20, Context_v_21, Context_v_22, models.Context],
    'Receiver': [Receiver_v_14, None, None, None, Receiver_v_15, Receiver_v_16, Receiver_v_19, None, None, Receiver_v_20, models.Receiver, None, None],
    'ReceiverFile': [ReceiverFile_v_19, None, None, None, None, None, None, None, None, models.ReceiverFile, None, None, None],
    'Notification': [Notification_v_14, None, None, None, Notification_v_15, Notification_v_16, Notification_v_19, None, None, Notification_v_20, models.Notification, None, None],
    'Comment': [Comment_v_14, None, None, None, Comment_v_19, None, None, None, None, Comment_v_22, None, None, models.Comment],
    'InternalTip': [InternalTip_v_14, None, None, None, InternalTip_v_19, None, None, None, None, InternalTip_v_20, InternalTip_v_21, models.InternalTip, None],
    'InternalFile': [InternalFile_v_19, None, None, None, None, None, None, None, None, InternalFile_v_22, None, None, models.InternalFile],
    'WhistleblowerTip': [models.WhistleblowerTip, None, None, None, None, None, None, None, None, None, None, None, None],
    'ReceiverTip': [ReceiverTip_v_19, None, None, None, None, None, None, None, None, models.ReceiverTip, None, None, None],
    'ReceiverInternalTip': [models.ReceiverInternalTip, None, None, None, None, None, None, None, None, None, None, None, None],
    'ReceiverContext': [models.ReceiverContext, None, None, None, None, None, None, None, None, None, None, None, None],
    'Message': [Message_v_19, None, None, None, None, None, None, None, None, models.Message, None, None, None],
    'Stats': [Stats_v_14, None, None, None, Stats_v_16, None, models.Stats, None, None, None, None, None, None],
    'ApplicationData': [models.ApplicationData, None, None, None, None, None, None, None, None, None, None, None, None],
    'Field': [Field_v_20, None, None, None, None, None, None, None, None, None, Field_v_22, None, models.Field],
    'FieldAttr': [models.FieldAttr, None, None, None, None, None, None, None, None, None, None, None, None],
    'FieldOption': [FieldOption_v_20, None, None, None, None, None, None, None, None, None, FieldOption_v_22, None, models.FieldOption],
    'FieldField': [models.FieldField, None, None, None, None, None, None, None, None, None, None, None, None],
    'Step': [Step_v_20, None, None, None, None, None, None, None, None, None, models.Step, None, None],
    'StepField': [models.StepField, None, None, None, None, None, None, None, None, None, None, None, None],
    'Anomalies': [models.Anomalies, None, None, None, None, None, None, None, None, None, None, None, None],
    'EventLogs': [models.EventLogs, None, None, None, None, None, None, None, None, None, None, None, None]
}


def perform_version_update(starting_ver, ending_ver):
    """
    @param starting_ver:
    @param ending_ver:
    @return:
    """
    releases_supported = {
        "1112": Replacer1112,
        "1213": Replacer1213,
        "1314": Replacer1314,
        "1415": Replacer1415,
        "1516": Replacer1516,
        "1617": Replacer1617,
        "1718": Replacer1718,
        "1819": Replacer1819,
        "1920": Replacer1920,
        "2021": Replacer2021,
        "2122": Replacer2122,
        "2223": Replacer2223
    }
    
    to_delete_on_fail = []
    to_delete_on_success = []

    if starting_ver < FIRST_DATABASE_VERSION_SUPPORTED:
        print "Migrations from DB version lower than %d are no more supported!" % FIRST_DATABASE_VERSION_SUPPORTED
        print "If you can't create your Node from scratch, contact us asking for support."
        quit()

    try:
        while starting_ver < ending_ver:
            if not starting_ver:
                old_db_file = os.path.abspath(os.path.join(
                    GLSetting.gldb_path, 'glbackend.db'))
            else:
                old_db_file = os.path.abspath(os.path.join(
                    GLSetting.gldb_path, 'glbackend-%d.db' % starting_ver))

            new_db_file = os.path.abspath(os.path.join(GLSetting.gldb_path, 'glbackend-%d.db' % (starting_ver + 1)))
            
            to_delete_on_fail.append(new_db_file)
            to_delete_on_success.append(old_db_file)
            
            print "Updating DB from version %d to version %d" % (starting_ver, starting_ver + 1)

            update_key = "%d%d" % (starting_ver, starting_ver + 1)
            if update_key not in releases_supported:
                raise NotImplementedError("mistake detected! %s" % update_key)

            try:
                # Here is instanced the migration class
                updater_code = releases_supported[update_key](table_history, old_db_file, new_db_file, starting_ver)
            except Exception as excep:
                print "__init__ updater_code: %s " % excep.message
                raise excep

            try:
                updater_code.initialize()
            except Exception as excep:
                print "initialize of updater class: %s " % excep.message
                raise excep

            for model in models.models_list:
                migrate_function = 'migrate_%s' % model.__name__
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
