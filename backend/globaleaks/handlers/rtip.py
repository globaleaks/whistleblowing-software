# -*- coding: UTF-8
#
# rtip
# ****
#
# Contains all the logic for handling tip related operations, for the
# receiver side. These classes are executed in the /rtip/* URI PATH

import os

from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import transport_security_check, authenticated
from globaleaks.handlers.custodian import serialize_identityaccessrequest
from globaleaks.handlers.submission import serialize_usertip
from globaleaks.models import Notification, Comment, Message, \
    ReceiverFile, ReceiverTip, EventLogs,  InternalTip, ArchivedSchema, \
    SecureFileDelete, IdentityAccessRequest
from globaleaks.rest import errors, requests
from globaleaks.settings import transact, transact_ro, GLSettings
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
            'ifile_id': internalfile.id,
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
            'ifile_id': internalfile.id,
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
    return {
        'id': comment.id,
        'author': comment.author,
        'type': comment.type,
        'creation_date': datetime_to_ISO8601(comment.creation_date),
        'content': comment.content
    }


def serialize_message(msg):
    return {
        'id': msg.id,
        'author': msg.author,
        'type': msg.type,
        'creation_date': datetime_to_ISO8601(msg.creation_date),
        'content': msg.content,
        'visualized': msg.visualized
    }


def db_access_rtip(store, user_id, rtip_id):
    rtip = store.find(ReceiverTip, ReceiverTip.id == unicode(rtip_id),
                      ReceiverTip.receiver_id == user_id).one()

    if not rtip:
        raise errors.TipIdNotFound

    return rtip


def db_get_files_receiver(store, user_id, rtip_id):
    rtip = db_access_rtip(store, user_id, rtip_id)

    receiver_files = store.find(ReceiverFile,
                                (ReceiverFile.internaltip_id == rtip.internaltip_id,
                                 ReceiverFile.receiver_id == rtip.receiver_id))

    return [receiver_serialize_file(receiverfile.internalfile, receiverfile, rtip_id)
            for receiverfile in receiver_files]


def db_get_rtip(store, user_id, rtip_id, language):
    rtip = db_access_rtip(store, user_id, rtip_id)

    db_increment_receiver_access_count(store, user_id, rtip_id)

    notif = store.find(Notification).one()

    if not notif.send_email_for_every_event:
        # If Receiver is accessing this Tip, Events related can be removed before
        # Notification is sent. This is a Twitter/Facebook -like behavior.
        store.find(EventLogs, EventLogs.receivertip_id == rtip_id).remove()
        # Note - before the check was:
        # store.find(EventLogs, And(EventLogs.receivertip_id == rtip_id,
        #                          EventLogs.mail_sent == True)).remove()

    tip_desc = serialize_usertip(store, rtip, language)

    tip_desc['receiver_id'] = user_id
    tip_desc['label'] = rtip.label
    tip_desc['collection'] = '/rtip/' + rtip_id + '/collection'
    tip_desc['files'] = db_get_files_receiver(store, user_id, rtip_id)

    return tip_desc


def db_increment_receiver_access_count(store, user_id, rtip_id):
    rtip = db_access_rtip(store, user_id, rtip_id)

    rtip.access_counter += 1
    rtip.last_access = datetime_now()

    log.debug("Tip %s access granted to user %s (%d)" %
              (rtip.id, rtip.receiver.user.name, rtip.access_counter))

    return rtip.access_counter


def db_delete_itip(store, itip):
    for ifile in itip.internalfiles:
        abspath = os.path.join(GLSettings.submission_path, ifile.file_path)

        if os.path.isfile(abspath):
            log.debug("Marking internalfile %s for secure deletion" % abspath)
            secure_file_delete = SecureFileDelete()
            secure_file_delete.filepath = abspath
            store.add(secure_file_delete)

        rfiles = store.find(ReceiverFile, ReceiverFile.internalfile_id == ifile.id)
        for rfile in rfiles:
            # The following code must be bypassed if rfile.file_path == ifile.filepath,
            # this mean that is referenced the plaintext file instead having E2E.
            if rfile.file_path == ifile.file_path:
                continue

            abspath = os.path.join(GLSettings.submission_path, rfile.file_path)

            if os.path.isfile(abspath):
                log.debug("Marking receiverfile %s for secure deletion" % abspath)
                secure_file_delete = SecureFileDelete()
                secure_file_delete.filepath = abspath
                store.add(secure_file_delete)

        log.debug("Removing InternalTip %s" % itip.id)

    store.remove(itip)

    if store.find(InternalTip, InternalTip.questionnaire_hash == itip.questionnaire_hash).count() == 0:
        store.find(ArchivedSchema, ArchivedSchema.hash == itip.questionnaire_hash).remove()


def db_delete_rtip(store, rtip):
    return db_delete_itip(store, rtip.internaltip)


def db_postpone_expiration_date(rtip):
    rtip.internaltip.expiration_date = \
        utc_future_date(seconds=rtip.internaltip.context.tip_timetolive)


@transact
def delete_rtip(store, user_id, rtip_id):
    """
    Delete internalTip is possible only to Receiver with
    the dedicated property.
    """
    rtip = db_access_rtip(store, user_id, rtip_id)

    if not (GLSettings.memory_copy.can_delete_submission or
                rtip.receiver.can_delete_submission):
        raise errors.ForbiddenOperation

    db_delete_rtip(store, rtip)


@transact
def postpone_expiration_date(store, user_id, rtip_id):
    rtip = db_access_rtip(store, user_id, rtip_id)

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
def assign_rtip_label(store, user_id, rtip_id, label_content):
    rtip = db_access_rtip(store, user_id, rtip_id)
    if rtip.label:
        log.debug("Updating ReceiverTip label from '%s' to '%s'" % (rtip.label, label_content))
    else:
        log.debug("Assigning ReceiverTip label '%s'" % label_content)
    rtip.label = unicode(label_content)


@transact
def get_rtip(store, user_id, rtip_id, language):
    return db_get_rtip(store, user_id, rtip_id, language)


@transact_ro
def get_comment_list_receiver(store, user_id, rtip_id):
    rtip = db_access_rtip(store, user_id, rtip_id)

    comment_list = []
    for comment in rtip.internaltip.comments:
        comment_list.append(serialize_comment(comment))

    return comment_list

@transact
def create_identityaccessrequest(store, user_id, rtip_id, request, language):
    rtip = db_access_rtip(store, user_id, rtip_id)

    iar = IdentityAccessRequest()
    iar.request_motivation = request['request_motivation']
    iar.receivertip_id = rtip.id
    store.add(iar)

    return serialize_identityaccessrequest(iar, language)


@transact
def create_comment_receiver(store, user_id, rtip_id, request):
    rtip = db_access_rtip(store, user_id, rtip_id)
    rtip.internaltip.update_update = datetime_now()

    comment = Comment()
    comment.content = request['content']
    comment.internaltip_id = rtip.internaltip.id
    comment.author = rtip.receiver.user.name
    comment.type = u'receiver'

    rtip.internaltip.comments.add(comment)

    return serialize_comment(comment)


@transact
def get_messages_list(store, user_id, rtip_id):
    rtip = db_access_rtip(store, user_id, rtip_id)

    content_list = []
    for msg in rtip.messages:
        content_list.append(serialize_message(msg))

        if not msg.visualized and msg.type == u'whistleblower':
            log.debug("Marking as read message [%s] from %s" % (msg.content, msg.author))
            msg.visualized = True

    return content_list


@transact
def create_message_receiver(store, user_id, rtip_id, request):
    rtip = db_access_rtip(store, user_id, rtip_id)

    msg = Message()
    msg.content = request['content']
    msg.receivertip_id = rtip.id
    msg.author = rtip.receiver.user.name
    msg.visualized = False
    msg.type = u'receiver'

    store.add(msg)

    return serialize_message(msg)


@transact
def get_identityaccessrequests_list(store, user_id, rtip_id, language):
    rtip = db_access_rtip(store, user_id, rtip_id)

    iars = store.find(IdentityAccessRequest, IdentityAccessRequest.receivertip_id == rtip.id)

    return [serialize_identityaccessrequest(iar, language) for iar in iars]


class RTipInstance(BaseHandler):
    """
    This interface expose the Receiver Tip
    """

    @transport_security_check('receiver')
    @authenticated('receiver')
    @inlineCallbacks
    def get(self, tip_id):
        """
        Parameters: None
        Response: actorsTipDesc
        Errors: InvalidAuthentication

        tip_id can be a valid tip_id (Receiver case) or a random one (because is
        ignored, only authenticated user with whistleblower token can access to
        the wbtip, this is why tip_is is not checked if self.is_whistleblower)

        This method is decorated as @unauthenticated because in the handler
        the various cases are managed differently.
        """

        answer = yield get_rtip(self.current_user.user_id, tip_id, 'en')

        self.set_status(200)
        self.finish(answer)

    @transport_security_check('receiver')
    @authenticated('receiver')
    @inlineCallbacks
    def put(self, tip_id):
        """
        Some special operation over the Tip are handled here
        """
        request = self.validate_message(self.request.body, requests.TipOpsDesc)

        if request['operation'] == 'postpone':
            yield postpone_expiration_date(self.current_user.user_id, tip_id)
        if request['operation'] == 'label':
            yield assign_rtip_label(self.current_user.user_id, tip_id, request['label'])

        self.set_status(202)  # Updated
        self.finish()

    @transport_security_check('receiver')
    @authenticated('receiver')
    @inlineCallbacks
    def delete(self, tip_id):
        """
        Response: None
        Errors: ForbiddenOperation, TipIdNotFound

        delete: remove the Internaltip and all the associated data
        """
        yield delete_rtip(self.current_user.user_id, tip_id)

        self.set_status(200)  # Success
        self.finish()


class RTipCommentCollection(BaseHandler):
    """
    Interface use to read/write comments inside of a Tip, is not implemented as CRUD because we've not
    needs, at the moment, to delete/update comments once has been published. Comments is intended, now,
    as a stone written consideration about Tip reliability, therefore no editing and rethinking is
    permitted.
    """

    @transport_security_check('receiver')
    @authenticated('receiver')
    @inlineCallbacks
    def get(self, tip_id):
        """
        Parameters: None
        Response: actorsCommentList
        Errors: InvalidAuthentication
        """
        comment_list = yield get_comment_list_receiver(self.current_user.user_id, tip_id)

        self.set_status(200)
        self.finish(comment_list)

    @transport_security_check('receiver')
    @authenticated('receiver')
    @inlineCallbacks
    def post(self, tip_id):
        """
        Request: CommentDesc
        Response: CommentDesc
        Errors: InvalidAuthentication, InvalidInputFormat, TipIdNotFound, TipReceiptNotFound
        """
        request = self.validate_message(self.request.body, requests.CommentDesc)

        answer = yield create_comment_receiver(self.current_user.user_id, tip_id, request)

        self.set_status(201)  # Created
        self.finish(answer)


def db_get_itip_receivers_list(store, itip, language):
    receivers_list = []

    for rtip in itip.receivertips:
        receivers_list.append({
            "id": rtip.receiver.id,
            "name": rtip.receiver.user.name,
            "last_access": datetime_to_ISO8601(rtip.last_access),
            "access_counter": rtip.access_counter,
        })

    return receivers_list


@transact_ro
def get_rtip_receivers_list(store, user_id, rtip_id, language):
    rtip = db_access_rtip(store, user_id, rtip_id)

    return db_get_itip_receivers_list(store, rtip.internaltip, language)


class RTipReceiversCollection(BaseHandler):
    """
    This interface return the list of the Receiver active in a Tip.
    GET /tip/<auth_tip_id>/receivers
    """

    @transport_security_check('receiver')
    @authenticated('receiver')
    @inlineCallbacks
    def get(self, rtip_id):
        """
        Parameters: None
        Response: actorsReceiverList
        Errors: InvalidAuthentication
        """
        answer = yield get_rtip_receivers_list(self.current_user.user_id, rtip_id, self.request.language)

        self.set_status(200)
        self.finish(answer)


class ReceiverMsgCollection(BaseHandler):
    """
    This interface return the lists of the private messages exchanged.
    """
    @transport_security_check('receiver')
    @authenticated('receiver')
    @inlineCallbacks
    def get(self, tip_id):
        answer = yield get_messages_list(self.current_user.user_id, tip_id)

        self.set_status(200)
        self.finish(answer)

    @transport_security_check('receiver')
    @authenticated('receiver')
    @inlineCallbacks
    def post(self, tip_id):
        """
        Request: CommentDesc
        Response: CommentDesc
        Errors: InvalidAuthentication, InvalidInputFormat, TipIdNotFound, TipReceiptNotFound
        """
        request = self.validate_message(self.request.body, requests.CommentDesc)

        message = yield create_message_receiver(self.current_user.user_id, tip_id, request)

        self.set_status(201)  # Created
        self.finish(message)


class IdentityAccessRequestsCollection(BaseHandler):
    """
    This interface return the list of identity access requests performed
    on the tip and allow to perform new ones.
    """

    @transport_security_check('receiver')
    @authenticated('receiver')
    @inlineCallbacks
    def get(self, tip_id):
        """
        Response: identityaccessrequestsList
        Errors: InvalidAuthentication
        """
        answer = yield get_identityaccessrequests_list(self.current_user.user_id,
                                                       tip_id,
                                                       self.request.language)

        self.set_status(200)
        self.finish(answer)

    @transport_security_check('receiver')
    @authenticated('receiver')
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
        self.finish(identityaccessrequest)
