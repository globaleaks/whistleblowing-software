# -*- coding: UTF-8
#
# wbtip
#   *****
#
#   Contains all the logic for handling tip related operations, managed by
#   the whistleblower, handled and executed within /wbtip/* URI PATH interaction.
import os

from cyclone.web import asynchronous

from twisted.internet import threads
from twisted.internet.defer import inlineCallbacks

from globaleaks.orm import transact
from globaleaks.handlers.base import BaseHandler, directory_traversal_check
from globaleaks.handlers.rtip import serialize_comment, serialize_message, db_get_itip_comment_list
from globaleaks.handlers.submission import serialize_usertip, \
    db_save_questionnaire_answers, db_get_archived_questionnaire_schema
from globaleaks.models import serializers, \
    InternalFile, WhistleblowerFile, \
    ReceiverTip, WhistleblowerTip, Comment, Message
from globaleaks.rest import errors, requests
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import log, datetime_now, datetime_to_ISO8601

def wb_serialize_ifile(f):
    return {
        'id': f.id,
        'creation_date': datetime_to_ISO8601(f.creation_date),
        'name': f.name,
        'size': f.size,
        'content_type': f.content_type
    }


def wb_serialize_wbfile(f):
    return {
        'id': f.id,
        'creation_date': datetime_to_ISO8601(f.creation_date),
        'name': f.name,
        'description': f.description,
        'size': f.size,
        'content_type': f.content_type
    }


def db_access_wbtip(store, wbtip_id):
    wbtip = store.find(WhistleblowerTip, WhistleblowerTip.id == wbtip_id).one()

    if not wbtip:
        raise errors.TipReceiptNotFound

    return wbtip


def db_get_rfile_list(store, itip_id):
    ifiles = store.find(InternalFile, InternalFile.internaltip_id == itip_id)

    return [wb_serialize_ifile(ifile) for ifile in ifiles]


def db_get_wbfile_list(store, itip_id):
    wbfiles = store.find(WhistleblowerFile, WhistleblowerFile.receivertip_id == ReceiverTip.id,
                                           ReceiverTip.internaltip_id == itip_id)

    return [wb_serialize_wbfile(wbfile) for wbfile in wbfiles]


def db_get_wbtip(store, wbtip_id, language):
    wbtip = db_access_wbtip(store, wbtip_id)

    wbtip.internaltip.wb_access_counter += 1
    wbtip.internaltip.wb_last_access = datetime_now()

    log.debug("Tip %s access granted to whistleblower (%d)" %
              (wbtip.id, wbtip.internaltip.wb_access_counter))

    return serialize_wbtip(store, wbtip, language)


@transact
def get_wbtip(store, wbtip_id, language):
    return db_get_wbtip(store, wbtip_id, language)


def serialize_wbtip(store, wbtip, language):
    ret = serialize_usertip(store, wbtip, language)

    # filter submission progressive
    # to prevent a fake whistleblower to assess every day how many
    # submissions are received by the platform.
    del ret['progressive']

    ret['id'] = wbtip.id
    ret['comments'] = db_get_itip_comment_list(store, wbtip.internaltip)
    ret['rfiles'] = db_get_rfile_list(store, wbtip.id)
    ret['wbfiles'] = db_get_wbfile_list(store, wbtip.id)

    return ret

@transact
def create_comment(store, wbtip_id, request):
    wbtip = db_access_wbtip(store, wbtip_id)
    wbtip.internaltip.update_date = datetime_now()

    comment = Comment()
    comment.content = request['content']
    comment.internaltip_id = wbtip.id
    comment.type = u'whistleblower'

    wbtip.internaltip.comments.add(comment)

    return serialize_comment(comment)


@transact
def get_itip_message_list(store, wbtip_id, receiver_id):
    """
    Get the messages content and mark all the unread
    messages as "read"
    """
    wbtip = db_access_wbtip(store, wbtip_id)

    rtip = store.find(ReceiverTip, ReceiverTip.internaltip_id == wbtip.id,
                      ReceiverTip.receiver_id == receiver_id).one()

    if not rtip:
        raise errors.TipIdNotFound

    return [serialize_message(message) for message in rtip.messages]


@transact
def create_message(store, wbtip_id, receiver_id, request):
    wbtip = db_access_wbtip(store, wbtip_id)
    wbtip.internaltip.update_date = datetime_now()

    rtip = store.find(ReceiverTip, ReceiverTip.internaltip_id == wbtip.id,
                      ReceiverTip.receiver_id == receiver_id).one()

    if not rtip:
        raise errors.TipIdNotFound

    msg = Message()
    msg.content = request['content']
    msg.receivertip_id = rtip.id
    msg.type = u'whistleblower'

    store.add(msg)

    return serialize_message(msg)


@transact
def update_identity_information(store, tip_id, identity_field_id, identity_field_answers, language):
    wbtip = db_access_wbtip(store, tip_id)
    internaltip = wbtip.internaltip
    identity_provided = internaltip.identity_provided

    if not identity_provided:
        questionnaire = db_get_archived_questionnaire_schema(store, internaltip.questionnaire_hash, language)
        for step in questionnaire:
            for field in step['children']:
                if field['id'] == identity_field_id and field['key'] == 'whistleblower_identity':
                    db_save_questionnaire_answers(store, internaltip.id,
                                                  {identity_field_id: [identity_field_answers]})
                    now = datetime_now()
                    internaltip.update_date = now
                    internaltip.identity_provided = True
                    internaltip.identity_provided_date = now
                    return


class WBTipInstance(BaseHandler):
    """
    This interface expose the Whistleblower Tip.

    Tip is the safe area, created with an expiration time, where Receivers (and optionally)
    Whistleblower can discuss about the submission, comments, collaborative voting, forward,
    promote, and perform other operations in this protected environment.
    """

    @BaseHandler.transport_security_check('whistleblower')
    @BaseHandler.authenticated('whistleblower')
    @inlineCallbacks
    def get(self):
        """
        Parameters: None
        Response: actorsTipDesc

        Check the user id (in the whistleblower case, is authenticated and
        contain the internaltip)
        """
        answer = yield get_wbtip(self.current_user.user_id, self.request.language)

        self.write(answer)


class WBTipCommentCollection(BaseHandler):
    """
    Interface use to write comments inside of a Tip, is not implemented as CRUD because we've not
    needs, at the moment, to delete/update comments once has been published. Comments is intended, now,
    as a stone written consideration about Tip reliability, therefore no editing and rethinking is
    permitted.
    """
    @BaseHandler.transport_security_check('whistleblower')
    @BaseHandler.authenticated('whistleblower')
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
        self.write(answer)


class WBTipMessageCollection(BaseHandler):
    """
    This interface return the lists of the private messages exchanged between
    whistleblower and the specified receiver requested in GET

    Supports the creation of a new message for the requested receiver
    """
    @BaseHandler.transport_security_check('whistleblower')
    @BaseHandler.authenticated('whistleblower')
    @inlineCallbacks
    def get(self, receiver_id):
        messages = yield get_itip_message_list(self.current_user.user_id, receiver_id)

        self.write(messages)

    @BaseHandler.transport_security_check('whistleblower')
    @BaseHandler.authenticated('whistleblower')
    @inlineCallbacks
    def post(self, receiver_id):
        request = self.validate_message(self.request.body, requests.CommentDesc)

        message = yield create_message(self.current_user.user_id, receiver_id, request)

        self.set_status(201)  # Created
        self.write(message)


class WhistleblowerFileInstanceHandler(BaseHandler):
    @transact
    def download_wbfile(self, store, user_id, file_id):
        wbfile = store.find(WhistleblowerFile,
                            WhistleblowerFile.id == file_id,
                            WhistleblowerFile.receivertip_id == ReceiverTip.id,
                            WhistleblowerTip.id == ReceiverTip.internaltip_id).one()

        if not wbfile:
            raise errors.FileIdNotFound

        log.debug("Download of file %s by whistleblower %s" %
                  (wbfile.id, user_id))

        wbfile.downloads += 1

        return serializers.serialize_wbfile(wbfile)

    @BaseHandler.transport_security_check('whistleblower')
    @BaseHandler.authenticated('whistleblower')
    @inlineCallbacks
    @asynchronous
    def get(self, wbfile_id):
        wbfile = yield self.download_wbfile(self.current_user.user_id, wbfile_id)

        filelocation = os.path.join(GLSettings.submission_path, wbfile['path'])

        directory_traversal_check(GLSettings.submission_path, filelocation)

        self.force_file_download(wbfile['name'], filelocation)


class WBTipIdentityHandler(BaseHandler):
    """
    This is the interface that securely allows the whistleblower to provide his identity
    """
    @BaseHandler.transport_security_check('whistleblower')
    @BaseHandler.authenticated('whistleblower')
    @inlineCallbacks
    def post(self, tip_id):
        request = self.validate_message(self.request.body, requests.WhisleblowerIdentityAnswers)

        yield update_identity_information(tip_id,
                                          request['identity_field_id'],
                                          request['identity_field_answers'],
                                          self.request.language)

        self.set_status(202)  # Updated
