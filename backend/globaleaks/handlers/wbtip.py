# -*- coding: utf-8 -*-
#
# Handlers dealing with tip interface for whistleblowers (wbtip)
import base64
import json
from twisted.internet.threads import deferToThread
from twisted.internet.defer import inlineCallbacks, returnValue

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.rtip import serialize_comment, serialize_message, db_get_itip_comment_list, WBFileHandler
from globaleaks.handlers.submission import serialize_usertip, \
    db_save_questionnaire_answers, decrypt_tip, \
    db_set_internaltip_answers, db_get_questionnaire, db_archive_questionnaire_schema, db_set_internaltip_data
from globaleaks.orm import transact
from globaleaks.rest import errors, requests
from globaleaks.state import State
from globaleaks.utils.crypto import GCE
from globaleaks.utils.log import log
from globaleaks.utils.utility import datetime_now, datetime_to_ISO8601


def wb_serialize_ifile(ifile):
    return {
        'id': ifile.id,
        'creation_date': datetime_to_ISO8601(ifile.creation_date),
        'name': ifile.name,
        'size': ifile.size,
        'content_type': ifile.content_type
    }


def wb_serialize_wbfile(session, wbfile):
    receiver_id = session.query(models.ReceiverTip.receiver_id) \
                         .filter(models.ReceiverTip.id == wbfile.receivertip_id).one()[0]

    return {
        'id': wbfile.id,
        'creation_date': datetime_to_ISO8601(wbfile.creation_date),
        'name': wbfile.name,
        'description': wbfile.description,
        'size': wbfile.size,
        'content_type': wbfile.content_type,
        'author': receiver_id
    }


def db_get_rfile_list(session, itip_id):
    return [wb_serialize_ifile(ifile) for ifile in session.query(models.InternalFile) \
                                                          .filter(models.InternalFile.internaltip_id == itip_id,
                                                                  models.InternalTip.id == itip_id)]


def db_get_wbfile_list(session, itip_id):
    wbfiles = session.query(models.WhistleblowerFile) \
                     .filter(models.WhistleblowerFile.receivertip_id == models.ReceiverTip.id,
                             models.ReceiverTip.internaltip_id == itip_id)

    return [wb_serialize_wbfile(session, wbfile) for wbfile in wbfiles]


def db_get_wbtip(session, itip_id, language):
    wbtip, itip = models.db_get(session,
                                (models.WhistleblowerTip, models.InternalTip),
                                models.WhistleblowerTip.id == models.InternalTip.id,
                                models.InternalTip.id == itip_id)

    itip.wb_access_counter += 1
    itip.wb_last_access = datetime_now()

    return serialize_wbtip(session, wbtip, itip, language), wbtip.crypto_tip_prv_key


@transact
def get_wbtip(session, itip_id, language):
    return db_get_wbtip(session, itip_id, language)


def serialize_wbtip(session, wbtip, itip, language):
    ret = serialize_usertip(session, itip, itip, language)

    ret['comments'] = db_get_itip_comment_list(session, itip.id)
    ret['messages'] = db_get_itip_message_list(session, itip.id)
    ret['rfiles'] = db_get_rfile_list(session, itip.id)
    ret['wbfiles'] = db_get_wbfile_list(session, itip.id)

    return ret


@transact
def create_comment(session, tid, wbtip_id, user_key, content):
    wbtip, itip = session.query(models.WhistleblowerTip, models.InternalTip)\
                         .filter(models.WhistleblowerTip.id == wbtip_id,
                                 models.InternalTip.id == models.WhistleblowerTip.id,
                                 models.InternalTip.tid == tid).one_or_none()

    if wbtip is None:
        raise errors.ModelNotFound(models.WhistleblowerTip)

    itip.update_date = itip.wb_last_access = datetime_now()

    comment = models.Comment()
    comment.internaltip_id = wbtip_id
    comment.type = u'whistleblower'

    if itip.crypto_tip_pub_key:
        comment.content = base64.b64encode(GCE.asymmetric_encrypt(itip.crypto_tip_pub_key, content)).decode()
    else:
        comment.content = content

    session.add(comment)
    session.flush()

    ret = serialize_comment(session, comment)
    ret['content'] = content

    return ret


def db_get_itip_message_list(session, wbtip_id):
    messages = session.query(models.Message) \
                      .filter(models.Message.receivertip_id == models.ReceiverTip.id,
                              models.ReceiverTip.internaltip_id == models.InternalTip.id,
                              models.InternalTip.id == wbtip_id)

    return [serialize_message(session, message) for message in messages]


@transact
def create_message(session, tid, wbtip_id, user_key, receiver_id, content):
    wbtip, itip, rtip_id = session.query(models.WhistleblowerTip, models.InternalTip, models.ReceiverTip.id) \
                                  .filter(models.WhistleblowerTip.id == wbtip_id,
                                          models.ReceiverTip.internaltip_id == wbtip_id,
                                          models.ReceiverTip.receiver_id == receiver_id,
                                          models.InternalTip.id == models.WhistleblowerTip.id,
                                          models.InternalTip.tid == tid).one_or_none()

    if wbtip is None:
        raise errors.ModelNotFound(models.WhistleblowerTip)

    itip.update_date = itip.wb_last_access = datetime_now()

    msg = models.Message()
    msg.receivertip_id = rtip_id
    msg.type = u'whistleblower'

    if itip.crypto_tip_pub_key:
        msg.content = base64.b64encode(GCE.asymmetric_encrypt(itip.crypto_tip_pub_key, content)).decode()
    else:
        msg.content = content

    session.add(msg)
    session.flush()

    ret = serialize_message(session, msg)
    ret['content'] = content

    return ret


@transact
def update_identity_information(session, tid, tip_id, identity_field_id, wbi, language):
    itip = models.db_get(session, models.InternalTip, models.InternalTip.id == tip_id, models.InternalTip.tid == tid)

    if itip.crypto_tip_pub_key:
        wbi = base64.b64encode(GCE.asymmetric_encrypt(itip.crypto_tip_pub_key, json.dumps(wbi).encode())).decode()

    db_set_internaltip_data(session, itip.id, 'identity_provided', True, False)
    db_set_internaltip_data(session, itip.id, 'whistleblower_identity', wbi, True)

    now = datetime_now()
    itip.update_date = now
    itip.wb_last_access = now


@transact
def store_additional_questionnaire_answers(session, tid, tip_id, answers, language):
    internaltip = session.query(models.InternalTip) \
                         .filter(models.InternalTip.id == tip_id,
                                 models.InternalTip.tid == tid).one()

    if not internaltip.additional_questionnaire_id:
        return

    steps = db_get_questionnaire(session, tid, internaltip.additional_questionnaire_id, None)['steps']
    questionnaire_hash = db_archive_questionnaire_schema(session, steps)

    db_save_questionnaire_answers(session, tid, internaltip.id, answers)

    db_set_internaltip_answers(session,
                               internaltip.id,
                               questionnaire_hash,
                               answers,
                               False)

    internaltip.additional_questionnaire_id = ''


class WBTipInstance(BaseHandler):
    """
    This interface expose the Whistleblower Tip.

    Tip is the safe area, created with an expiration time, where Receivers (and optionally)
    Whistleblower can discuss about the submission, comments, collaborative voting, forward,
    promote, and perform other operations in this protected environment.
    """
    check_roles = 'whistleblower'

    @inlineCallbacks
    def get(self):
        tip, crypto_tip_prv_key = yield get_wbtip(self.current_user.user_id, self.request.language)

        if State.tenant_cache[self.request.tid].encryption and crypto_tip_prv_key:
            tip = yield deferToThread(decrypt_tip, self.current_user.cc, crypto_tip_prv_key, tip)

        returnValue(tip)


class WBTipCommentCollection(BaseHandler):
    """
    Interface use to write comments inside of a Tip, is not implemented as CRUD because we've not
    needs, at the moment, to delete/update comments once has been published. Comments is intended, now,
    as a stone written consideration about Tip reliability, therefore no editing and rethinking is
    permitted.
    """
    check_roles = 'whistleblower'

    def post(self):
        request = self.validate_message(self.request.content.read(), requests.CommentDesc)
        return create_comment(self.request.tid, self.current_user.user_id, self.current_user.cc, request['content'])


class WBTipMessageCollection(BaseHandler):
    """
    This interface return the lists of the private messages exchanged between
    whistleblower and the specified receiver requested in GET

    Supports the creation of a new message for the requested receiver
    """
    check_roles = 'whistleblower'

    def post(self, receiver_id):
        request = self.validate_message(self.request.content.read(), requests.CommentDesc)

        return create_message(self.request.tid, self.current_user.user_id, self.current_user.cc, receiver_id, request['content'])


class WBTipWBFileHandler(WBFileHandler):
    check_roles = 'whistleblower'
    upload_handler = False

    def user_can_access(self, session, tid, wbfile):
        wbtip_id = session.query(models.InternalTip.id) \
                          .filter(models.ReceiverTip.id == wbfile.receivertip_id,
                                  models.InternalTip.id == models.ReceiverTip.internaltip_id,
                                  models.InternalTip.tid == tid).one_or_none()

        return wbtip_id is not None and self.current_user.user_id == wbtip_id[0]

    def access_wbfile(self, session, wbfile):
        wbfile.downloads += 1
        log.debug("Download of file %s by whistleblower %s",
                  wbfile.id, self.current_user.user_id)


class WBTipIdentityHandler(BaseHandler):
    """
    This is the interface that securely allows the whistleblower to provide his identity
    """
    check_roles = 'whistleblower'

    def post(self, tip_id):
        request = self.validate_message(self.request.content.read(), requests.WhisleblowerIdentityAnswers)

        return update_identity_information(self.request.tid,
                                           tip_id,
                                           request['identity_field_id'],
                                           request['identity_field_answers'],
                                           self.request.language)


class WBTipAdditionalQuestionnaire(BaseHandler):
    """
    This is the interface that securely allows the whistleblower to fill the additional questionnaire
    """
    check_roles = 'whistleblower'

    def post(self, tip_id):
        request = self.validate_message(self.request.content.read(), requests.AdditionalQuestionnaireAnswers)

        return store_additional_questionnaire_answers(self.request.tid,
                                                      tip_id,
                                                      request['answers'],
                                                      self.request.language)
