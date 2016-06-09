# -*- coding: UTF-8
#
# rtip
# ****
#
# Contains all the logic for handling tip related operations, for the
# receiver side. These classes are executed in the /rtip/* URI PATH

import os

from twisted.internet.defer import inlineCallbacks

from globaleaks.orm import transact, transact_ro
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.custodian import serialize_identityaccessrequest
from globaleaks.handlers.submission import serialize_receiver_tip, db_get_rtip, \
    get_rtip
from globaleaks.models import Notification, Comment, Message, \
    ReceiverFile, ReceiverTip, InternalTip, ArchivedSchema, \
    SecureFileDelete, IdentityAccessRequest, ReceiverTip
from globaleaks.rest import errors, requests
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import log, utc_future_date, datetime_now, \
    datetime_to_ISO8601, datetime_to_pretty_str

def receiver_serialize_file(internalfile, receiverfile, receivertip_id):
    """
    ReceiverFile is the mixing between the metadata present in InternalFile
    and the Receiver-dependent, and for the client sake receivertip_id is
    required to create the download link
    """
    if receiverfile.status != 'unavailable':

        ret_dict = {
            'id': receiverfile.id,
            'internalfile_id': internalfile.id,
            'status': receiverfile.status,
            'href': "/rtip/" + receivertip_id + "/download/" + receiverfile.id,
            # if the ReceiverFile has encrypted status, we append ".pgp" to the filename, to avoid mistake on Receiver side.
            'name': ("%s.pgp" % internalfile.name) if receiverfile.status == u'encrypted' else internalfile.name,
            'content_type': internalfile.content_type,
            'creation_date': datetime_to_ISO8601(internalfile.creation_date),
            'size': receiverfile.size,
            'downloads': receiverfile.downloads
        }

    else:  # == 'unavailable' in this case internal file metadata is returned.

        ret_dict = {
            'id': receiverfile.id,
            'internalfile_id': internalfile.id,
            'status': 'unavailable',
            'href': "",
            'name': internalfile.name,  # original filename
            'content_type': internalfile.content_type,  # original content size
            'creation_date': datetime_to_ISO8601(internalfile.creation_date),  # original creation_date
            'size': int(internalfile.size),  # original filesize
            'downloads': unicode(receiverfile.downloads)  # this counter is always valid
        }

    return ret_dict

def serialize_comment(comment):
    if comment.type == 'whistleblower':
        author = 'Whistleblower'
    else:
        if comment.author is not None:
            author = comment.author.name
        else:
            author = 'Recipient'

    return {
        'id': comment.id,
        'author': author,
        'type': comment.type,
        'creation_date': datetime_to_ISO8601(comment.creation_date),
        'content': comment.content
    }


def serialize_message(msg):
    return {
        'id': msg.id,
        'author': msg.receivertip.receiver.user.name,
        'type': msg.type,
        'creation_date': datetime_to_ISO8601(msg.creation_date),
        'content': msg.content
    }


def db_mark_file_for_secure_deletion(store, relpath):
    abspath = os.path.join(GLSettings.submission_path, relpath)
    if os.path.isfile(abspath):
        secure_file_delete = SecureFileDelete()
        secure_file_delete.filepath = abspath
        store.add(secure_file_delete)


def db_delete_itip_files(store, itip):
    log.debug("Removing files associated to InternalTip %s" % itip.id)
    for ifile in itip.internalfiles:
        log.debug("Marking internalfile %s for secure deletion" % ifile.file_path)

        db_mark_file_for_secure_deletion(store, ifile.file_path)

        for rfile in store.find(ReceiverFile, ReceiverFile.internalfile_id == ifile.id):
            # The following code must be bypassed if rfile.file_path == ifile.filepath,
            # this mean that is referenced the plaintext file instead having E2E.
            if rfile.file_path == ifile.file_path:
                continue

            log.debug("Marking receiverfile %s for secure deletion" % rfile.file_path)

            db_mark_file_for_secure_deletion(store, rfile.file_path)


def db_delete_itip(store, itip):
    log.debug("Removing InternalTip %s" % itip.id)

    db_delete_itip_files(store, itip)

    store.remove(itip)

    if store.find(InternalTip, InternalTip.questionnaire_hash == itip.questionnaire_hash).count() == 0:
        store.find(ArchivedSchema, ArchivedSchema.hash == itip.questionnaire_hash).remove()


def db_delete_itips(store, itips):
    for itip in itips:
        db_delete_itip_files(store, itip)

    itips.remove()


def db_delete_rtip(store, rtip):
    return db_delete_itip(store, rtip.internaltip)


def db_postpone_expiration_date(rtip):
    rtip.internaltip.expiration_date = \
        utc_future_date(seconds=rtip.internaltip.context.tip_timetolive)


def db_get_itip_receiver_list(store, itip, language):
    return [{
        "id": rtip.receiver.id,
        "name": rtip.receiver.user.name,
        "last_access": datetime_to_ISO8601(rtip.last_access),
        "access_counter": rtip.access_counter,
    } for rtip in itip.receivertips]


@transact_ro
def get_receiver_list(store, user_id, rtip_id, language):
    rtip = db_get_rtip(store, user_id, rtip_id)

    return db_get_itip_receiver_list(store, rtip.internaltip, language)


@transact
def delete_rtip(store, user_id, rtip_id):
    """
    Delete internalTip is possible only to Receiver with
    the dedicated property.
    """
    rtip = db_get_rtip(store, user_id, rtip_id)

    if not (GLSettings.memory_copy.can_delete_submission or
                rtip.receiver.can_delete_submission):
        raise errors.ForbiddenOperation

    db_delete_rtip(store, rtip)


@transact
def postpone_expiration_date(store, user_id, rtip_id):
    rtip = db_get_rtip(store, user_id, rtip_id)

    if not (GLSettings.memory_copy.can_postpone_expiration or
                rtip.receiver.can_postpone_expiration):

        raise errors.ExtendTipLifeNotEnabled

    log.debug("Postpone check: Node %s, Receiver %s" % (
       "True" if GLSettings.memory_copy.can_postpone_expiration else "False",
       "True" if rtip.receiver.can_postpone_expiration else "False"
    ))

    db_postpone_expiration_date(rtip)

    log.debug(" [%s] in %s has postponed expiration time to %s" % (
        rtip.receiver.user.name,
        datetime_to_pretty_str(datetime_now()),
        datetime_to_pretty_str(rtip.internaltip.expiration_date)))


@transact
def set_internaltip_variable(store, user_id, rtip_id, key, value):
    rtip = db_get_rtip(store, user_id, rtip_id)

    if not (GLSettings.memory_copy.can_grant_permissions or
            rtip.receiver.can_grant_permissions):
        raise errors.ForbiddenOperation

    setattr(rtip.internaltip, key, value)


@transact
def set_receivertip_variable(store, user_id, rtip_id, key, value):
    rtip = db_get_rtip(store, user_id, rtip_id)
    setattr(rtip, key, value)


def db_get_comment_list(rtip):
    return [serialize_comment(comment) for comment in rtip.internaltip.comments]


@transact_ro
def get_comment_list(store, user_id, rtip_id):
    rtip = db_get_rtip(store, user_id, rtip_id)

    return db_get_comment_list(rtip)


@transact
def create_identityaccessrequest(store, user_id, rtip_id, request, language):
    rtip = db_get_rtip(store, user_id, rtip_id)

    iar = IdentityAccessRequest()
    iar.request_motivation = request['request_motivation']
    iar.receivertip_id = rtip.id
    store.add(iar)

    return serialize_identityaccessrequest(iar, language)


@transact
def create_comment(store, user_id, rtip_id, request):
    rtip = db_get_rtip(store, user_id, rtip_id)
    rtip.internaltip.update_date = datetime_now()

    comment = Comment()
    comment.content = request['content']
    comment.internaltip_id = rtip.internaltip.id
    comment.type = u'receiver'
    comment.author = rtip.receiver.user.id

    rtip.internaltip.comments.add(comment)

    return serialize_comment(comment)


def db_get_message_list(rtip):
    return [serialize_message(message) for message in rtip.messages]


@transact_ro
def get_message_list(store, user_id, rtip_id):
    rtip = db_get_rtip(store, user_id, rtip_id)

    return db_get_message_list(rtip)


@transact
def create_message(store, user_id, rtip_id, request):
    rtip = db_get_rtip(store, user_id, rtip_id)
    rtip.internaltip.update_date = datetime_now()

    msg = Message()
    msg.content = request['content']
    msg.receivertip_id = rtip.id
    msg.type = u'receiver'

    store.add(msg)

    return serialize_message(msg)


@transact_ro
def get_identityaccessrequest_list(store, user_id, rtip_id, language):
    rtip = db_get_rtip(store, user_id, rtip_id)

    iars = store.find(IdentityAccessRequest, IdentityAccessRequest.receivertip_id == rtip.id)

    return [serialize_identityaccessrequest(iar, language) for iar in iars]


class RTipInstance(BaseHandler):
    """
    This interface exposes the Receiver's Tip
    """
    @BaseHandler.transport_security_check('receiver')
    @BaseHandler.authenticated('receiver')
    @inlineCallbacks
    def get(self, tip_id):
        """
        Parameters: None
        Response: actorsTipDesc
        Errors: InvalidAuthentication

        tip_id can be a valid tip_id (Receiver case) or a random one (because is
        ignored, only authenticated user with whistleblower token can access to
        the wbtip, this is why tip_is is not checked if self.is_whistleblower)

        This method is decorated as @BaseHandler.unauthenticated because in the handler
        the various cases are managed differently.
        """

        answer = yield get_rtip(self.current_user.user_id, tip_id, self.request.language)

        self.write(answer)

    @BaseHandler.transport_security_check('receiver')
    @BaseHandler.authenticated('receiver')
    @inlineCallbacks
    def put(self, tip_id):
        """
        Some special operations that manipulate a Tip are handled here
        """
        request = self.validate_message(self.request.body, requests.TipOpsDesc)

        if request['operation'] == 'postpone':
            yield postpone_expiration_date(self.current_user.user_id, tip_id)
        elif request['operation'] == 'set':
            key = request['args']['key']
            value = request['args']['value']
            internal_var_lst = ['enable_two_way_comments', 
                                'enable_two_way_messages', 
                                'enable_attachments'] 
            if key == 'label' and isinstance(value, unicode):
                set_receivertip_variable(self.current_user.user_id, tip_id, key, value)
            elif key == 'enable_notifications' and isinstance(value, bool):
                set_receivertip_variable(self.current_user.user_id, tip_id, key, value)
            elif key in internal_var_lst and isinstance(value, bool):
                # Elements of internal_var_lst are not stored in the receiver's tip table
                set_internaltip_variable(self.current_user.user_id, tip_id, key, value)

        # TODO A 202 is returned regardless of whether or not an update was performed.
        self.set_status(202)  # Updated

    @BaseHandler.transport_security_check('receiver')
    @BaseHandler.authenticated('receiver')
    @inlineCallbacks
    def delete(self, tip_id):
        """
        Response: None
        Errors: ForbiddenOperation, TipIdNotFound

        delete: remove the Internaltip and all the associated data
        """
        yield delete_rtip(self.current_user.user_id, tip_id)


class RTipCommentCollection(BaseHandler):
    """
    Interface use to read/write comments inside of a Tip, is not implemented as CRUD because we've not
    needs, at the moment, to delete/update comments once has been published. Comments is intended, now,
    as a stone written consideration about Tip reliability, therefore no editing and rethinking is
    permitted.
    """
    @BaseHandler.transport_security_check('receiver')
    @BaseHandler.authenticated('receiver')
    @inlineCallbacks
    def get(self, tip_id):
        """
        Parameters: None
        Response: actorsCommentList
        Errors: InvalidAuthentication
        """
        comment_list = yield get_comment_list(self.current_user.user_id, tip_id)

        self.write(comment_list)

    @BaseHandler.transport_security_check('receiver')
    @BaseHandler.authenticated('receiver')
    @inlineCallbacks
    def post(self, tip_id):
        """
        Request: CommentDesc
        Response: CommentDesc
        Errors: InvalidAuthentication, InvalidInputFormat, TipIdNotFound, TipReceiptNotFound
        """
        request = self.validate_message(self.request.body, requests.CommentDesc)

        answer = yield create_comment(self.current_user.user_id, tip_id, request)

        self.set_status(201)  # Created
        self.write(answer)


class RTipReceiversCollection(BaseHandler):
    """
    This interface return the list of the Receiver active in a Tip.
    GET /tip/<auth_tip_id>/receivers
    """
    @BaseHandler.transport_security_check('receiver')
    @BaseHandler.authenticated('receiver')
    @inlineCallbacks
    def get(self, rtip_id):
        """
        Parameters: None
        Response: actorsReceiverList
        Errors: InvalidAuthentication
        """
        answer = yield get_receiver_list(self.current_user.user_id, rtip_id, self.request.language)

        self.write(answer)


class ReceiverMsgCollection(BaseHandler):
    """
    This interface return the lists of the private messages exchanged.
    """
    @BaseHandler.transport_security_check('receiver')
    @BaseHandler.authenticated('receiver')
    @inlineCallbacks
    def get(self, tip_id):
        answer = yield get_message_list(self.current_user.user_id, tip_id)

        self.write(answer)

    @BaseHandler.transport_security_check('receiver')
    @BaseHandler.authenticated('receiver')
    @inlineCallbacks
    def post(self, tip_id):
        """
        Request: CommentDesc
        Response: CommentDesc
        Errors: InvalidAuthentication, InvalidInputFormat, TipIdNotFound, TipReceiptNotFound
        """
        request = self.validate_message(self.request.body, requests.CommentDesc)

        message = yield create_message(self.current_user.user_id, tip_id, request)

        self.set_status(201)  # Created
        self.write(message)


class IdentityAccessRequestsCollection(BaseHandler):
    """
    This interface return the list of identity access requests performed
    on the tip and allow to perform new ones.
    """

    @BaseHandler.transport_security_check('receiver')
    @BaseHandler.authenticated('receiver')
    @inlineCallbacks
    def get(self, tip_id):
        """
        Response: identityaccessrequestsList
        Errors: InvalidAuthentication
        """
        answer = yield get_identityaccessrequest_list(self.current_user.user_id,
                                                      tip_id,
                                                      self.request.language)

        self.write(answer)

    @BaseHandler.transport_security_check('receiver')
    @BaseHandler.authenticated('receiver')
    @inlineCallbacks
    def post(self, tip_id):
        """
        Request: IdentityAccessRequestDesc
        Response: IdentityAccessRequestDesc
        Errors: IdentityAccessRequestIdNotFound, InvalidInputFormat, InvalidAuthentication
        """
        request = self.validate_message(self.request.body, requests.ReceiverIdentityAccessRequestDesc)

        identityaccessrequest = yield create_identityaccessrequest(self.current_user.user_id,
                                                                   tip_id,
                                                                   request,
                                                                   self.request.language)

        self.set_status(201)
        self.write(identityaccessrequest)
