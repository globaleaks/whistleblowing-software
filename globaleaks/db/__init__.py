# -*- coding: UTF-8
#   GLBackend Database
#   ******************
from __future__ import with_statement
import os
import os.path

from twisted.internet.defer import succeed

from storm.zope.zstorm import ZStorm
from storm.exceptions import OperationalError

from globaleaks.utils import log, datetime_now
from globaleaks.settings import transact, GLSetting
from globaleaks import models
from globaleaks.third_party import rstr
from globaleaks.security import hash_password, get_salt

@transact
def initialize_node(store, results, only_node, email_template):
    """
    TODO refactor with languages the email_template, develop a dedicated
    function outside the node, and inquire fucking YHWH about the
    callbacks existence/usage
    """

    node = models.Node(only_node)
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
    notification.tip_template = email_template

    # defaults until software is not ready
    notification.server = u"box549.bluehost.com"
    notification.port = 25
    notification.username = u"sendaccount939@globaleaks.org"
    notification.password = u"sendaccount939"

    # It's the only NOT NULL variable with CHECK
    notification.security = u'TLS'
    # notification.security = models.Notification._security_types[0]

    # Those fields are sets as default in order to show to the Admin the various 'variables'
    # callable by template, with %KeyWord% format

    notification.tip_template = "Hi, in %NodeName%, in %ContextName%\n\n"\
                                "You (%ReceiverName%) had received in %EventTime%, a Tip!\n"\
                                "1) %TipTorURL%\n"\
                                "2) %TipT2WURL%\n\n"\
                                "Best."

    notification.file_template = "Hi, in %NodeName%, in %ContextName%\n\n"\
                                 "You (%ReceiverName%) had received in %EventTime%, a File!\n"\
                                 "is %FileName% (%FileSize%, %FileType%)\n"\
                                "Best."

    notification.comment_template = "Hi, in %NodeName%, in %ContextName%\n\n"\
                                    "You (%ReceiverName%) had received in %EventTime%, a Comment!\n"\
                                    "And is from %CommentSource%\n"\
                                    "Best."

    notification.activation_template = "*Not Yet implemented*"
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
        }

        # load notification template, ignored ATM
        emailfile = os.path.join(GLSetting.root_path, 'globaleaks', 'db', 'emailnotification_template')
        with open(emailfile) as f:
            email_template = f.read()

        # Initialize the node + notification table
        deferred.addCallback(initialize_node, only_node, email_template)
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
    if not os.path.exists(GLSetting.db_file.replace('sqlite:', '')):
        return True

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

    if comma_compare != comma_number:
        log.err("*********************************")
        log.err("Detected an invalid DB version.")
        log.err("You have to specify a different working_dir, or restartclean")
        log.err("Also, if the DB is changed, we suggest to update also the GlobaLeaks client")
        log.err("*********************************")
        ret = False

    store.close()

    return ret
