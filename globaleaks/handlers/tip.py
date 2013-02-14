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
from globaleaks import utils
from globaleaks.settings import transact
from globaleaks.models import now
from globaleaks.models import *
from globaleaks.rest.errors import InvalidTipAuthToken, InvalidInputFormat, ForbiddenOperation, \
    TipGusNotFound, TipReceiptNotFound, TipPertinenceExpressed


def actor_serialize_internal_tip(internaltip):

    itip_dict = {
        'context_id': unicode(internaltip.context.id),
        'creation_date' : unicode(utils.prettyDateTime(internaltip.creation_date)),
        'last_activity' : unicode(utils.prettyDateTime(internaltip.creation_date)),
        'expiration_date' : unicode(utils.prettyDateTime(internaltip.creation_date)),
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
        'creation_date' : unicode(utils.prettyDateTime(internalfile.creation_date)),
        'size': int(internalfile.size),
        'downloads': unicode(receiverfile.downloads)
    }
    return rfile_dict


def wb_serialize_file(internalfile):

    wb_file_desc = {
        'name' : unicode(internalfile.name),
        'sha2sum' : unicode(internalfile.sha2sum),
        'content_type' : unicode(internalfile.content_type),
        'size': int(internalfile.size),
    }
    return wb_file_desc


@transact
def get_folders_wb(store, receipt):

    wbtip = store.find(WhistleblowerTip, WhistleblowerTip.receipt == unicode(receipt)).one()

    folders_desc = []
    for internalfile in wbtip.internaltip.internalfiles:
        folders_desc.append(wb_serialize_file(internalfile))

    return folders_desc

@transact
def get_folders_receiver(store, tip_id):

    rtip = store.find(ReceiverTip, ReceiverTip.id == unicode(id)).one()

    files_list = []
    for receiverfile in rtip.receiver_files:
        internalfile = receiverfile.internal_file
        files_list.append(receiver_serialize_file(internalfile, receiverfile, tip_id))

    return files_list

def strong_receiver_validate(store, username, id):
    """
    Utility: TODO description
    """

    rtip = store.find(ReceiverTip, ReceiverTip.id == unicode(id)).one()

    if not rtip:
        raise TipGusNotFound

    receiver = store.find(Receiver, Receiver.username == unicode(username)).one()

    if receiver.id != rtip.receiver.id:
        # This in attack!!
        raise TipGusNotFound


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

    rtip = strong_receiver_validate(store, username, id)

    tip_desc = actor_serialize_internal_tip(rtip.internaltip)
    tip_desc['access_counter'] = int(rtip.access_counter)
    tip_desc['expressed_pertinence'] = int(rtip.expressed_pertinence)
    # tip_desc['notification_date'] =
    # tip_desc['last_access'] TODO

    return tip_desc


@transact
def delete_receiver_tip(store, username, id):

    rtip = strong_receiver_validate(store, username, id)
    store.delete(rtip)

@transact
def delete_internal_tip(store, username, id):

    rtip = strong_receiver_validate(store, username, id)
    store.delete(rtip.internaltip)


@transact
def manage_pertinence(store, username, id, vote):
    """
    Assign in ReceiverTip the expressed vote (checks if already present)
    Roll over all the rTips with a vote
    re-count the Overall Pertinence
    Assign the Overall Pertinence to the InternalTip
    """

    rtip = strong_receiver_validate(store, username, id)

    # expressed_pertinence has these meanings:
    # 0 = unassigned
    # 1 = negative vote
    # 2 = positive vote

    if not rtip.expressed_pertinence:
        raise TipPertinenceExpressed

    rtip.expressed_pertinence = 2 if vote else 1

    vote_sum = 0
    for rtip in rtip.internaltip.receivertips:
        if rtip.expressed_pertinence == 1:
            vote_sum -= 1
        else:
            vote_sum += 1

    rtip.internaltip.pertinence_counter = vote_sum



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

        # TODO move this operation within the auth decorator
        if self.is_whistleblower():
            raise ForbiddenOperation

        request = self.validate_message(self.request.body, requests.actorsTipOpsDesc)

        if request['personal_delete']:
            yield delete_receiver_tip(self.current_user['username'], tip_id)

        elif request['is_pertinent']:
            yield manage_pertinence(self.current_user['username'], tip_id, request['is_pertinent'])

        self.set_status(202) # Updated
        self.finish()

    @inlineCallbacks
    def delete(self, tip_id, *uriargs):
        """
        Request: None
        Response: None
        Errors: ForbiddenOperation, TipGusNotFound

        When an uber-receiver decide to "total delete" a Tip, is handled by this call.
        """

        # TODO move this operation within the auth decorator
        if self.is_whistleblower():
            raise ForbiddenOperation

        yield delete_internal_tip(self.current_user['username'], tip_id)

        self.set_status(200) # Success
        self.finish()



def actor_serialize_comment(comment):

    comment_desc = {
        'comment_id' : unicode(comment.id),
        'source' : unicode(comment.source),
        'content' : unicode(comment.content),
        'author_id' : unicode(comment.author_gus),
        'internaltip_id' : int(comment.internaltip_id),
        'creation_time' : unicode(utils.prettyDateTime(comment.creation_time))
    }
    return comment_desc


def get_comment_list(internaltip):
    """
    @param internaltip:
    This function is used by both Receiver and WB.
    """
    # TODO may supports parameters to handle comments range

    comment_list = []
    for comment in internaltip.comments:
        comment_list.append(actor_serialize_comment(comment))

    return comment_list

@transact
def get_comment_list_wb(receipt, id):

    wbtip = store.find(WhistleblowerTip, WhistleblowerTip.receipt == unicode(receipt)).one()

    if not wbtip:
        raise TipReceiptNotFound

    return get_comment_list(wbtip.internaltip)

@transact
def get_comment_list_receiver(store, username, id):

    rtip = strong_receiver_validate(store, username, id)
    return get_comment_list(rtip.internaltip)

@transact
def create_comment_wb(store, receipt, request):

    wbtip = store.find(WhistleblowerTip, WhistleblowerTip.receipt == unicode(receipt)).one()

    if not wbtip:
        raise TipReceiptNotFound

    request['internaltip_id'] = wbtip.internaltip.id
    request['author'] = u'whistleblower'

    comment = Comment(request)
    store.add(comment)

    return actor_serialize_comment(comment)

@transact
def create_comment_receiver(store, username, id, request):

    rtip = strong_receiver_validate(store, username, id)

    request['internaltip_id'] = rtip.internaltip.id
    request['author'] = rtip.receiver.name

    comment = Comment(request)
    store.add(comment)

    return actor_serialize_comment()


class TipCommentCollection(TipBaseHandler):
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

        if self.is_whistleblower():
            comment_list = yield get_comment_list_wb(self.current_user['password'], tip_id)
        else:
            comment_list = yield get_comment_list_receiver(self.current_user['username'], tip_id)

        self.set_status(200)
        self.finish(comment_list)

    @inlineCallbacks
    def post(self, tip_id, *uriargs):
        """
        Request: actorsCommentDesc
        Response: actorsCommentDesc
        Errors: InvalidTipAuthToken, InvalidInputFormat, TipGusNotFound, TipReceiptNotFound
        """

        request = self.validate_message(self.request.body, requests.actorsCommentDesc)

        if self.is_whistleblower():
            answer = yield create_comment_wb(self.current_user['password'], request)
        else:
            answer = yield create_comment_receiver(self.current_user['username'], tip_id, request)

        self.set_status(201) # Created
        self.finish(answer)


def public_serialize_receiver(receiver):

    pub_receiver_desc = {
        'name' : unicode(receiver.name),
        'description' : unicode(receiver.description),
    }

def get_receiver_itip(internaltip):
    """
    Having the InernalTip, after the right authorization, just loop for all
    the receiver associated.
    """

    pub_receiver_list = []
    for receiver in internaltip.receivers:
        pub_receiver_list.append(public_serialize_receiver(receiver))

    return pub_receiver_list

@transact
def get_receiver_wb(store, receipt, id):

    wbtip = store.find(WhistleblowerTip, WhistleblowerTip.receipt == unicode(receipt)).one()

    if not wbtip:
        raise TipReceiptNotFound

    return public_serialize_receiver(wbtip.internaltip.id)

@transact
def get_receiver_receiver(store, username, id):

    rtip = strong_receiver_validate(store, username, id)
    return public_serialize_receiver(rtip.internaltip.id)


class TipReceiversCollection(TipBaseHandler):
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

        if self.is_whistleblower():
            answer = yield get_receiver_wb(self.current_user['password'], tip_id)
        else:
            answer = yield get_receiver_receiver(self.current_user['username'], tip_id)

        self.set_status(200)
        self.finish(answer)

