# -*- coding: UTF-8
#   GLBackend Database
#   ******************

from twisted.internet.defer import inlineCallbacks
from storm.twisted.transact import transact
from globaleaks import settings
from globaleaks.db import tables
from globaleaks.utils import log

from globaleaks.models.context import Context
from globaleaks.models.externaltip import ReceiverTip, WhistleblowerTip, Comment, File
from globaleaks.models.internaltip import InternalTip
from globaleaks.models.receiver import Receiver
from globaleaks.models.submission import Submission
from globaleaks.models.node import Node

__all__ = ['createTables']

def initialize_node():
    # Initialize the node
    onlyNode = {
        'name':  u"Please, set me: name/title",
        'description':  u"Please, set me: description",
        'hidden_service':  u"Please, set me: hidden service",
        'public_site':  u"Please, set me: public site",
        'email':  u"email@dumnmy.net",
        'stats_update_time':  2, # hours,
        'languages':  [{ "code" : "it" , "name": "Italiano"},
                       { "code" : "en" , "name" : "English" }],
    }
    node_created = Node(store).new(onlyNode)

def create_tables_transaction():
    """
    @return: None, create the right table at the first start, and initialized
    the node.
    """
    store = settings.get_store()

    for model in [Node, Context, Receiver, InternalTip, ReceiverTip, WhistleblowerTip,
                  Submission, Comment, File]:
        create_query = tables.generateCreateQuery(model)
        store.execute(create_query)

    # new is the only Models function executed without @transact, call .add, but
    # the called has to .commit and .close, operations commonly performed by decorator
    try:
        store.commit()
    except StormError as e:
        log.msg(e)
    finally:
        store.close()

def createTables(transactor=None):
    """
    Override transactor for testing.
    """
    if not transactor:
        transactor = settings.config.main.transactor
    return transactor.run(create_tables_transaction)

