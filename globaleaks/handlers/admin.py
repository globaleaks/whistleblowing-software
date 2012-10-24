# -*- coding: UTF-8
#
#   admin
#   *****
#
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#

from globaleaks.handlers.base import BaseHandler
from globaleaks.models import node, admin
from globaleaks.utils import log
from cyclone.web import asynchronous
from twisted.internet.defer import inlineCallbacks

class AdminNode(BaseHandler):
    """
    A1
    Get the node main settings, update the node main settings, it works in a single static
    table, in models/admin.py
    """

    @asynchronous
    @inlineCallbacks
    def get(self, *uriargs):
        log.debug("[D] %s %s " % (__file__, __name__), "Class Admin Node", "get")

        context = admin.Context()
        context_description_dicts = yield context.list_description_dicts()

        node_info = node.Node()
        node_description_dicts = yield node_info.get_admin_info()

        # it's obviously a madness that need to be solved
        node_description_dicts.update({"contexts": context_description_dicts})

        self.write(node_description_dicts)
        self.finish()

    @asynchronous
    @inlineCallbacks
    def post(self, *uriargs):
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminNode", "post")
        pass


class AdminContexts(BaseHandler):

    log.debug("[D] %s %s " % (__file__, __name__), "Class AdminContexts", "BaseHandler", BaseHandler)
    # A2
    """
    classic CURD in the 'contexts'
    """
    def get(self, context_id):
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminContexts", "get")
        pass

    def post(self, context_id):
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminContexts", "post")
        pass

    def put(self, context_id):
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminContexts", "put")
        pass

    def delete(self, context_id):
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminContexts", "delete")
        pass


class AdminReceivers(BaseHandler):
    log.debug("[D] %s %s " % (__file__, __name__), "Class AdminReceivers", "BaseHandler", BaseHandler)
    # A3
    """
    classic CURD in the 'receivers'
    """
    def get(self, context_id):
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminReceivers", "get")
        pass

    def post(self, context_id):
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminReceivers", "post")
        pass

    def put(self, context_id):
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminReceivers", "put")
        pass

    def delete(self, context_id):
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminReceivers", "delete")
        pass


class AdminModules(BaseHandler):
    log.debug("[D] %s %s " % (__file__, __name__), "Class AdminModules", "BaseHandler", BaseHandler)
    # A4
    """
    A limited CURD (we've not creation|delete, just update, with
    maybe a flag that /disable/ a module)
    """
    def get(self, context_id, module_id):
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminModules", "get")
        pass

    def post(self, context_id, module_id):
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminModules", "post")
        pass
