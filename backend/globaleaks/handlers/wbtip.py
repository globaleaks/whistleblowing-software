# -*- coding: UTF-8
#
# wbtip
#   *****
#
#   Contains all the logic for handling tip related operations, managed by
#   the whistleblower, handled and executed within /wbtip/* URI PATH interaction.

from storm.exceptions import DatabaseError
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.rtip import db_get_itip_receivers_list, \
    serialize_comment, serialize_message
from globaleaks.handlers.submission import db_get_archived_questionnaire_schema, \
    db_serialize_questionnaire_answers
from globaleaks.handlers.authentication import transport_security_check, authenticated
from globaleaks.rest import requests
from globaleaks.utils.utility import log, datetime_now, datetime_to_ISO8601
from globaleaks.utils.structures import Rosetta
from globaleaks.settings import transact, transact_ro
from globaleaks.models import WhistleblowerTip, Comment, Message, ReceiverTip
from globaleaks.rest import errors


def wb_serialize_wbtip(store, wbtip, language):
    internaltip = wbtip.internaltip

    return {
        'id': internaltip.id,
        'context_id': internaltip.context_id,
        'context_name': mo.dump_localized_key('name', language),
        'show_receivers': internaltip.context.show_receivers,
        'creation_date': datetime_to_ISO8601(internaltip.creation_date),
        'update_date': datetime_to_ISO8601(internaltip.update_date),
        'expiration_date': datetime_to_ISO8601(internaltip.expiration_date),
        'questionnaire': db_get_archived_questionnaire_schema(store, internaltip.questionnaire_hash, language),
        'answers': db_serialize_questionnaire_answers(store, internaltip),
        'tor2web': internaltip.tor2web,
        'enable_comments': internaltip.enable_comments,
        'enable_messages': internaltip.enable_messages,
        'enable_two_way_communication': internaltip.enable_two_way_communication,
        'enable_attachments': internaltip.enable_attachments
    }


def wb_serialize_file(internalfile):
    return {
        'id': internalfile.id,
        'name': internalfile.name,
        'content_type': internalfile.content_type,
        'creation_date': datetime_to_ISO8601(internalfile.creation_date),
        'size': internalfile.size,
    }


def db_access_wbtip(store, wbtip_id):
    wbtip = store.find(WhistleblowerTip, WhistleblowerTip.id == wbtip_id).one()

    if not wbtip:
        raise errors.TipReceiptNotFound

    return wbtip


def db_get_files_wb(store, wbtip_id):
    wbtip = db_access_wbtip(store, wbtip_id)

    return [wb_serialize_file(internalfile) for internalfile in wbtip.internaltip.internalfiles]


def db_get_wbtip(store, wbtip_id, language):
    wbtip = db_access_wbtip(store, wbtip_id)

    # there is not a limit in the WB access counter, but is kept track
    wbtip.access_counter += 1

    tip_desc = wb_serialize_wbtip(store, wbtip, language)

    # two elements from WhistleblowerTip
    tip_desc['access_counter'] = wbtip.access_counter
    tip_desc['id'] = wbtip.id

    tip_desc['files'] = db_get_files_wb(store, wbtip_id)

    return tip_desc


@transact
def get_wbtip(store, wbtip_id, language):
    return db_get_wbtip(store, wbtip_id, language)


@transact_ro
def get_wbtip_receivers_list(store, wbtip_id, language):
    wbtip = db_access_wbtip(store, wbtip_id)

    return db_get_itip_receivers_list(store, wbtip.internaltip, language)


@transact_ro
def get_comment_list_wb(store, wbtip_id):
    wbtip = db_access_wbtip(store, wbtip_id)

    return [serialize_comment(comment) for comment in wbtip.internaltip.comments]


@transact
def create_comment_wb(store, wbtip_id, request):
    wbtip = db_access_wbtip(store, wbtip_id)
    wbtip.internaltip.update_update = datetime_now()

    comment = Comment()
    comment.content = request['content']
    comment.internaltip_id = wbtip.internaltip_id
    comment.author = u'whistleblower'
    comment.type = u'whistleblower'

    wbtip.internaltip.comments.add(comment)

    return serialize_comment(comment)


@transact
def get_messages_content(store, wbtip_id, receiver_id):
    """
    Get the messages content and mark all the unread
    messages as "read"
    """
    wbtip = db_access_wbtip(store, wbtip_id)

    rtip = store.find(ReceiverTip, ReceiverTip.internaltip_id == wbtip.internaltip_id,
                      ReceiverTip.receiver_id == receiver_id).one()

    if not rtip:
        raise errors.TipIdNotFound

    messages_list = []
    for msg in rtip.messages:
        messages_list.append(serialize_message(msg))

        if not msg.visualized and msg.type == u'receiver':
            log.debug("Marking as readed message [%s] from %s" % (msg.content, msg.author))
            msg.visualized = True

    return messages_list


@transact
def create_message_wb(store, wbtip_id, receiver_id, request):
    wbtip = db_access_wbtip(store, wbtip_id)

    rtip = store.find(ReceiverTip, ReceiverTip.internaltip_id == wbtip.internaltip_id,
                      ReceiverTip.receiver_id == receiver_id).one()

    if not rtip:
        raise errors.TipIdNotFound

    msg = Message()
    msg.content = request['content']
    msg.receivertip_id = rtip.id
    msg.author = u'whistleblower'
    msg.visualized = False

    msg.type = u'whistleblower'

    try:
        store.add(msg)
    except DatabaseError as dberror:
        log.err("Unable to add WB message from %s: %s" % (rtip.receiver.user.name, dberror))
        raise dberror

    return serialize_message(msg)


class WBTipInstance(BaseHandler):
    """
    This interface expose the Whistleblower Tip.

    Tip is the safe area, created with an expiration time, where Receivers (and optionally)
    Whistleblower can discuss about the submission, comments, collaborative voting, forward,
    promote, and perform other operations in this protected environment.
    """

    @transport_security_check('whistleblower')
    @authenticated('whistleblower')
    @inlineCallbacks
    def get(self):
        """
        Parameters: None
        Response: actorsTipDesc

        Check the user id (in the whistleblower case, is authenticated and
        contain the internaltip)
        """

        answer = yield get_wbtip(self.current_user.user_id, 'en')

        self.set_status(200)
        self.finish(answer)


class WBTipCommentCollection(BaseHandler):
    """
    Interface use to read/write comments inside of a Tip, is not implemented as CRUD because we've not
    needs, at the moment, to delete/update comments once has been published. Comments is intended, now,
    as a stone written consideration about Tip reliability, therefore no editing and rethinking is
    permitted.
    """
    @transport_security_check('whistleblower')
    @authenticated('whistleblower')
    @inlineCallbacks
    def get(self):
        """
        Parameters: None
        Response: actorsCommentList
        """
        wb_comment_list = yield get_comment_list_wb(self.current_user.user_id)

        self.set_status(200)
        self.finish(wb_comment_list)

    @transport_security_check('whistleblower')
    @authenticated('whistleblower')
    @inlineCallbacks
    def post(self):
        """
        Request: CommentDesc
        Response: CommentDesc
        Errors: InvalidInputFormat, TipIdNotFound, TipReceiptNotFound
        """

        request = self.validate_message(self.request.body, requests.CommentDesc)
        answer = yield create_comment_wb(self.current_user.user_id, request)

        self.set_status(201)  # Created
        self.finish(answer)


class WBTipReceiversCollection(BaseHandler):
    """
    This interface return the list of the Receiver active in a Tip.
    GET /tip/receivers
    """

    @transport_security_check('whistleblower')
    @authenticated('whistleblower')
    @inlineCallbacks
    def get(self):
        """
        Parameters: None
        Response: actorsReceiverList
        """
        answer = yield get_wbtip_receivers_list(self.current_user.user_id, self.request.language)

        self.set_status(200)
        self.finish(answer)


class WBTipMessageCollection(BaseHandler):
    """
    This interface return the lists of the private messages exchanged between
    whistleblower and the specified receiver requested in GET

    Supports the creation of a new message for the requested receiver
    """

    @transport_security_check('whistleblower')
    @authenticated('whistleblower')
    @inlineCallbacks
    def get(self, receiver_id):
        messages = yield get_messages_content(self.current_user.user_id, receiver_id)

        self.set_status(200)
        self.finish(messages)

    @transport_security_check('whistleblower')
    @authenticated('whistleblower')
    @inlineCallbacks
    def post(self, receiver_id):
        request = self.validate_message(self.request.body, requests.CommentDesc)

        message = yield create_message_wb(self.current_user.user_id, receiver_id, request)

        self.set_status(201)  # Created
        self.finish(message)
