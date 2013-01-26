# -*- coding: UTF-8
#   GLBackend Database
#   ******************

__all__ = ['createTables']

from twisted.internet.defer import inlineCallbacks
from globaleaks import main
from globaleaks.config import config
from globaleaks.db import tables
from globaleaks.utils import log

from globaleaks.models.context import Context
from globaleaks.models.externaltip import ReceiverTip, WhistleblowerTip, Comment, File
from globaleaks.models.internaltip import InternalTip
from globaleaks.models.receiver import Receiver
from globaleaks.models.options import PluginProfiles, ReceiverConfs
from globaleaks.models.submission import Submission
from globaleaks.models.node import Node

@inlineCallbacks
def createTables():
    """
    @return: None, create the right table at the first start, and initialized
    the node.
    """
    for model in [ Node, Context, Receiver, InternalTip, ReceiverTip, WhistleblowerTip,
                    Submission, Comment, File, PluginProfiles, ReceiverConfs ]:

        yield tables.createTable(model)

def initializeNode():
    """
    This function is called only one time in a node life, and initialize
    the table. the configure_node run edit of this row (id = 1)
    This is not a @transact but is a white fly for this reason.
    """
    store = config.main.zstorm.get('main_store')

    onlyNode = Node()

    onlyNode.name = u"Please, set me: name/title"
    onlyNode.description = u"Please, set me: description"
    onlyNode.hidden_service = u"Please, set me: hidden service"
    onlyNode.public_site = u"Please, set me: public site"
    onlyNode.email = u"email@dumnmy.net"
    onlyNode.stats_update_time = 2 # hours
    onlyNode.languages = [ { "code" : "it" , "name": "Italiano"}, { "code" : "en" , "name" : "English" }]

    store.add(onlyNode)
