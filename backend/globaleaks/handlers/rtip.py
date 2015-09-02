# -*- coding: UTF-8
#
# rtip
# ****
#
# Contains all the logic for handling tip related operations, for the
# receiver side. These classes are executed in the /rtip/* URI PATH

import os

from twisted.internet.defer import inlineCallbacks
from storm.expr import Desc, And

from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import transport_security_check, authenticated
from globaleaks.handlers.submission import db_get_archived_questionnaire_schema, \
    db_serialize_questionnaire_answers
from globaleaks.rest import requests
from globaleaks.utils.utility import log, utc_future_date, datetime_now, \
    datetime_to_ISO8601, datetime_to_pretty_str

from globaleaks.utils.structures import Rosetta
from globaleaks.settings import transact, transact_ro, GLSettings
from globaleaks.models import Node, Notification, Comment, Message, \
    ReceiverFile, ReceiverTip, EventLogs,  InternalTip, ArchivedSchema
from globaleaks.rest import errors


def receiver_serialize_tip(store, internaltip, language):
    ret_dict = {
        'id': internaltip.id,
        'context_id': internaltip.context.id,
        'show_receivers': internaltip.context.show_receivers,
        # Question: this is serialization is for Receivers, the Receiver are hidden just for Viz
        'creation_date': datetime_to_ISO8601(internaltip.creation_date),
        'expiration_date': datetime_to_ISO8601(internaltip.expiration_date),
        'questionnaire': db_get_archived_questionnaire_schema(store, internaltip.questionnaire_hash, language),
        'answers': db_serialize_questionnaire_answers(store, internaltip),
        'tor2web': internaltip.tor2web,
        'timetolive': internaltip.context.tip_timetolive,
        'enable_comments': internaltip.context.enable_comments,
        'enable_private_messages': internaltip.context.enable_private_messages,
    }

    # context_name and context_description are localized fields
    mo = Rosetta(internaltip.context.localized_strings)
    mo.acquire_storm_object(internaltip.context)
    for attr in ['name', 'description']:
        key = "context_%s" % attr
        ret_dict[key] = mo.dump_localized_key(attr, language)

    return ret_dict


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


def db_get_files_receiver(store, user_id, tip_id):
    rtip = db_access_tip(store, user_id, tip_id)

    receiver_files = store.find(ReceiverFile,
                                (ReceiverFile.internaltip_id == rtip.internaltip_id,
                                 ReceiverFile.receiver_id == rtip.receiver_id))

    files_list = []
    for receiverfile in receiver_files:
        internalfile = receiverfile.internalfile
        files_list.append(receiver_serialize_file(internalfile, receiverfile, tip_id))

    return files_list


def db_get_tip_receiver(store, user_id, tip_id, language):
    rtip = db_access_tip(store, user_id, tip_id)

    notif = store.find(Notification).one()

    if not notif.send_email_for_every_event:
        # If Receiver is accessing this Tip, Events related can be removed before
        # Notification is sent. This is a Twitter/Facebook -like behavior.
        store.find(EventLogs, EventLogs.receivertip_id == tip_id).remove()
        # Note - before the check was:
        # store.find(EventLogs, And(EventLogs.receivertip_id == tip_id,
        #                          EventLogs.mail_sent == True)).remove()

    tip_desc = receiver_serialize_tip(store, rtip.internaltip, language)

    # are added here because part of ReceiverTip, not InternalTip
    tip_desc['access_counter'] = rtip.access_counter
    tip_desc['id'] = rtip.id
    tip_desc['receiver_id'] = user_id
    tip_desc['label'] = rtip.label

    return tip_desc


def db_increment_receiver_access_count(store, user_id, tip_id):
    rtip = db_access_tip(store, user_id, tip_id)

    rtip.access_counter += 1
    rtip.last_access = datetime_now()

    log.debug("Tip %s access granted to user %s (%d)" %
              (rtip.id, rtip.receiver.name, rtip.access_counter))

    return rtip.access_counter


def db_access_tip(store, user_id, tip_id):
    rtip = store.find(ReceiverTip, ReceiverTip.id == unicode(tip_id),
                      ReceiverTip.receiver_id == user_id).one()

    if not rtip:
        raise errors.TipIdNotFound

    return rtip


def db_delete_itip(store, itip, itip_number=0):
    for ifile in itip.internalfiles:
        abspath = os.path.join(GLSettings.submission_path, ifile.file_path)

        if os.path.isfile(abspath):
            log.debug("Removing internalfile %s" % abspath)
            try:
                os.remove(abspath)
            except OSError as excep:
                log.err("Unable to remove %s: %s" % (abspath, excep.strerror))

        rfiles = store.find(ReceiverFile, ReceiverFile.internalfile_id == ifile.id)
        for rfile in rfiles:
            # The following code must be bypassed if rfile.file_path == ifile.filepath,
            # this mean that is referenced the plaintext file instead having E2E.
            if rfile.file_path == ifile.file_path:
                continue

            abspath = os.path.join(GLSettings.submission_path, rfile.file_path)

            if os.path.isfile(abspath):
                log.debug("Removing receiverfile %s" % abspath)
                try:
                    os.remove(abspath)
                except OSError as excep:
                    log.err("Unable to remove %s: %s" % (abspath, excep.strerror))

    if itip_number:
        log.debug("Removing from Cleaning operation InternalTip (%s) N# %d" %
                  (itip.id, itip_number) )
    else:
        log.debug("Removing InternalTip as commanded by Receiver (%s)" % itip.id)

    store.remove(itip)

    if store.find(InternalTip, InternalTip.questionnaire_hash == itip.questionnaire_hash).count() == 0:
        store.find(ArchivedSchema, ArchivedSchema.hash == itip.questionnaire_hash).remove()


def db_delete_rtip(store, rtip):
    return db_delete_itip(store, rtip.internaltip)


def db_postpone_expiration_date(rtip):
    rtip.internaltip.expiration_date = \
        utc_future_date(seconds=rtip.internaltip.context.tip_timetolive)


@transact
def delete_rtip(store, user_id, tip_id):
    """
    Delete internalTip is possible only to Receiver with
    the dedicated property.
    """
    rtip = db_access_tip(store, user_id, tip_id)

    node = store.find(Node).one()

    if not (node.can_delete_submission or
                rtip.receiver.can_delete_submission):
        raise errors.ForbiddenOperation

    db_delete_rtip(store, rtip)


@transact
def postpone_expiration_date(store, user_id, tip_id):
    rtip = db_access_tip(store, user_id, tip_id)

    node = store.find(Node).one()

    if not (node.can_postpone_expiration or
                rtip.receiver.can_postpone_expiration):

        raise errors.ExtendTipLifeNotEnabled

    log.debug("Postpone check: Node %s, Receiver %s" % (
       "True" if node.can_postpone_expiration else "False",
       "True" if rtip.receiver.can_postpone_expiration else "False"
    ))

    db_postpone_expiration_date(rtip)

    log.debug(" [%s] in %s has postponed expiration time to %s" % (
        rtip.receiver.name,
        datetime_to_pretty_str(datetime_now()),
        datetime_to_pretty_str(rtip.internaltip.expiration_date)))


@transact
def assign_rtip_label(store, user_id, tip_id, label_content):
    rtip = db_access_tip(store, user_id, tip_id)
    log.debug("Updating ReceiverTip label from [%s] to %s" % (rtip.label, label_content))
    rtip.label = unicode(label_content)


@transact
def get_tip(store, user_id, tip_id, language):
    db_increment_receiver_access_count(store, user_id, tip_id)
    answer = db_get_tip_receiver(store, user_id, tip_id, language)
    answer['collection'] = '/rtip/' + tip_id + '/collection'
    answer['files'] = db_get_files_receiver(store, user_id, tip_id)

    return answer


@transact_ro
def get_comment_list_receiver(store, user_id, tip_id):
    rtip = db_access_tip(store, user_id, tip_id)

    comment_list = []
    for comment in rtip.internaltip.comments:
        comment_list.append(receiver_serialize_comment(comment))

    return comment_list


@transact
def create_comment_receiver(store, user_id, tip_id, request):
    rtip = db_access_tip(store, user_id, tip_id)

    comment = Comment()
    comment.content = request['content']
    comment.internaltip_id = rtip.internaltip.id
    comment.author = rtip.receiver.name
    comment.type = u'receiver'

    rtip.internaltip.comments.add(comment)

    return receiver_serialize_comment(comment)


def receiver_serialize_message(msg):
    return {
        'id': msg.id,
        'creation_date': datetime_to_ISO8601(msg.creation_date),
        'content': msg.content,
        'visualized': msg.visualized,
        'type': msg.type,
        'author': msg.author
    }


@transact
def get_messages_list(store, user_id, tip_id):
    rtip = db_access_tip(store, user_id, tip_id)

    content_list = []
    for msg in rtip.messages:
        content_list.append(receiver_serialize_message(msg))

        if not msg.visualized and msg.type == u'whistleblower':
            log.debug("Marking as read message [%s] from %s" % (msg.content, msg.author))
            msg.visualized = True

    return content_list


@transact
def create_message_receiver(store, user_id, tip_id, request):
    rtip = db_access_tip(store, user_id, tip_id)

    msg = Message()
    msg.content = request['content']
    msg.receivertip_id = rtip.id
    msg.author = rtip.receiver.name
    msg.visualized = False
    msg.type = u'receiver'

    store.add(msg)

    return receiver_serialize_message(msg)



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
        the wb_tip, this is why tip_is is not checked if self.is_whistleblower)

        This method is decorated as @unauthenticated because in the handler
        the various cases are managed differently.
        """

        answer = yield get_tip(self.current_user.user_id, tip_id, 'en')

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


def receiver_serialize_comment(comment):
    comment_desc = {
        'comment_id': comment.id,
        'type': comment.type,
        'content': comment.content,
        'author': comment.author,
        'creation_date': datetime_to_ISO8601(comment.creation_date)
    }

    return comment_desc


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


@transact_ro
def get_receiver_list_receiver(store, user_id, tip_id, language):
    rtip = db_access_tip(store, user_id, tip_id)

    receiver_list = []
    # Improvement TODO, instead of looping over rtip, that can be A LOTS, we
    # can just iterate over receiver, and then remove the receiver not present
    # in the specific InternalTip
    for rtip in rtip.internaltip.receivertips:
        receiver_desc = {
            "pgp_key_status": rtip.receiver.pgp_key_status,
            "can_delete_submission": rtip.receiver.can_delete_submission,
            "name": unicode(rtip.receiver.name),
            "receiver_id": unicode(rtip.receiver.id),
            "access_counter": rtip.access_counter,
        }

        mo = Rosetta(rtip.receiver.localized_strings)
        mo.acquire_storm_object(rtip.receiver)
        receiver_desc["description"] = mo.dump_localized_key("description", language)

        receiver_list.append(receiver_desc)

    return receiver_list


class RTipReceiversCollection(BaseHandler):
    """
    This interface return the list of the Receiver active in a Tip.
    GET /tip/<auth_tip_id>/receivers
    """

    @transport_security_check('receiver')
    @authenticated('receiver')
    @inlineCallbacks
    def get(self, tip_id):
        """
        Parameters: None
        Response: actorsReceiverList
        Errors: InvalidAuthentication
        """
        answer = yield get_receiver_list_receiver(self.current_user.user_id, tip_id, self.request.language)

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
