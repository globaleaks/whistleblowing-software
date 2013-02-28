# -*- coding: UTF-8
#   node
#   ****
#
# Implementation of classes handling the HTTP request to /node, public
# exposed API.

from twisted.internet.defer import inlineCallbacks
from cyclone.web import asynchronous

from globaleaks.utils import log
from globaleaks import utils
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
      'languages': list(node.languages or []),
    }

def serialize_context(context):
    context_dict = {
        "context_gus": unicode(context.id),
        "description": unicode(context.description),
        "escalation_threshold": None,
        "fields": list(context.fields or []),
        "file_max_download": int(context.file_max_download),
        "name": unicode(context.name),
        "receivers": [],
        "selectable_receiver": bool(context.selectable_receiver),
        "tip_max_access": int(context.tip_max_access),
        "tip_timetolive": int(context.tip_timetolive)
    }
    for receiver in context.receivers:
        context_dict['receivers'].append(unicode(receiver.id))
    return context_dict

def serialize_receiver(receiver):
    receiver_dict = {
        "can_delete_submission": receiver.can_delete_submission,
        "contexts": [],
        "creation_date": utils.prettyDateTime(receiver.creation_date),
        "update_date": utils.prettyDateTime(receiver.last_update),
        "description": receiver.description,
        "name": unicode(receiver.name),
        "receiver_gus": unicode(receiver.id),
        "receiver_level": int(receiver.receiver_level),
    }
    for context in receiver.contexts:
        receiver_dict['contexts'].append(unicode(context.id))
    return receiver_dict

class InfoCollection(BaseHandler):
    """
    U1
    Returns information on the GlobaLeaks node. This includes submission
    parameters (contexts description, fields, public receiver list).
    Contains System-wide properties.
    """

    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: publicNodeDesc
        Errors: NodeNotFound
        """
        response = yield anon_serialize_node()
        self.finish(response)

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

@transact
def get_public_context_list(store):
    context_list = []
    contexts = store.find(models.Context)
    for context in contexts:
        context_list.append(serialize_context(context))
    return context_list


class ContextsCollection(BaseHandler):
    """
    U6
    Return the public list of contexts, those information are shown in client
    and would be memorized in a third party indexer service. This is way some dates
    are returned within.
    """
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: publicContextList
        Errors: None
        """
        response = yield get_public_context_list()
        self.finish(response)

@transact
def get_public_receiver_list(store):
    receiver_list = []
    receivers = store.find(models.Receiver)
    for receiver in receivers:
        receiver_list.append(serialize_receiver(receiver))
    return receiver_list

class ReceiversCollection(BaseHandler):
    """
    U7
    Return the description of all the receiver visible from the outside. A receiver is associated
    to one or more context, and is present in the "first tier" if a multi level review is configured.
    """

    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: publicReceiverList
        Errors: None
        """
        response = yield get_public_receiver_list()
        self.finish(response)

