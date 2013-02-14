# -*- coding: UTF-8
#   GLBackend Database
#   ******************
from __future__ import with_statement
import os.path

from twisted.internet.defer import inlineCallbacks, DeferredList, succeed
from globaleaks import settings
from globaleaks.db import tables
from globaleaks.utils import log
from globaleaks.settings import transact
from globaleaks import models

@transact
def initialize_node(store, result, onlyNode):
    nodes = store.find(models.Node)
    # assert len(list(nodes)) == 0
    store.add(models.Node(onlyNode))

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
            store.execute(create_query+';')
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
        # load notification template
        emailfile = os.path.join(settings.root_path, 'globaleaks', 'db', 'emailnotification_template')
        onlyNode = {
            'name':  u"Please, set me: name/title",
            'description':  u"Please, set me: description",
            'hidden_service':  u"Please, set me: hidden service",
            'public_site':  u"Please, set me: public site",
            'email':  u"email@dumnmy.net",
            'stats_update_time':  2, # hours,
            'languages':  [{ "code" : "it" , "name": "Italiano"},
                           { "code" : "en" , "name" : "English" }],
            'notification_settings': {},
            'password': u'globaleaks',
            'creation_date': models.now(),
        }
        with open(emailfile) as f:
            onlyNode['notification_settings']['email_template'] = f.read()

        log.debug('Initializing node with new config')
        # Initialize the node
        d.addCallback(initialize_node, onlyNode)
    return d

