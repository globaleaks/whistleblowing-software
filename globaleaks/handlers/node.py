# -*- coding: UTF-8
#   node
#   ****
#
# Implementation of classes handling the HTTP request to /node, public
# exposed API.

from twisted.internet.defer import inlineCallbacks
from cyclone.web import asynchronous

from globaleaks.utils import log
from globaleaks.settings import transact
from globaleaks.handlers.base import BaseHandler
from globaleaks import models

@transact
def anon_serialize_node(store):
    node = store.find(models.Node).one()
    return {
      'name': unicode(node.name),
      'description': unicode(node.description),
      'hidden_service': unicode(node.hidden_service),
      'public_site': unicode(node.public_site),
      'email': unicode(node.email),
      'notification_settings': dict(node.notification_settings) or None,
}


class InfoCollection(BaseHandler):
    """
    U1
    Returns information on the GlobaLeaks node. This includes submission
    parameters (contexts description, fields, public receiver list).
    Contains System-wide properties.
    """

    def get(self, *uriargs):
        """
        Parameters: None
        Response: publicNodeDesc
        Errors: NodeNotFound
        """
        return anon_serialize_node()

# U2 Submission create
# U3 Submission update/status/delete
# U4 Files

class StatsCollection(BaseHandler):
    """
    U5
    Interface for the public statistics, configured between the Node settings and the
    Contexts settings
    """

    def get(self, *uriargs):
        """
        Parameters: None
        Response: publicStatsList
        Errors: StatsNotCollectedError

        This interface return the collected statistics for the public audience.
        """
        log.debug("[D] %s %s " % (__file__, __name__), "TO BE IMPLEMENTED", "get", uriargs)
        pass


class ContextsCollection(BaseHandler):
    """
    U6
    Return the public list of contexts, those information are shown in client
    and would be memorized in a third party indexer service. This is way some dates
    are returned within.
    """
    @transact
    def get_context_list(self, store):
        return [x.dict() for x in store.find(models.Context)]

    def get(self, *uriargs):
        """
        Parameters: None
        Response: publicContextList
        Errors: None
        """
        return self.get_context_list().addCallback(self.finish)


class ReceiversCollection(BaseHandler):
    """
    U7
    Return the description of all the receiver visible from the outside. A receiver is associated
    to one or more context, and is present in the "first tier" if a multi level review is configured.
    """

    @transact
    def get_receiver_list(self, store):
        return [x.dict() for x in Receiver(store).get_all()]

    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: publicReceiverList
        Errors: None
        """
        self.get_receiver_list().addCallback(self.finish)
