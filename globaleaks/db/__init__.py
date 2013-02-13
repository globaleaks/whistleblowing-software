# -*- coding: UTF-8
#   GLBackend Database
#   ******************
import transaction

from twisted.internet.defer import inlineCallbacks, DeferredList
from globaleaks import settings
from globaleaks.db import tables
from globaleaks.utils import log
from globaleaks.settings import transact

from globaleaks.models import Context, ReceiverTip, WhistleblowerTip
from globaleaks.models import Comment, InternalTip, Receiver, Node
from globaleaks.models import ReceiverFile, Folder, InternalFile

__all__ = ['createTables']

def initialize_node():
    store = settings.get_store()

    nodes = store.find(Node)
    if len(list(nodes)) == 0:
        log.debug('Initializing node with new config')
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
            'notification_settings': {},
            'password': u'globaleaks'
        }
        node_created = Node(store).new(onlyNode)
        store.commit()

    store.close()

def create_tables_transaction():
    """
    @return: None, create the right table at the first start, and initialized
    the node.
    """
    store = settings.get_store()
    for model in [Node, Context, ReceiverTip, WhistleblowerTip, Comment, InternalTip,
            Receiver, InternalFile, Folder]:
        create_query = tables.generateCreateQuery(model)
        store.execute(create_query)
    # new is the only Models function executed without @transact, call .add, but
    # the called has to .commit and .close, operations commonly performed by decorator
    try:
        store.commit()
    except StormError as e:
        log.msg(e)
        transaction.abort()
    finally:
        store.close()

@inlineCallbacks
def createTables(create_node=True):
    """
    Override transactor for testing.
    """
    try:
        yield transact.run(create_tables_transaction)
    except Exception, e:
        log.msg(e)

    if create_node:
        yield transact.run(initialize_node)

