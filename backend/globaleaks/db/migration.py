# -*- encoding: utf-8 -*-
from collections import OrderedDict
import importlib
import os
import shutil

from storm.locals import create_database, Store

from globaleaks import models, DATABASE_VERSION, FIRST_DATABASE_VERSION_SUPPORTED
from globaleaks.settings import GLSettings

from globaleaks.db.migrations.update_12 import Node_v_11, Context_v_11
from globaleaks.db.migrations.update_13 import Node_v_12, Context_v_12
from globaleaks.db.migrations.update_14 import Node_v_13, Context_v_13
from globaleaks.db.migrations.update_15 import Node_v_14, User_v_14, Context_v_14, Receiver_v_14, \
    InternalTip_v_14, Notification_v_14, Comment_v_14
from globaleaks.db.migrations.update_16 import Receiver_v_15, Notification_v_15
from globaleaks.db.migrations.update_17 import Node_v_16, Receiver_v_16, Notification_v_16, Stats_v_16
from globaleaks.db.migrations.update_18 import Node_v_17
from globaleaks.db.migrations.update_19 import Node_v_18
from globaleaks.db.migrations.update_20 import Node_v_19, Notification_v_19, Comment_v_19, Message_v_19, \
    InternalTip_v_19, ReceiverTip_v_19, InternalFile_v_19, ReceiverFile_v_19, Receiver_v_19, Context_v_19
from globaleaks.db.migrations.update_21 import Node_v_20, Notification_v_20, Receiver_v_20, User_v_20, \
    Context_v_20, Step_v_20, Field_v_20, FieldOption_v_20, InternalTip_v_20
from globaleaks.db.migrations.update_22 import Context_v_21, InternalTip_v_21
from globaleaks.db.migrations.update_23 import InternalFile_v_22, Comment_v_22, Context_v_22, \
    Field_v_22, FieldOption_v_22, Notification_v_22, InternalTip_v_22
from globaleaks.db.migrations.update_24 import User_v_23, Receiver_v_23, Node_v_23, Notification_v_23, \
    Context_v_23, InternalTip_v_23, Step_v_23, Field_v_23, ArchivedSchema_v_23, ReceiverTip_v_23
from globaleaks.db.migrations.update_25 import User_v_24
from globaleaks.db.migrations.update_26 import InternalFile_v_25

migration_mapping = OrderedDict([
    ('Anomalies', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models.Anomalies, 0, 0, 0, 0]),
    ('ArchivedSchema', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, ArchivedSchema_v_23, models.ArchivedSchema, 0, 0, 0]),
    ('ApplicationData', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models.ApplicationData, 0, 0, 0]),
    ('Comment', [Comment_v_14, 0, 0, 0, Comment_v_19, 0, 0, 0, 0, Comment_v_22, 0, 0, models.Comment, 0, 0, 0, 0]),
    ('Context', [Context_v_11, Context_v_12, Context_v_13, Context_v_14, Context_v_19, 0, 0, 0, 0, Context_v_20, Context_v_21, Context_v_22, Context_v_23, models.Context, 0, 0, 0]),
    ('Custodian', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models.Custodian, 0, 0, 0]),
    ('CustodianContext', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models.CustodianContext, 0, 0, 0]),
    ('Field', [-1, -1, -1, -1, Field_v_20, 0, 0, 0, 0, 0, Field_v_22, 0, Field_v_23, models.Field, 0, 0, 0]),
    ('FieldAnswer', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models.FieldAnswer, 0, 0, 0, 0]),
    ('FieldAnswerGroup', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models.FieldAnswerGroup, 0, 0, 0, 0]),
    ('FieldAnswerGroupFieldAnswer', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models.FieldAnswerGroupFieldAnswer, 0, 0, 0, 0]),
    ('FieldAttr', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models.FieldAttr, 0, 0, 0, 0]),
    ('FieldField', [-1, -1, -1, -1, models.FieldField, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('FieldOption', [-1, -1, -1, -1, FieldOption_v_20, 0, 0, 0, 0, 0, FieldOption_v_22, 0, models.FieldOption, 0, 0, 0, 0]),
    ('IdentityAccessRequest', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models.IdentityAccessRequest, 0, 0, 0]),
    ('Mail', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models.Mail, 0]),
    ('Message', [Message_v_19, 0, 0, 0, 0, 0, 0, 0, 0, models.Message, 0, 0, 0, 0, 0, 0, 0]),
    ('Node', [Node_v_11, Node_v_12, Node_v_13, Node_v_14, Node_v_16, 0, Node_v_17, Node_v_18, Node_v_19, Node_v_20, Node_v_23, 0, 0, models.Node, 0, 0, 0]),
    ('Notification', [Notification_v_14, 0, 0, 0, Notification_v_15, Notification_v_16, Notification_v_19, 0, 0, Notification_v_20, Notification_v_22, 0, Notification_v_23, models.Notification, 0, 0, 0]),
    ('InternalFile', [InternalFile_v_19, 0, 0, 0, 0, 0, 0, 0, 0, InternalFile_v_22, 0, 0, InternalFile_v_25, 0, 0, models.InternalFile, 0]),
    ('InternalTip', [InternalTip_v_14, 0, 0, 0, InternalTip_v_19, 0, 0, 0, 0, InternalTip_v_20, InternalTip_v_21, InternalTip_v_22, InternalTip_v_23, models.InternalTip, 0, 0, 0]),
    ('OptionActivateField', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models.OptionActivateField, 0, 0, 0]),
    ('OptionActivateStep', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models.OptionActivateStep, 0, 0]),
    ('Receiver', [Receiver_v_14, 0, 0, 0, Receiver_v_15, Receiver_v_16, Receiver_v_19, 0, 0, Receiver_v_20, Receiver_v_23, 0, 0, models.Receiver, 0, 0, 0]),
    ('ReceiverContext', [models.ReceiverContext, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('ReceiverFile', [ReceiverFile_v_19, 0, 0, 0, 0, 0, 0, 0, 0, models.ReceiverFile, 0, 0, 0, 0, 0, 0, 0]),
    ('ReceiverInternalTip', [models.ReceiverInternalTip, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('ReceiverTip', [ReceiverTip_v_19, 0, 0, 0, 0, 0, 0, 0, 0, ReceiverTip_v_23, 0, 0, 0, models.ReceiverTip, 0, 0, 0]),
    ('Step', [-1, -1, -1, -1, Step_v_20, 0, 0, 0, 0, 0, Step_v_23, 0, 0, models.Step, 0, 0, 0]),
    ('StepField', [-1, -1, -1, -1, models.StepField, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('SecureFileDelete', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models.SecureFileDelete, 0, 0, 0]),
    ('Stats', [-1, -1, -1, -1, Stats_v_16, 0, models.Stats, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('User', [User_v_14, 0, 0, 0, User_v_20, 0, 0, 0, 0, 0, User_v_23, 0, 0, User_v_24, models.User, 0, 0]),
    ('WhistleblowerTip', [models.WhistleblowerTip, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
])

def perform_version_update(version):
    """
    @param version:
    @return:
    """
    to_delete_on_fail = []
    to_delete_on_success = []

    if version < FIRST_DATABASE_VERSION_SUPPORTED:
        print "Migrations from DB version lower than %d are no more supported!" % FIRST_DATABASE_VERSION_SUPPORTED
        print "If you can't create your Node from scratch, contact us asking for support."
        quit()

    try:
        tmpdir =  os.path.abspath(os.path.join(GLSettings.db_path, 'tmp'))
        orig_db_file = os.path.abspath(os.path.join(GLSettings.db_path, 'glbackend-%d.db' % version))
        final_db_file = os.path.abspath(os.path.join(GLSettings.db_path, 'glbackend-%d.db' % DATABASE_VERSION))

        shutil.rmtree(tmpdir, True)
        os.mkdir(tmpdir)
        shutil.copy2(orig_db_file, tmpdir)

        while version < DATABASE_VERSION:
            old_db_file = os.path.abspath(os.path.join(tmpdir, 'glbackend-%d.db' % version))
            new_db_file = os.path.abspath(os.path.join(tmpdir, 'glbackend-%d.db' % (version + 1)))

            GLSettings.db_file = new_db_file
            GLSettings.enable_input_length_checks = False

            to_delete_on_fail.append(new_db_file)
            to_delete_on_success.append(old_db_file)
            
            print "Updating DB from version %d to version %d" % (version, version + 1)

            store_old = Store(create_database('sqlite:' + old_db_file))
            store_new = Store(create_database('sqlite:' + new_db_file))

            # Here is instanced the migration script
            MigrationModule = importlib.import_module("globaleaks.db.migrations.update_%d" % (version + 1))
            migration_script = MigrationModule.MigrationScript(migration_mapping, version, store_old, store_new)

            print "Migrating table:"

            try:
                try:
                    migration_script.prologue()
                except Exception as exception:
                    print "Failure while executing migration prologue: %s " % exception
                    raise exception

                for model_name, _ in migration_mapping.iteritems():
                    if migration_script.model_from[model_name] is not None and migration_script.model_to[model_name] is not None:
                        try:
                            migration_script.migrate_model(model_name)

                            # Commit at every table migration in order to be able to detect
                            # the precise migration that may fail.
                            migration_script.commit()
                        except Exception as exception:
                            print "Failure while migrating table %s: %s " % (model_name, exception)
                            raise exception
                try:
                    migration_script.epilogue()
                    migration_script.commit()
                except Exception as exception:
                    print "Failure while executing migration epilogue: %s " % exception
                    raise exception

            finally:
                # the database should bee always closed before leaving the application
                # in order to not keep leaking journal files.
                migration_script.close()

            print "Migration stats:"

            # we open a new db in order to verify integrity of the generated file
            store_verify = Store(create_database('sqlite:' + new_db_file))

            for model_name, _ in migration_mapping.iteritems():
                if model_name == 'ApplicationData':
                    continue

                if migration_script.model_from[model_name] is not None and migration_script.model_to[model_name] is not None:
                     count = store_verify.find(migration_script.model_to[model_name]).count()
                     if migration_script.entries_count[model_name] != count:
                         if migration_script.fail_on_count_mismatch[model_name]:
                             raise AssertionError("Integrity check failed on count equality for table %s: %d != %d" %
                                                (model_name, count, migration_script.entries_count[model_name]))
                         else:
                             print " * %s table migrated (entries count changed from %d to %d)" % \
                                     (model_name, migration_script.entries_count[model_name], count)
                     else:
                         print " * %s table migrated (%d entry(s))" % \
                                 (model_name, migration_script.entries_count[model_name])

            version += 1

    except Exception as exception:
        # simply propagage the exception
        raise exception

    else:
        # in case of success first copy the new migrated db, then as last action delete the original db file
        shutil.copy(os.path.abspath(os.path.join(tmpdir, 'glbackend-%d.db' % DATABASE_VERSION)), final_db_file)
        os.remove(orig_db_file)

    finally:
        # always cleanup the temporary directory used for the migration
        shutil.rmtree(tmpdir, True)
