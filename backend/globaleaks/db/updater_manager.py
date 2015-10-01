# -*- encoding: utf-8 -*-
import os

from globaleaks.settings import GLSettings
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
    Field_v_22, FieldOption_v_22, Notification_v_22, InternalTip_v_22
from globaleaks.db.migrations.update_23_24 import Replacer2324, User_v_23, Receiver_v_23, Node_v_23, Notification_v_23, \
    Context_v_23, InternalTip_v_23, Field_v_23, ArchivedSchema_v_23, FieldField_v_23, StepField_v_23


table_history = {
    'Node': [Node_v_11, Node_v_12, Node_v_13, Node_v_14, Node_v_16, 0, Node_v_17, Node_v_18, Node_v_19, Node_v_20, Node_v_23, 0, 0, models.Node],
    'IdentityAccessRequest': [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models.IdentityAccessRequest],
    'SecureFileDelete': [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models.SecureFileDelete],
    'User': [User_v_14, 0, 0, 0, User_v_20, 0, 0, 0, 0, 0, User_v_23, 0, 0, models.User],
    'Custodian': [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models.Custodian],
    'Receiver': [Receiver_v_14, 0, 0, 0, Receiver_v_15, Receiver_v_16, Receiver_v_19, 0, 0, Receiver_v_20, Receiver_v_23, 0, 0, models.Receiver],
    'Context': [Context_v_11, Context_v_12, Context_v_13, Context_v_14, Context_v_19, 0, 0, 0, 0, Context_v_20, Context_v_21, Context_v_22, Context_v_23, models.Context],
    'ReceiverFile': [ReceiverFile_v_19, 0, 0, 0, 0, 0, 0, 0, 0, models.ReceiverFile, 0, 0, 0, 0],
    'Notification': [Notification_v_14, 0, 0, 0, Notification_v_15, Notification_v_16, Notification_v_19, 0, 0, Notification_v_20, Notification_v_22, 0, Notification_v_23, models.Notification],
    'Comment': [Comment_v_14, 0, 0, 0, Comment_v_19, 0, 0, 0, 0, Comment_v_22, 0, 0, models.Comment, 0],
    'InternalTip': [InternalTip_v_14, 0, 0, 0, InternalTip_v_19, 0, 0, 0, 0, InternalTip_v_20, InternalTip_v_21, InternalTip_v_22, InternalTip_v_23, models.InternalTip],
    'InternalFile': [InternalFile_v_19, 0, 0, 0, 0, 0, 0, 0, 0, InternalFile_v_22, 0, 0, models.InternalFile, 0],
    'WhistleblowerTip': [models.WhistleblowerTip, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    'ReceiverTip': [ReceiverTip_v_19, 0, 0, 0, 0, 0, 0, 0, 0, models.ReceiverTip, 0, 0, 0, 0],
    'ReceiverInternalTip': [models.ReceiverInternalTip, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    'CustodianContext': [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models.CustodianContext],
    'ReceiverContext': [models.ReceiverContext, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    'Message': [Message_v_19, 0, 0, 0, 0, 0, 0, 0, 0, models.Message, 0, 0, 0, 0],
    'Stats': [-1, -1, -1, -1, Stats_v_16, 0, models.Stats, 0, 0, 0, 0, 0, 0, 0],
    'ApplicationData': [models.ApplicationData, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    'Field': [-1, -1, -1, -1, Field_v_20, 0, 0, 0, 0, 0, Field_v_22, 0, Field_v_23, models.Field],
    'FieldAttr': [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models.FieldAttr, 0],
    'FieldOption': [-1, -1, -1, -1, FieldOption_v_20, 0, 0, 0, 0, 0, FieldOption_v_22, 0, models.FieldOption, 0],
    'OptionActivateField': [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models.OptionActivateField],
    'OptionActivateStep': [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models.OptionActivateStep],
    'Step': [-1, -1, -1, -1, Step_v_20, 0, 0, 0, 0, 0, models.Step, 0, 0, 0],
    'Anomalies': [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models.Anomalies, 0],
    'EventLogs': [-1, -1, -1, -1, -1, -1, -1, -1, -1, models.EventLogs, 0, 0, 0, 0],
    'FieldAnswer': [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models.FieldAnswer, 0],
    'FieldAnswerGroup': [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models.FieldAnswerGroup, 0],
    'FieldAnswerGroupFieldAnswer': [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models.FieldAnswerGroupFieldAnswer, 0],
    'ArchivedSchema': [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, ArchivedSchema_v_23, models.ArchivedSchema],
    'FieldField': [-1, -1, -1, -1, FieldField_v_23, 0, 0, 0, 0, 0, 0, 0, 0, -1],
    'StepField': [-1, -1, -1, -1, StepField_v_23, 0, 0, 0, 0, 0, 0, 0, 0, -1]
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
        "2223": Replacer2223,
        "2324": Replacer2324
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
                    GLSettings.gldb_path, 'glbackend.db'))
            else:
                old_db_file = os.path.abspath(os.path.join(
                    GLSettings.gldb_path, 'glbackend-%d.db' % starting_ver))

            new_db_file = os.path.abspath(os.path.join(GLSettings.gldb_path, 'glbackend-%d.db' % (starting_ver + 1)))
            
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

            updater_code.entries_count = {}
            updater_code.fail_on_count_mismatch = {}
            updater_code.fail_on_count_mismatch['ApplicationData'] = False

            for model_name, _ in table_history.iteritems():
                updater_code.fail_on_count_mismatch[model_name] = True

                m_from = updater_code.get_right_model(model_name, starting_ver)
                m_to = updater_code.get_right_model(model_name, starting_ver + 1)

                if m_from is not None and m_to is not None:
                    updater_code.entries_count[model_name] = updater_code.store_old.find(m_from).count()
                else:
                    updater_code.entries_count[model_name] = 0

            for model_name, _ in table_history.iteritems():
                m_from = updater_code.get_right_model(model_name, starting_ver)
                m_to = updater_code.get_right_model(model_name, starting_ver + 1)

                if m_from is not None and m_to is not None:
                    print model_name
                    migrate_function = 'migrate_%s' % model_name
                    function_pointer = getattr(updater_code, migrate_function)

                    try:
                        function_pointer()
                    except Exception as excep:
                        print "Failure in %s: %s " % (migrate_function, excep)
                        raise excep

            print "Migration stats:"
            for model_name, _ in table_history.iteritems():
                if model_name == 'ApplicationData':
                    continue

                m_from = updater_code.get_right_model(model_name, starting_ver)
                m_to = updater_code.get_right_model(model_name, starting_ver + 1)

                if m_from is not None and m_to is not None:
                   count = updater_code.store_new.find(m_to).count()
                   if updater_code.entries_count[model_name] != count:
                       if updater_code.fail_on_count_mismatch[model_name]:
                           raise AssertionError("Integrity check failed on count equality for table %s: %d != %d" %
                                                (model_name, count, updater_code.entries_count[model_name]))
                       else:
                           print " * %s table migrated (entries count changed from %d to %d)" % \
                               (model_name, updater_code.entries_count[model_name], count)
                   else:
                       print " * %s table migrated (%d entry(s))" % \
                           (model_name, updater_code.entries_count[model_name])

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
