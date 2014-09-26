# -*- coding: UTF-8
#   GLBackend Database
#   ******************
from __future__ import with_statement
import os
import sys
import traceback

from twisted.internet.defer import succeed, inlineCallbacks
from storm.exceptions import OperationalError

from globaleaks.utils.utility import log
from globaleaks.settings import transact, transact_ro, ZStorm, GLSetting
from globaleaks import models
from globaleaks.db import updater_manager
from globaleaks.db.datainit import initialize_node, opportunistic_appdata_init

def init_models():
    for model in models.models:
        model()
    return succeed(None)

@transact
def create_tables_transaction(store):
    """
    @return: None, create the right table at the first start, and initialized
    the node.
    """
    if not os.access(GLSetting.db_schema_file, os.R_OK):
        log.err("Unable to access %s" % GLSetting.db_schema_file)
        raise Exception("Unable to access db schema file")

    with open(GLSetting.db_schema_file) as f:
        create_queries = ''.join(f.readlines()).split(';')
        for create_query in create_queries:
            try:
                store.execute(create_query+';')
            except OperationalError as exc:
                log.err("OperationalError in [%s]" % create_query)
                log.err(exc)

    init_models()
    # new is the only Models function executed without @transact, call .add, but
    # the called has to .commit and .close, operations commonly performed by decorator

def acquire_email_templates(filename, fallback):

    templ_f = os.path.join(GLSetting.static_db_source, filename)

    if not os.path.isfile(templ_f):
        return fallback

    # else, load from the .txt files
    with open( templ_f) as templfd:
        template_text = templfd.read()
        log.info("Loading %d bytes from template: %s" % (len(template_text), filename))
        return template_text

def create_tables(create_node=True):
    """
    Override transactor for testing.
    """
    if GLSetting.db_type == 'sqlite':
        db_path = GLSetting.db_uri.replace('sqlite:', '').split('?', 1)[0]
        if os.path.exists(db_path):
            return succeed(None)

    deferred = create_tables_transaction()
    if create_node:

        log.debug("Node initialization with defaults values")

        only_node = {
            'name':  u"",
            'description':  dict({ GLSetting.memory_copy.default_language: u"" }),
            'presentation':  dict({ GLSetting.memory_copy.default_language: u"" }),
            'footer':  dict({ GLSetting.memory_copy.default_language: u"" }),
            'subtitle':  dict({ GLSetting.memory_copy.default_language: u"" }),
            'terms_and_conditions':  dict({ GLSetting.memory_copy.default_language: u"" }),
            'hidden_service':  u"",
            'public_site':  u"",
            'email':  u"",
            'receipt_regexp': u"[0-9]{16}",
            'stats_update_time':  2, # hours,
            # advanced settings
            'maximum_filesize' : GLSetting.defaults.maximum_filesize,
            'maximum_namesize' : GLSetting.defaults.maximum_namesize,
            'maximum_textsize' : GLSetting.defaults.maximum_textsize,
            'tor2web_admin' : GLSetting.defaults.tor2web_admin,
            'tor2web_submission' : GLSetting.defaults.tor2web_submission,
            'tor2web_receiver' : GLSetting.defaults.tor2web_receiver,
            'tor2web_unauth' : GLSetting.defaults.tor2web_unauth,
            'postpone_superpower' : False, # disabled by default
            'can_delete_submission' : False, # disabled too
            'ahmia' : False, # disabled too
            'anomaly_checks' : False, # need to disabled in this stage as it need to be tuned
            'allow_unencrypted': GLSetting.memory_copy.allow_unencrypted,
            'exception_email' : GLSetting.defaults.exception_email,
            'default_language' : GLSetting.memory_copy.default_language,
        }

        templates = {}

        templates['encrypted_tip'] = acquire_email_templates('default_ETNT.txt',
            "default Encrypted Tip notification not available! %NodeName% configure this!")
        templates['plaintext_tip'] = acquire_email_templates('default_PTNT.txt',
            "default Plaintext Tip notification not available! %NodeName% configure this!")

        templates['encrypted_comment'] = acquire_email_templates('default_ECNT.txt',
            "default Encrypted Comment notification not available! %NodeName% configure this!")
        templates['plaintext_comment'] = acquire_email_templates('default_PCNT.txt',
            "default Plaintext Comment notification not available! %NodeName% configure this!")

        templates['encrypted_message'] = acquire_email_templates('default_EMNT.txt',
             "default Encrypted Message notification not available! %NodeName% configure this!")
        templates['plaintext_message'] = acquire_email_templates('default_PMNT.txt',
             "default Plaintext Message notification not available! %NodeName% configure this!")

        templates['encrypted_file'] = acquire_email_templates('default_EFNT.txt',
            "default Encrypted File notification not available! %NodeName% configure this!")
        templates['plaintext_file'] = acquire_email_templates('default_PFNT.txt',
            "default Plaintext File notification not available! %NodeName% configure this!")

        # This specific template do not need different threatment as it is used to write some
        # data inside zip files.
        templates['zip_collection'] = acquire_email_templates('default_ZCT.txt',
            "default Zip Collection template not available! %NodeName% configure this!")

        appdata_dict = opportunistic_appdata_init()
        # here is ok!

        # Initialize the node + notification table
        deferred.addCallback(initialize_node, only_node, templates, appdata_dict)

    return deferred


def find_current_db_version(dirpath, filearray):

    glbackend_file_present = 0
    for single_file in filearray:

        # -journal file may remain if GLB crashes badly
        if single_file.endswith('-journal'):
            print "Found a DB journal file! %s: removing" % single_file
            try:
                os.unlink(os.path.join(dirpath, single_file))
                continue
            except Exception as excep:
                print "Unable to remove %s: %s" % \
                      (os.unlink(os.path.join(dirpath, single_file)), excep)
                # this would lead quitting for "too much DBs" below

        if single_file[:len('glbackend')] == 'glbackend':
            glbackend_file_present += 1

    if glbackend_file_present == 0:
        print "glbackend database file not found in %s" % dirpath
        raise StandardError
    elif glbackend_file_present > 1:
        print "glbackend database file found more than 1! keep only the latest in %s" % dirpath
        raise AssertionError

    for single_file in filearray:
        abspath = os.path.join(dirpath, single_file)

        if abspath[-3:] == '.db':

            nameindex = abspath.rfind('glbackend')
            extensindex = abspath.rfind('.db')

            if nameindex + len('glbackend') == extensindex:
                detected_version = 0
            else:
                detected_version = int(
                    abspath[nameindex+len('glbackend-'):extensindex])

            return detected_version, abspath

def check_db_files():
    """
    This function checks the DB version and executes eventually the DB update scripts
    """
    for (path, dirs, files) in os.walk(GLSetting.gldb_path):

        try:
            starting_ver, abspath = find_current_db_version(path, files)

            if starting_ver < GLSetting.db_version:
                print "Performing update of Database from version %d to version %d" %\
                      (starting_ver, GLSetting.db_version)
                try:
                    updater_manager.perform_version_update(starting_ver, GLSetting.db_version, abspath)
                    print "GlobaLeaks database version %d: update complete!" % GLSetting.db_version
                except Exception as excep:
                    print "GlobaLeaks database version %d: update failure :(" % GLSetting.db_version
                    print "Verbose exception traceback:"
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    traceback.print_tb(exc_traceback)
                    quit(-1)

                print "Database version detected: %d" % GLSetting.db_version

        except AssertionError:
            print "Error: More than one database file has been found in %s" % path
            quit(-1)
        except StandardError:
            continue

def check_schema_version():
    """
    @return: True of che version is the same, False if the
        sqlite.sql describe a different schema of the one found
        in the DB.

    ok ok, this is a dirty check. I'm counting the number of
    *comma* (,) inside the SQL just to check if a new column
    has been added. This would help if an incorrect DB version
    is used. For sure there are other better checks, but not
    today.
    """

    db_file = GLSetting.db_uri

    if GLSetting.db_type == 'sqlite':
        db_file = GLSetting.db_uri.replace('sqlite:', '')

        if not os.path.exists(db_file):
            return True

    if not os.access(GLSetting.db_schema_file, os.R_OK):
        log.err("Unable to access %s" % GLSetting.db_schema_file)
        return False
    else:
        ret = True

        with open(GLSetting.db_schema_file) as f:
            sqlfile = f.readlines()
            comma_number = "".join(sqlfile).count(',')

        zstorm = ZStorm()
        db_uri = GLSetting.db_uri.replace("?foreign_keys=O", "")
        zstorm.set_default_uri(GLSetting.store_name, db_uri)
        store = zstorm.get(GLSetting.store_name)

        q = """
            SELECT name, type, sql
            FROM sqlite_master
            WHERE sql NOT NULL AND type == 'table'
            """

        res = store.execute(q)

        comma_compare = 0
        for table in res:
            if len(table) == 3:
                comma_compare += table[2].count(',')

        if not comma_compare:
            log.err("Found an empty database (%s)" % db_file)
            ret = False

        elif comma_compare != comma_number:
            log.err("Detected an invalid DB version (%s)" %  db_file)
            log.err("You have to specify a different workingdir (-w) or to upgrade the DB")
            ret = False

        store.close()

    return ret


@transact_ro
def get_tracked_files(store):
    """
    returns a list the basenames of files tracked by InternalFile and ReceiverFile.
    """
    ifiles = list(store.find(models.InternalFile).values(models.InternalFile.file_path))
    rfiles = list(store.find(models.ReceiverFile).values(models.ReceiverFile.file_path))

    tracked_files = list()
    for files in list(set(ifiles + rfiles)):
        tracked_files.append(os.path.basename(files))

    return tracked_files

@inlineCallbacks
def clean_untracked_files(res):
    """
    removes files in GLSetting.submission_path that are not
    tracked by InternalFile/ReceiverFile.
    """
    tracked_files = yield get_tracked_files()
    for filesystem_file in os.listdir(GLSetting.submission_path):
        if filesystem_file not in tracked_files:
            file_to_remove = os.path.join(GLSetting.submission_path, filesystem_file)
            try:
                os.remove(file_to_remove)
            except OSError as e:
                log.err("Failed to remove untracked file" % file_to_remove)
