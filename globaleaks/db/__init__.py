# -*- coding: UTF-8
#   GLBackend Database
#   ******************

from twisted.internet.defer import inlineCallbacks
from storm.twisted.transact import transact
from globaleaks.config import config
from globaleaks.db import tables
from globaleaks.utils import log

from globaleaks.models.context import Context
from globaleaks.models.externaltip import ReceiverTip, WhistleblowerTip, Comment, File
from globaleaks.models.internaltip import InternalTip
from globaleaks.models.receiver import Receiver
from globaleaks.models.submission import Submission
from globaleaks.models.node import Node

__all__ = ['createTables']

@inlineCallbacks
def createTables():
    """
    @return: None, create the right table at the first start, and initialized
    the node.
    """
    for model in [Node, Context, Receiver, InternalTip, ReceiverTip, WhistleblowerTip,
                  Submission, Comment, File]:
        createdTable = yield tables.createTable(model)

    if not createdTable:
        return

    # Initialize the node
    store = config.main.zstorm.get(config.store)
    onlyNode = {}

    onlyNode['name'] = u"Please, set me: name/title"
    onlyNode['description'] = u"Please, set me: description"
    onlyNode['hidden_service'] = u"Please, set me: hidden service"
    onlyNode['public_site'] = u"Please, set me: public site"
    onlyNode['email'] = u"email@dumnmy.net"
    onlyNode['stats_update_time'] = 2 # hours
    onlyNode['languages'] = [{ "code" : "it" , "name": "Italiano"},
                             { "code" : "en" , "name" : "English" }]

    node_created = Node(store).new(onlyNode)

    # new is the only Models function executed without @transact, call .add, but
    # the called has to .commit and .close, operations commonly performed by decorator
    store.commit()
    store.close()

