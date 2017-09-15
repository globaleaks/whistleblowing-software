# -*- coding: utf-8 -*-
import importlib
import os
import shutil
from collections import OrderedDict
from storm.database import create_database
from storm.store import Store

from globaleaks import __version__, models, DATABASE_VERSION, FIRST_DATABASE_VERSION_SUPPORTED, \
    LANGUAGES_SUPPORTED_CODES, security
from globaleaks.db.appdata import db_update_defaults, load_appdata
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
from globaleaks.models import config, l10n
from globaleaks.models.config import PrivateFactory
from globaleaks.settings import Settings
from globaleaks.utils.utility import log

XTIDX = 1


migration_mapping = OrderedDict([
    ('Anomalies', [-1, -1, -1, -1, -1, -1, models.Anomalies, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('ArchivedSchema', [models.ArchivedSchema, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('Comment', [Comment_v_31, 0, 0, 0, 0, 0, 0, 0, models.Comment, 0, 0, 0, 0, 0, 0]),
    ('Config', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, config.Config, 0, 0, 0, 0]),
    ('ConfigL10N', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, l10n.ConfigL10N, 0, 0, 0, 0]),
    ('Context', [Context_v_26, 0, 0, Context_v_28, 0, Context_v_29, Context_v_30, Context_v_34, 0, 0, 0, models.Context, 0, 0, 0]),
    ('Counter', [models.Counter, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('CustomTexts', [-1, -1, -1, -1, -1, -1, -1, -1, models.CustomTexts, 0, 0, 0, 0, 0, 0]),
    ('EnabledLanguage', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, l10n.EnabledLanguage, 0, 0, 0, 0]),
    ('Field', [Field_v_27, 0, 0, 0, Field_v_37, 0, 0, 0, 0, 0, 0, 0, 0, 0, models.Field]),
    ('FieldAnswer', [FieldAnswer_v_29, 0, 0, 0, 0, 0, models.FieldAnswer, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('FieldAnswerGroup', [FieldAnswerGroup_v_29, 0, 0, 0, 0, 0, models.FieldAnswerGroup, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('FieldAnswerGroupFieldAnswer', [FieldAnswerGroupFieldAnswer_v_29, 0, 0, 0, 0, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1]),
    ('FieldAttr', [models.FieldAttr, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('FieldField', [FieldField_v_27, 0, 0, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]),
    ('FieldOption', [FieldOption_v_27, 0, 0, 0, models.FieldOption, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('File', [-1, -1, -1, -1, -1, -1, -1, models.File, 0, 0, 0, 0, 0, 0, 0]),
    ('IdentityAccessRequest', [models.IdentityAccessRequest, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('InternalFile', [InternalFile_v_25, 0, models.InternalFile, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('InternalTip', [InternalTip_v_32, 0, 0, 0, 0, 0, 0, 0, 0, InternalTip_v_34, 0, models.InternalTip, 0, 0, 0]),
    ('Mail', [-1, -1, models.Mail, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('Message', [Message_v_31, 0, 0, 0, 0, 0, 0, 0, models.Message, 0, 0, 0, 0, 0, 0]),
    ('Node', [Node_v_26, 0, 0, Node_v_28, 0, Node_v_29, Node_v_30, Node_v_31, Node_v_32, Node_v_33, -1, -1, -1, -1, -1]),
    ('Notification', [Notification_v_26, 0, 0, Notification_v_30, 0, 0, 0, Notification_v_33, 0, 0, -1, -1, -1, -1, -1]),
    ('Questionnaire', [-1, -1, -1, -1, -1, -1, Questionnaire_v_37, 0, 0, 0, 0, 0, 0, 0, models.Questionnaire]),
    ('Receiver', [models.Receiver, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('ReceiverContext', [models.ReceiverContext, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('ReceiverFile', [models.ReceiverFile, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('ReceiverTip', [ReceiverTip_v_30, 0, 0, 0, 0, 0, 0, models.ReceiverTip, 0, 0, 0, 0, 0, 0, 0]),
    ('SecureFileDelete', [models.SecureFileDelete, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('ShortURL', [-1, -1, models.ShortURL, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('Step', [Step_v_27, 0, 0, 0, Step_v_29, 0, models.Step, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('StepField', [StepField_v_27, 0, 0, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]),
    ('Stats', [models.Stats, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ('User', [User_v_24, User_v_30, 0, 0, 0, 0, 0, User_v_31, User_v_32, models.User, 0, 0, 0, 0, 0]),
    ('WhistleblowerFile', [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, models.WhistleblowerFile, 0, 0, 0]),
    ('WhistleblowerTip', [WhistleblowerTip_v_32, 0, 0, 0, 0, 0, 0, 0, 0, WhistleblowerTip_v_34, 0, models.WhistleblowerTip, 0, 0, 0])
])


def db_perform_data_update(store):
    for tid in store.find(models.Tenant.id):
        prv = PrivateFactory(store, tid)

        stored_ver = prv.get_val(u'version')
        t = (stored_ver, __version__)

        if stored_ver != __version__:
            prv.set_val(u'version', __version__)

            # The below commands can change the current store based on the what is
            # currently stored in the DB.
            appdata = load_appdata()
            db_update_defaults(store, tid)
            l10n.update_defaults(store, tid, appdata)
            config.update_defaults(store, tid)

        ok = config.is_cfg_valid(store, tid)
        if not ok:
            m = 'Error: the system is not stable, update failed from %s to %s' % t
            raise Exception(m)


def perform_data_update(dbfile):
    store = Store(create_database(Settings.make_db_uri(dbfile)))

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
            store_verify = Store(create_database(Settings.make_db_uri(new_db_file)))

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

    except Exception:
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
