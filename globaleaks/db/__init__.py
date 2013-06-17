# -*- coding: UTF-8
#   GLBackend Database
#   ******************
from __future__ import with_statement
import os
import os.path

from twisted.internet.defer import succeed

from storm.exceptions import OperationalError

from globaleaks.utils import log, datetime_now
from globaleaks.settings import transact, ZStorm, GLSetting
from globaleaks import models
from globaleaks.third_party import rstr
from globaleaks.security import hash_password, get_salt

@transact
def initialize_node(store, results, only_node, email_templates):
    """
    TODO refactor with languages the email_template, develop a dedicated
    function outside the node, and inquire fucking YHWH about the
    callbacks existence/usage
    """
    node = models.Node(only_node)

    # This is hardcoded here, at the moment
    node.database_version = 1

    # Add here by hand the languages supported!
    node.languages =  [{ "code" : "it" , "name": "Italiano"},
                       { "code" : "en" , "name" : "English" }]

    # Salt for admin password is a safe random string different in every Node.
    node.salt = get_salt(rstr.xeger('[A-Za-z0-9]{56}'))
    node.password = hash_password(u"globaleaks", node.salt)

    node.receipt_salt = get_salt(rstr.xeger('[A-Za-z0-9]{56}'))

    node.creation_date = datetime_now()
    store.add(node)

    notification = models.Notification()

    # our defaults for free, because we're like Gandhi of the mail accounts.
    notification.server = u"mail.headstrong.de"
    notification.port = 587
    notification.username = u"sendaccount@lists.globaleaks.org"
    notification.password = u"sendaccount99"
    notification.security = models.Notification._security_types[0] # TLS

    # Those fields are sets as default in order to show to the Admin the various 'variables'
    # used in the template.
    notification.tip_template = email_templates['tip']
    notification.tip_mail_title = "From %ContextName% a new Tip in %EventTime%"
    notification.file_template = email_templates['file']
    notification.file_mail_title = "From %ContextName% a new file appended in a tip (%EventTime%, %FileType%)"
    notification.comment_template = email_templates['comment']
    notification.comment_mail_title = "From %ContextName% a new comment in %EventTime%"

    notification.activation_template = "*Not Yet implemented*"
    notification.activation_mail_title = "TODO"

    store.add(notification)


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
    if os.path.exists(GLSetting.db_file.replace('sqlite:', '')):
        # Here we instance every model so that __storm_table__ gets set via
        # __new__
        for model in models.models:
            model()
        return succeed(None)

    deferred = create_tables_transaction()
    if create_node:

        log.debug("Node initialization with dummy values")

        only_node = {
            'name':  u"MissingConfLeaks",
            'description':  u"Please, set me: description",
            'hidden_service':  u"",
            'public_site':  u"",
            'email':  u"email@dumnmy.net",
            'stats_update_time':  2, # hours,
            # advanced settings
            'maximum_descsize' : GLSetting.defaults.maximum_descsize,
            'maximum_filesize' : GLSetting.defaults.maximum_filesize,
            'maximum_namesize' : GLSetting.defaults.maximum_namesize,
            'maximum_textsize' : GLSetting.defaults.maximum_textsize,
            'tor2web_admin' : GLSetting.defaults.tor2web_admin,
            'tor2web_submission' : GLSetting.defaults.tor2web_submission,
            'tor2web_tip' : GLSetting.defaults.tor2web_tip,
            'tor2web_receiver' : GLSetting.defaults.tor2web_receiver,
            'tor2web_unauth' : GLSetting.defaults.tor2web_unauth,
            'exception_email' : GLSetting.defaults.exception_email,
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
    db_file = GLSetting.db_file.replace('sqlite:', '')

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
        zstorm.set_default_uri(GLSetting.store_name, GLSetting.db_file)
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


@transact
def import_memory_variables(store):
    """
    to get fast checks, import (same) of the Node variable in  GLSetting,
    this function is called every time that Node is updated.
    """
    node = store.find(models.Node).one()

    GLSetting.memory_copy.maximum_filesize = node.maximum_filesize
    GLSetting.memory_copy.maximum_namesize = node.maximum_namesize
    GLSetting.memory_copy.maximum_descsize = node.maximum_descsize
    GLSetting.memory_copy.maximum_textsize = node.maximum_textsize

    GLSetting.memory_copy.tor2web_admin = node.tor2web_admin
    GLSetting.memory_copy.tor2web_submission = node.tor2web_submission
    GLSetting.memory_copy.tor2web_tip = node.tor2web_tip
    GLSetting.memory_copy.tor2web_receiver = node.tor2web_receiver
    GLSetting.memory_copy.tor2web_unauth = node.tor2web_unauth

    GLSetting.memory_copy.exception_email = node.exception_email


