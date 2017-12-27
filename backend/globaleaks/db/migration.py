# -*- coding: utf-8 -*-
import importlib
import os
import shutil
from collections import OrderedDict
from storm.database import create_database
from storm.store import Store

from globaleaks import __version__, models, DATABASE_VERSION, FIRST_DATABASE_VERSION_SUPPORTED, \
    LANGUAGES_SUPPORTED_CODES, security
from globaleaks.db.appdata import db_update_defaults, load_appdata, db_fix_fields_attrs
from globaleaks.db.migrations.update_25 import User_v_24
from globaleaks.db.migrations.update_26 import InternalFile_v_25
from globaleaks.db.migrations.update_27 import Node_v_26, Context_v_26, Notification_v_26
from globaleaks.db.migrations.update_28 import Field_v_27, Step_v_27, FieldField_v_27, StepField_v_27, FieldOption_v_27
from globaleaks.db.migrations.update_29 import Context_v_28, Node_v_28
from globaleaks.db.migrations.update_30 import Node_v_29, Context_v_29, Step_v_29, FieldAnswer_v_29, \
    FieldAnswerGroup_v_29, FieldAnswerGroupFieldAnswer_v_29
from globaleaks.db.migrations.update_31 import Node_v_30, Context_v_30, User_v_30, ReceiverTip_v_30, Notification_v_30
from globaleaks.db.migrations.update_32 import Node_v_31, Comment_v_31, Message_v_31, User_v_31
from globaleaks.db.migrations.update_33 import Node_v_32, WhistleblowerTip_v_32, InternalTip_v_32, User_v_32
from globaleaks.db.migrations.update_34 import Node_v_33, Notification_v_33
from globaleaks.db.migrations.update_35 import Context_v_34, InternalTip_v_34, WhistleblowerTip_v_34
from globaleaks.db.migrations.update_38 import Field_v_37, Questionnaire_v_37
from globaleaks.db.migrations.update_39 import \
    Anomalies_v_38, ArchivedSchema_v_38, Comment_v_38, Config_v_38, ConfigL10N_v_38, \
    Context_v_38, Counter_v_38, CustomTexts_v_38, EnabledLanguage_v_38, \
    Field_v_38, FieldAnswer_v_38, FieldAnswerGroup_v_38, FieldAttr_v_38, \
    FieldOption_v_38, File_v_38, IdentityAccessRequest_v_38, \
    InternalFile_v_38, InternalTip_v_38, Mail_v_38, Message_v_38, \
    Questionnaire_v_38, Receiver_v_38, ReceiverContext_v_38, \
    ReceiverFile_v_38, ReceiverTip_v_38, ShortURL_v_38, Stats_v_38, \
    Step_v_38, User_v_38, WhistleblowerFile_v_38, WhistleblowerTip_v_38
from globaleaks.orm import make_db_uri
from globaleaks.models import config, l10n
from globaleaks.models.config import PrivateFactory
from globaleaks.settings import Settings
from globaleaks.utils.utility import log


migration_mapping = OrderedDict([
    ('Anomalies', [-1, -1, -1, -1, -1, -1, Anomalies_v_38, 0, 0, 0, 0, 0, 0, 0, 0, models.Anomalies]),
    ('ArchivedSchema', [ArchivedSchema_v_38, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, models.ArchivedSchema]),
    ('Comment', [Comment_v_31, 0, 0, 0, 0, 0, 0, 0, Comment_v_38, 0, 0, 0, 0, 0, 0, models.Comment]),
    ('Config', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, Config_v_38, 0, 0, 0, 0, config.Config]),
    ('ConfigL10N', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, ConfigL10N_v_38, 0, 0, 0, 0, l10n.ConfigL10N]),
    ('Context', [Context_v_26, 0, 0, Context_v_28, 0, Context_v_29, Context_v_30, Context_v_34, 0, 0, 0, Context_v_38, 0, 0, 0, models.Context]),
    ('ContextImg', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models.ContextImg]),
    ('Counter', [Counter_v_38, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, models.Counter]),
    ('CustomTexts', [-1, -1, -1, -1, -1, -1, -1, -1, CustomTexts_v_38, 0, 0, 0, 0, 0, 0, models.CustomTexts]),
    ('EnabledLanguage', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, EnabledLanguage_v_38, 0, 0, 0, 0, l10n.EnabledLanguage]),
    ('Field', [Field_v_27, 0, 0, 0, Field_v_37, 0, 0, 0, 0, 0, 0, 0, 0, 0, Field_v_38, models.Field]),
    ('FieldAnswer', [FieldAnswer_v_29, 0, 0, 0, 0, 0, FieldAnswer_v_38, 0, 0, 0, 0, 0, 0, 0, 0, models.FieldAnswer]),
    ('FieldAnswerGroup', [FieldAnswerGroup_v_29, 0, 0, 0, 0, 0, FieldAnswerGroup_v_38, 0, 0, 0, 0, 0, 0, 0, 0, models.FieldAnswerGroup]),
    ('FieldAnswerGroupFieldAnswer', [FieldAnswerGroupFieldAnswer_v_29, 0, 0, 0, 0, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]),
    ('FieldAttr', [FieldAttr_v_38, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, models.FieldAttr]),
    ('FieldField', [FieldField_v_27, 0, 0, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]),
    ('FieldOption', [FieldOption_v_27, 0, 0, 0, FieldOption_v_38, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, models.FieldOption]),
    ('File', [-1, -1, -1, -1, -1, -1, -1, File_v_38, 0, 0, 0, 0, 0, 0, 0, models.File]),
    ('IdentityAccessRequest', [IdentityAccessRequest_v_38, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, models.IdentityAccessRequest]),
    ('InternalFile', [InternalFile_v_25, 0, InternalFile_v_38, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, models.InternalFile]),
    ('InternalTip', [InternalTip_v_32, 0, 0, 0, 0, 0, 0, 0, 0, InternalTip_v_34, 0, InternalTip_v_38, 0, 0, 0, models.InternalTip]),
    ('Mail', [-1, -1, Mail_v_38, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, models.Mail]),
    ('Message', [Message_v_31, 0, 0, 0, 0, 0, 0, 0, Message_v_38, 0, 0, 0, 0, 0, 0, models.Message]),
    ('Node', [Node_v_26, 0, 0, Node_v_28, 0, Node_v_29, Node_v_30, Node_v_31, Node_v_32, Node_v_33, -1, -1, -1, -1, -1, -1]),
    ('Notification', [Notification_v_26, 0, 0, Notification_v_30, 0, 0, 0, Notification_v_33, 0, 0, -1, -1, -1, -1, -1, -1]),
    ('Questionnaire', [-1, -1, -1, -1, -1, -1, Questionnaire_v_37, 0, 0, 0, 0, 0, 0, 0, Questionnaire_v_38, models.Questionnaire]),
    ('Receiver', [Receiver_v_38, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, models.Receiver]),
    ('ReceiverContext', [ReceiverContext_v_38, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, models.ReceiverContext]),
    ('ReceiverFile', [ReceiverFile_v_38, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, models.ReceiverFile]),
    ('ReceiverTip', [ReceiverTip_v_30, 0, 0, 0, 0, 0, 0, ReceiverTip_v_38, 0, 0, 0, 0, 0, 0, 0, models.ReceiverTip]),
    ('SecureFileDelete', [models.SecureFileDelete, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('ShortURL', [-1, -1, ShortURL_v_38, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, models.ShortURL]),
    ('Stats', [Stats_v_38, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, models.Stats]),
    ('Step', [Step_v_27, 0, 0, 0, Step_v_29, 0, Step_v_38, 0, 0, 0, 0, 0, 0, 0, 0, models.Step]),
    ('StepField', [StepField_v_27, 0, 0, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]),
    ('Tenant', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models.Tenant]),
    ('User', [User_v_24, User_v_30, 0, 0, 0, 0, 0, User_v_31, User_v_32, User_v_38, 0, 0, 0, 0, 0, models.User]),
    ('UserImg', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models.UserImg]),
    ('WhistleblowerFile', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, WhistleblowerFile_v_38, 0, 0, 0, models.WhistleblowerFile]),
    ('WhistleblowerTip', [WhistleblowerTip_v_32, 0, 0, 0, 0, 0, 0, 0, 0, WhistleblowerTip_v_34, 0, WhistleblowerTip_v_38, 0, 0, 0, models.WhistleblowerTip])
])


def db_perform_data_update(store):
    prv = PrivateFactory(store, 1)

    stored_ver = prv.get_val(u'version')
    t = (stored_ver, __version__)

    if stored_ver != __version__:
        prv.set_val(u'version', __version__)

        # The below commands can change the current store based on the what is
        # currently stored in the DB.
        for tid in store.find(models.Tenant.id):
            appdata = load_appdata()
            db_update_defaults(store, tid)
            l10n.update_defaults(store, tid, appdata)
            config.update_defaults(store, tid)

        db_fix_fields_attrs(store)


def perform_data_update(db_file):
    store = Store(create_database(make_db_uri(db_file)))

    enabled_languages = [lang.name for lang in store.find(l10n.EnabledLanguage)]

    removed_languages = list(set(enabled_languages) - set(LANGUAGES_SUPPORTED_CODES))

    if removed_languages:
        removed_languages.sort()
        removed_languages = ', '.join(removed_languages)
        raise Exception("FATAL: cannot complete the upgrade because the support for some of the enabled languages is currently incomplete (%s)\n"
                        "Read about how to handle this condition at: https://github.com/globaleaks/GlobaLeaks/wiki/Upgrade-Guide#lang-drop" % removed_languages)


    try:
        db_perform_data_update(store)
        store.commit()
    except:
        store.rollback()
        raise
    finally:
        store.close()


def perform_schema_migration(version):
    """
    @param version:
    @return:
    """
    to_delete_on_fail = []
    to_delete_on_success = []

    if version < FIRST_DATABASE_VERSION_SUPPORTED:
        log.info("Migrations from DB version lower than %d are no longer supported!" % FIRST_DATABASE_VERSION_SUPPORTED)
        quit()

    tmpdir =  os.path.abspath(os.path.join(Settings.db_path, 'tmp'))
    orig_db_file = os.path.abspath(os.path.join(Settings.db_path, 'glbackend-%d.db' % version))
    final_db_file = os.path.abspath(os.path.join(Settings.db_path, 'glbackend-%d.db' % DATABASE_VERSION))

    shutil.rmtree(tmpdir, True)
    os.mkdir(tmpdir)
    shutil.copy2(orig_db_file, tmpdir)

    new_db_file = None

    try:
        while version < DATABASE_VERSION:
            old_db_file = os.path.abspath(os.path.join(tmpdir, 'glbackend-%d.db' % version))
            new_db_file = os.path.abspath(os.path.join(tmpdir, 'glbackend-%d.db' % (version + 1)))

            Settings.db_file = new_db_file
            Settings.enable_input_length_checks = False

            to_delete_on_fail.append(new_db_file)
            to_delete_on_success.append(old_db_file)

            log.info("Updating DB from version %d to version %d" % (version, version + 1))

            store_old = Store(create_database('sqlite:' + old_db_file))
            store_new = Store(create_database('sqlite:' + new_db_file))

            # Here is instanced the migration script
            MigrationModule = importlib.import_module("globaleaks.db.migrations.update_%d" % (version + 1))
            migration_script = MigrationModule.MigrationScript(migration_mapping, version, store_old, store_new)

            log.info("Migrating table:")

            try:
                try:
                    migration_script.prologue()
                except Exception as exception:
                    log.err("Failure while executing migration prologue: %s" % exception)
                    raise exception

                for model_name, _ in migration_mapping.items():
                    if migration_script.model_from[model_name] is not None and migration_script.model_to[model_name] is not None:
                        try:
                            migration_script.migrate_model(model_name)

                            # Commit at every table migration in order to be able to detect
                            # the precise migration that may fail.
                            migration_script.commit()
                        except Exception as exception:
                            log.err("Failure while migrating table %s: %s " % (model_name, exception))
                            raise exception
                try:
                    migration_script.epilogue()
                    migration_script.commit()
                except Exception as exception:
                    log.err("Failure while executing migration epilogue: %s " % exception)
                    raise exception

            finally:
                # the database should be always closed before leaving the application
                # in order to not keep leaking journal files.
                migration_script.close()

            log.info("Migration stats:")

            # we open a new db in order to verify integrity of the generated file
            store_verify = Store(create_database(make_db_uri(new_db_file)))

            for model_name, _ in migration_mapping.items():
                if migration_script.model_from[model_name] is not None and migration_script.model_to[model_name] is not None:
                     count = store_verify.find(migration_script.model_to[model_name]).count()
                     if migration_script.entries_count[model_name] != count:
                         if migration_script.fail_on_count_mismatch[model_name]:
                             raise AssertionError("Integrity check failed on count equality for table %s: %d != %d" % \
                                                  (model_name, count, migration_script.entries_count[model_name]))
                         else:
                             log.info(" * %s table migrated (entries count changed from %d to %d)" % \
                                                  (model_name, migration_script.entries_count[model_name], count))
                     else:
                         log.info(" * %s table migrated (%d entry(s))" % \
                                              (model_name, migration_script.entries_count[model_name]))

            version += 1

            store_verify.close()

        perform_data_update(new_db_file)

    except:
        raise

    else:
        # in case of success first copy the new migrated db, then as last action delete the original db file
        shutil.copy(new_db_file, final_db_file)
        security.overwrite_and_remove(orig_db_file)

    finally:
        # Always cleanup the temporary directory used for the migration
        for f in os.listdir(tmpdir):
            security.overwrite_and_remove(os.path.join(tmpdir, f))

        shutil.rmtree(tmpdir)
