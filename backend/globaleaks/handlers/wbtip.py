# -*- coding: UTF-8
#
# wbtip
#   *****
#
#   Contains all the logic for handling tip related operations, managed by
#   the whistleblower, handled and executed within /wbtip/* URI PATH interaction.
from twisted.internet.defer import inlineCallbacks

from globaleaks.orm import transact, transact_ro
from globaleaks.handlers.authentication import transport_security_check, authenticated
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.rtip import db_get_itip_receiver_list, \
    serialize_comment, serialize_message
from globaleaks.handlers.submission import serialize_usertip, \
    db_save_questionnaire_answers, db_get_archived_questionnaire_schema
from globaleaks.models import WhistleblowerTip, Comment, Message, ReceiverTip
from globaleaks.rest import errors, requests
from globaleaks.utils.utility import log, datetime_now, datetime_to_ISO8601


def wb_serialize_file(internalfile):
    return {
        'id': internalfile.id,
        'name': internalfile.name,
        'content_type': internalfile.content_type,
        'creation_date': datetime_to_ISO8601(internalfile.creation_date),
        'size': internalfile.size
    }


def db_access_wbtip(store, wbtip_id):
    wbtip = store.find(WhistleblowerTip, WhistleblowerTip.id == wbtip_id).one()

    if not wbtip:
        raise errors.TipReceiptNotFound

    return wbtip


def db_get_file_list(store, wbtip_id):
    wbtip = db_access_wbtip(store, wbtip_id)

    return [wb_serialize_file(internalfile) for internalfile in wbtip.internaltip.internalfiles]


def db_get_wbtip(store, wbtip_id, language):
    wbtip = db_access_wbtip(store, wbtip_id)

    wbtip.access_counter += 1

    tip_desc = serialize_wbtip(store, wbtip, language)

    return tip_desc


@transact
def get_wbtip(store, wbtip_id, language):
    return db_get_wbtip(store, wbtip_id, language)


@transact_ro
def get_receiver_list(store, wbtip_id, language):
    wbtip = db_access_wbtip(store, wbtip_id)

    return db_get_itip_receiver_list(store, wbtip.internaltip, language)


@transact_ro
def get_comment_list(store, wbtip_id):
    wbtip = db_access_wbtip(store, wbtip_id)

    return [serialize_comment(comment) for comment in wbtip.internaltip.comments]


def serialize_wbtip(store, wbtip, language):
    ret = serialize_usertip(store, wbtip, language)

    # filter submission progressive
    # to prevent a fake whistleblower to assess every day how many
    # submissions are received by the platform.
    del ret['progressive']

    ret['id'] = wbtip.id
    ret['files'] = db_get_file_list(store, wbtip.id)

    return ret

@transact
def create_comment(store, wbtip_id, request):
    wbtip = db_access_wbtip(store, wbtip_id)
    wbtip.internaltip.update_date = datetime_now()

    comment = Comment()
    comment.content = request['content']
    comment.internaltip_id = wbtip.internaltip_id
    comment.author = u'whistleblower'
    comment.type = u'whistleblower'

    wbtip.internaltip.comments.add(comment)

    return serialize_comment(comment)


@transact
def get_message_list(store, wbtip_id, receiver_id):
    """
    Get the messages content and mark all the unread
    messages as "read"
    """
    wbtip = db_access_wbtip(store, wbtip_id)

    rtip = store.find(ReceiverTip, ReceiverTip.internaltip_id == wbtip.internaltip_id,
                      ReceiverTip.receiver_id == receiver_id).one()

    if not rtip:
        raise errors.TipIdNotFound

    return [serialize_message(message) for message in rtip.messages]


@transact
def create_message(store, wbtip_id, receiver_id, request):
    wbtip = db_access_wbtip(store, wbtip_id)
    wbtip.internaltip.update_date = datetime_now()

    rtip = store.find(ReceiverTip, ReceiverTip.internaltip_id == wbtip.internaltip_id,
                      ReceiverTip.receiver_id == receiver_id).one()

    if not rtip:
        raise errors.TipIdNotFound

    msg = Message()
    msg.content = request['content']
    msg.receivertip_id = rtip.id
    msg.author = u'whistleblower'
    msg.type = u'whistleblower'

    store.add(msg)

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

        answer = yield get_wbtip(self.current_user.user_id, self.request.language)

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
        wb_comment_list = yield get_comment_list(self.current_user.user_id)

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
        answer = yield create_comment(self.current_user.user_id, request)

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
        answer = yield get_receiver_list(self.current_user.user_id, self.request.language)

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
        messages = yield get_message_list(self.current_user.user_id, receiver_id)

        self.set_status(200)
        self.finish(messages)

    @transport_security_check('whistleblower')
    @authenticated('whistleblower')
    @inlineCallbacks
    def post(self, receiver_id):
        request = self.validate_message(self.request.body, requests.CommentDesc)

        message = yield create_message(self.current_user.user_id, receiver_id, request)

        self.set_status(201)  # Created
        self.finish(message)


class WBTipIdentityHandler(BaseHandler):
    """
    This is the interface that securely allows the whistleblower to provide his identity
    """
    @transport_security_check('whistleblower')
    @authenticated('whistleblower')
    @inlineCallbacks
    def post(self, tip_id):
        """
        Some special operation over the Tip are handled here
        """
        request = self.validate_message(self.request.body, requests.WhisleblowerIdentityAnswers)

        @transact
        def update_identity_information(store, identity_field_id, identity_field_answers, language):
            wbtip = db_access_wbtip(store, tip_id)
            internaltip = wbtip.internaltip
            identity_provided = internaltip.identity_provided

            if not identity_provided:
                questionnaire = db_get_archived_questionnaire_schema(store, internaltip.questionnaire_hash, language)
                for step in questionnaire:
                    if identity_provided: break
                    for field in step['children']:
                        if identity_provided: break
                        if field['id'] == identity_field_id and field['key'] == 'whistleblower_identity':
                            db_save_questionnaire_answers(store, internaltip.id,
                                                          {identity_field_id: [identity_field_answers]})
                            now = datetime_now()
                            internaltip.update_date = now
                            internaltip.identity_provided = True
                            internaltip.identity_provided_date = now

        yield update_identity_information(request['identity_field_id'], request['identity_field_answers'], self.request.language)

        self.set_status(202)  # Updated
        self.finish()
