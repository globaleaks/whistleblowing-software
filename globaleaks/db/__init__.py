# -*- coding: UTF-8
#   GLBackend Database
#   ******************


__all__ = ['createTables', 'database', 'transactor']

from twisted.internet.defer import inlineCallbacks
from globaleaks import transactor
from globaleaks.utils import log
from globaleaks.db import tables

@inlineCallbacks
def createTables():
    """
    @return: None, create the right table at the first start, and initialized
    the node.
    """
    from globaleaks.models.context import Context
    from globaleaks.models.externaltip import ReceiverTip, WhistleblowerTip, Comment, File
    from globaleaks.models.internaltip import InternalTip
    from globaleaks.models.receiver import Receiver
    from globaleaks.models.options import PluginProfiles, ReceiverConfs
    from globaleaks.models.submission import Submission
    from globaleaks.models.node import Node

    for model in [ Node, Context, Receiver, InternalTip, ReceiverTip, WhistleblowerTip, Submission,
               Comment, File, PluginProfiles, ReceiverConfs ]:
        try:
            log.debug("Creating %s" % model)
            yield tables.runCreateTable(model, transactor)
        except Exception, e:
            log.debug(str(e))

    nod = Node()
    is_only_one = yield nod.only_one()

    if False == is_only_one:
        yield nod.initialize_node()
        # no more verbose debugging
        # initvals = yield nod.get_admin_info()
        # print "Node initialized with", initvals
