# -*- coding: UTF-8
#   node
#   ****
#
# Implementation of classes handling the HTTP request to /node, public
# exposed API.

from twisted.internet.defer import inlineCallbacks
from globaleaks.utils import log
from globaleaks.handlers.base import BaseHandler
from cyclone.web import asynchronous
from globaleaks.transactors.crudoperations import CrudOperations
from globaleaks.rest.errors import NodeNotFound

class InfoCollection(BaseHandler):
    """
    U1
    Returns information on the GlobaLeaks node. This includes submission
    parameters (contexts description, fields, public receiver list).
    Contains System-wide properties.
    """

    @asynchronous
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: publicNodeDesc
        Errors: NodeNotFound
        """

        try:
            answer = yield CrudOperations().get_node()
            # output filtering TODO need to strip reserved infos

            self.json_write(answer['data'])
            self.set_status(answer['code'])

        except NodeNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()

# U2 Submission create
# U3 Submission update/status/delete
# U4 Files

class StatsCollection(BaseHandler):
    """
    U5
    Interface for the public statistics, configured between the Node settings and the
    Contexts settings
    """

    @asynchronous
    @inlineCallbacks
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

    @asynchronous
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: publicContextList
        Errors: None
        """

        answer = yield CrudOperations().get_context_list()

        # output filtering TODO need to strip reserved infos
        self.json_write(answer['data'])
        self.set_status(answer['code'])

        self.finish()


class ReceiversCollection(BaseHandler):
    """
    U7
    Return the description of all the receiver visible from the outside. A receiver is associated
    to one or more context, and is present in the "first tier" if a multi level review is configured.
    """

    @asynchronous
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: publicReceiverList
        Errors: None
        """

        answer = yield CrudOperations().get_receiver_list()

        # output filtering TODO need to strip reserved infos
        self.json_write(answer['data'])
        self.set_status(answer['code'])

        self.finish()


