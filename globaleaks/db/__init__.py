# -*- coding: UTF-8
#   GLBackend Database
#   ******************
from __future__ import with_statement
import os

from twisted.internet.defer import succeed
from storm.exceptions import OperationalError

from globaleaks.utils.utility import log
from globaleaks.settings import transact, ZStorm, GLSetting
from globaleaks import models
from globaleaks.db.datainit import initialize_node


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
            except OperationalError:
                log.err("OperationalError in [%s]" % create_query)

    init_models()
    # new is the only Models function executed without @transact, call .add, but
    # the called has to .commit and .close, operations commonly performed by decorator

def create_tables(create_node=True):
    """
    Override transactor for testing.
    """
    if os.path.exists(GLSetting.file_versioned_db.replace('sqlite:', '')):
        # Here we instance every model so that __storm_table__ gets set via
        # __new__
        for model in models.models:
            model()
        return succeed(None)

    deferred = create_tables_transaction()
    if create_node:

        log.debug("Node initialization with defaults values")

        only_node = {
            'name':  u"MissingConfLeaks",
            'description':  dict({ GLSetting.memory_copy.default_language:
                                       u"This is the description of your node. PLEASE CHANGE ME." }),
            'presentation':  dict({ GLSetting.memory_copy.default_language :
                                        u"Welcome to GlobaLeaks™" }),
            'footer': dict({ GLSetting.memory_copy.default_language :
                                 u"Copyright 2011-2013 Hermes Center for Transparency and Digital Human Rights" }),
            'hidden_service':  u"",
            'public_site':  u"",
            'email':  u"email@dumnmy.net",
            'stats_update_time':  2, # hours,
            # advanced settings
            'maximum_filesize' : GLSetting.defaults.maximum_filesize,
            'maximum_namesize' : GLSetting.defaults.maximum_namesize,
            'maximum_textsize' : GLSetting.defaults.maximum_textsize,
            'tor2web_admin' : GLSetting.defaults.tor2web_admin,
            'tor2web_submission' : GLSetting.defaults.tor2web_submission,
            'tor2web_tip' : GLSetting.defaults.tor2web_tip,
            'tor2web_receiver' : GLSetting.defaults.tor2web_receiver,
            'tor2web_unauth' : GLSetting.defaults.tor2web_unauth,
            'postpone_superpower' : False, # disabled by default
            'exception_email' : GLSetting.defaults.exception_email,
            'default_language' : GLSetting.memory_copy.default_language,
        }

        email_templates = {}

        tip_notif_templ= os.path.join(GLSetting.static_db_source, 'default_TNT.txt')
        if os.path.isfile(tip_notif_templ):
            with open( tip_notif_templ) as templfd:
                email_templates['tip'] = templfd.read()
        else:
            email_templates['tip'] = "default Tip notification not available! %NodeName% configure this!"

        comment_notif_templ= os.path.join(GLSetting.static_db_source, 'default_CNT.txt')
        if os.path.isfile(comment_notif_templ):
            with open( comment_notif_templ) as templfd:
                email_templates['comment'] = templfd.read()
        else:
            email_templates['comment'] = "default Comment notification not available! %NodeName% configure this!"

        file_notif_templ= os.path.join(GLSetting.static_db_source, 'default_FNT.txt')
        if os.path.isfile(file_notif_templ):
            with open(file_notif_templ) as templfd:
                email_templates['file'] = templfd.read()
        else:
            email_templates['file'] = "default File notification not available! %NodeName% configure this!"

        # Initialize the node + notification table
        deferred.addCallback(initialize_node, only_node, email_templates)

    return deferred


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
    db_file = GLSetting.file_versioned_db.replace('sqlite:', '')

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
        zstorm.set_default_uri(GLSetting.store_name, GLSetting.file_versioned_db)
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
