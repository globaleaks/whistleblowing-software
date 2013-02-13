# -*- coding: UTF-8
#
#   tip
#   ***
#
#   Contains all the logic for handling tip related operations, handled and
#   executed with /tip/* URI PATH interaction.

from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.base import BaseHandler
from globaleaks.rest import requests
from globaleaks.utils import gltime
from globaleaks.settings import transact
from globaleaks.models import update_model, now
from globaleaks.models import WhistleblowerTip, ReceiverTip, InternalFile, ReceiverFile, Folder, InternalTip, Receiver
from globaleaks.rest.errors import InvalidTipAuthToken, InvalidInputFormat, ForbiddenOperation, \
    TipGusNotFound, TipReceiptNotFound, TipPertinenceExpressed


def actor_serialize_internal_tip(internaltip):

    itip_dict = {
        'context_id': unicode(internaltip.context.id),
        'creation_date' : unicode(gltime.prettyDateTime(internaltip.creation_date)),
        'last_activity' : unicode(gltime.prettyDateTime(internaltip.creation_date)),
        'expiration_date' : unicode(gltime.prettyDateTime(internaltip.creation_date)),
        'download_limit' : int(internaltip.download_limit),
        'access_limit' : int(internaltip.access_limit),
        'mark' : unicode(internaltip.mark),
        'pertinence' : unicode(internaltip.pertinence_counter),
        'escalation_threshold' : unicode(internaltip.escalation_threshold),
        'fields' : dict(internaltip.fields),
        'folders' : []
    }

    return itip_dict

def receiver_serialize_file(internalfile, receiverfile, receivertip_id):
    """
    ReceiverFile is the mixing between the metadata present in InternalFile
    and the Receiver-dependent, and for the client sake receivertip_id is
    required to create the download link
    """

    rfile_dict = {
        'href' : unicode("/tip/" + receivertip_id + "/download/" + receiverfile.id),
        'name' : unicode(internalfile.name),
        'sha2sum' : unicode(receiverfile.sha2sum),
        'content_type' : unicode(internalfile.content_type),
        'creation_date' : unicode(gltime.prettyDateTime(internalfile.creation_date)),
        'size': int(internalfile.size),
        'downloads': unicode(receiverfile.downloads)
    }
    return rfile_dict


def actor_serialize_folder(folder):

    folder_dict = {
        'description' : unicode(folder.description),
        'files' : []
        # TODO creation date
    }

    for internalfile in folder.files:
        folder_dict['files'].append(unicode(internalfile.name))
        # ??? type/date are useful for the WB ?

    return folder_dict

@transact
def get_folders_wb(store, receipt):

    wbtip = store.find(WhistleblowerTip, WhistleblowerTip.receipt == unicode(receipt)).one()

    folders_desc = []
    for folder in wbtip.internaltip.folders:
        folders_desc.append(actor_serialize_folder(folder))

    return folders_desc

@transact
def get_folders_receiver(store, tip_id):

    rtip = store.find(ReceiverTip, ReceiverTip.id == unicode(id)).one()

    folders_desc = []
    for folder in rtip.internaltip.folders:

        single_folder = actor_serialize_folder(folder)
        single_folder['files'] = []

        for receiverfile in rtip.receiver_files:
            internalfile = receiverfile.internal_file
            single_folder['files'].append(folder receiver_serialize_file(internalfile, receiverfile, tip_id))

        folders_desc.append(single_folder)

    return folders_desc

@transact
def get_internaltip_wb(store, receipt):

    wbtip = store.find(WhistleblowerTip, WhistleblowerTip.receipt == unicode(receipt)).one()

    if not wbtip:
        raise TipReceiptNotFound

    tip_desc = actor_serialize_internal_tip(wbtip.internaltip)
    tip_desc['access_counter'] = int(wbtip.access_counter)
    # tip_desc['last_access'] TODO

    # Return a couple of value because WB needs them separately
    return tip_desc, unicode(wbtip.id)

@transact
def get_internaltip_receiver(store, id, username):

    rtip = store.find(ReceiverTip, ReceiverTip.id == unicode(id)).one()

    if not rtip:
        raise TipGusNotFound

    receiver = store.find(Receiver, Receiver.username == unicode(username)).one()

    if receiver.id != rtip.receiver.id:
        # This in attack!!
        raise TipGusNotFound

    tip_desc = actor_serialize_internal_tip(rtip.internaltip)
    tip_desc['access_counter'] = int(rtip.access_counter)
    tip_desc['expressed_pertinence'] = int(rtip.expressed_pertinence)
    # tip_desc['notification_date'] =
    # tip_desc['last_access'] TODO

    return tip_desc


class TipBaseHandler(BaseHandler):

    def is_whistleblower(self):

        if self.current_user['role'] == 'wb':
            return True
        else:
            return False


class TipInstance(TipBaseHandler):
    """
    T1
    This interface expose the Tip.

    Tip is the safe area, created with an expiration time, where Receivers (and optionally)
    Whistleblower can discuss about the submission, comments, collaborative voting, forward,
    promote, and perform other operation in this closed environment.
    In the request is present an unique token, aim to authenticate the users accessing to the
    resource, and giving accountability in resource accesses.
    Some limitation in access, security extensions an special token can exists, implemented by
    the extensions plugins.

    /tip/<tip_id>/
    tip_id is either a receiver_tip_gus or a whistleblower auth token
    """

    @inlineCallbacks
    def get(self, tip_id, *uriargs):
        """
        Parameters: None
        Response: actorsTipDesc
        Errors: InvalidTipAuthToken

        tip_id can be: a tip_gus for a receiver, or a WhistleBlower receipt, understand
        the format, help in addressing which kind of Tip need to be handled.
        """

        if self.is_whistleblower():
            (answer, internaltip_id) = yield get_internaltip_wb(self.current_user['password'])
            answer['folder'] = yield get_folders_wb(self.current_user['password'], internaltip_id)
        else:
            answer = yield get_internaltip_receiver(tip_id, self.current_user['username'])
            answer['folder'] = yield get_folders_receiver(self.current_user['username'], tip_id)

        self.set_status(200)
        self.finish(answer)

    @inlineCallbacks
    def put(self, tip_id, *uriargs):
        """
        Request: actorsTipOpsDesc
        Response: None
        Errors: InvalidTipAuthToken, InvalidInputFormat, ForbiddenOperation

        This interface modify some tip status value. pertinence, personal delete are handled here.
        Total delete operation is handled in this class, by the DELETE HTTP method.
        Those operations (may) trigger a 'system comment' inside of the Tip comment list.

        This interface return None, because may execute a delete operation. The client
        know which kind of operation has been requested. If a pertinence vote, would
        perform a refresh on get() API, if a delete, would bring the user in other places.
        """


        # Until whistleblowers has not right to perform Tip operations...
        if not is_receiver_token(tip_id):
            raise ForbiddenOperation

        request = self.validate_message(self.request.body, requests.actorsTipOpsDesc)
        answer = yield CrudOperations().update_tip_by_receiver(tip_id, request)

        self.set_status(answer['code'])

        if answer.has_key('data'):
            self.finish(answer['data'])
        else:
            self.finish()

    @inlineCallbacks
    def delete(self, tip_id, *uriargs):
        """
        Request: None
        Response: None
        Errors: ForbiddenOperation, TipGusNotFound

        When an uber-receiver decide to "total delete" a Tip, is handled by this call.
        """
        # This until WB can't Total delete the Tip!
        if not is_receiver_token(tip_id):
            raise ForbiddenOperation

        answer = yield CrudOperations().delete_tip(tip_id)

        self.set_status(answer['code'])
        self.finish()

class TipCommentCollection(BaseHandler):
    """
    T2
    Interface use to read/write comments inside of a Tip, is not implemented as CRUD because we've not
    needs, at the moment, to delete/update comments once has been published. Comments is intended, now,
    as a stone written consideration about Tip reliability, therefore no editing and rethinking is
    permitted.
    """

    @inlineCallbacks
    def get(self, tip_id, *uriargs):
        """
        Parameters: None (TODO start/end, date)
        Response: actorsCommentList
        Errors: InvalidTipAuthToken
        """

        if is_receiver_token(tip_id):
            answer = yield CrudOperations().get_comment_list_by_receiver(tip_id)
        else:
            answer = yield CrudOperations().get_comment_list_by_wb(tip_id)

        self.set_status(answer['code'])
        self.finish(answer['data'])

    @inlineCallbacks
    def post(self, tip_id, *uriargs):
        """
        Request: actorsCommentDesc
        Response: actorsCommentDesc
        Errors: InvalidTipAuthToken, InvalidInputFormat, TipGusNotFound, TipReceiptNotFound
        """

        request = self.validate_message(self.request.body, requests.actorsCommentDesc)

        if is_receiver_token(tip_id):
            answer = yield CrudOperations().new_comment_by_receiver(tip_id, request)
        else:
            answer = yield CrudOperations().new_comment_by_wb(tip_id, request)

        self.set_status(answer['code'])
        self.finish(answer['data'])

class TipReceiversCollection(BaseHandler):
    """
    T3
    This interface return the list of the Receiver active in a Tip.
    GET /tip/<auth_tip_id>/receivers
    """

    @inlineCallbacks
    def get(self, tip_id, *uriargs):
        """
        Parameters: None
        Response: actorsReceiverList
        Errors: InvalidTipAuthToken
        """

        if is_receiver_token(tip_id):
            answer = yield CrudOperations().get_receiver_list_by_receiver(tip_id)
        else:
            answer = yield CrudOperations().get_receiver_list_by_wb(tip_id)

        self.set_status(answer['code'])
        self.finish(answer['data'])

