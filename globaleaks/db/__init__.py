# -*- coding: UTF-8
#   GLBackend Database
#   ******************
from __future__ import with_statement
import os.path

from twisted.internet.defer import succeed
from storm.exceptions import OperationalError

from globaleaks import settings
from globaleaks.utils import log
from globaleaks.settings import transact
from globaleaks import models

@transact
def initialize_node(store, results, onlyNode, emailtemplate):
    """
    TODO refactor with languages the emailtemplate, develop a dedicated
    function outside the node, and inquire fucking YHWH about the
    callbacks existence/usage
    """

    node = models.Node(onlyNode)
    # Add here by hand the languages supported!
    node.languages =  [{ "code" : "it" , "name": "Italiano"},
                       { "code" : "en" , "name" : "English" }]

    node.password = unicode("globaleaks")
    node.creation_date = models.now()
    store.add(node)

    notification = models.Notification()
    notification.tip_template = emailtemplate

    # defaults until software is not ready 
    notification.server = u"box549.bluehost.com"
    notification.port = 25
    notification.username = u"sendaccount939@globaleaks.org"
    notification.password = u"sendaccount939"

    # It's the only NOT NULL variable with CHECK
    notification.security = u'TLS'
    # notification.security = models.Notification._security_types[0]

    # Those fileds are set here to override the emailnotification_template, the goal is
    # show to the Admin the various 'variables'

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


def initModels():
    for model in models.models:
        model()
    return succeed(None)

@transact
def create_tables_transaction(store):
    """
    @return: None, create the right table at the first start, and initialized
    the node.
    """
    with open(settings.create_db_file) as f:
        create_queries = ''.join(f.readlines()).split(';')
        for create_query in create_queries:
            try:
                store.execute(create_query+';')
            except OperationalError, e:
                log.err("OperationalError in [%s]" % create_query)
                pass

    initModels()
    # new is the only Models function executed without @transact, call .add, but
    # the called has to .commit and .close, operations commonly performed by decorator

def createTables(create_node=True):
    """
    Override transactor for testing.
    """
    if os.path.exists(settings.db_file.replace('sqlite:', '')):
        print "Node already configured"
        # Here we instance every model so that __storm_table__ gets set via
        # __new__
        for model in models.models:
            model()
        return succeed(None)

    d = create_tables_transaction()
    if create_node:

        log.debug("Node initialization with dummy values")

        onlyNode = {
            'name':  u"MisingConfLeaks",
            'description':  u"Please, set me: description",
            'hidden_service':  u"",
            'public_site':  u"",
            'email':  u"email@dumnmy.net",
            'stats_update_time':  2, # hours,
        }

        # load notification template, ignored ATM
        emailfile = os.path.join(settings.root_path, 'globaleaks', 'db', 'emailnotification_template')
        with open(emailfile) as f:
            email_template = f.read()

        # Initialize the node + notification table
        d.addCallback(initialize_node, onlyNode, email_template)
    return d

