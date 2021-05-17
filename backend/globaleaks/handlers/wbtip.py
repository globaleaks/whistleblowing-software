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
    decrypt_tip, db_set_internaltip_answers, db_get_questionnaire, \
    db_archive_questionnaire_schema, db_set_internaltip_data
from globaleaks.models import serializers
from globaleaks.orm import db_get, transact
from globaleaks.rest import requests
from globaleaks.utils.crypto import GCE
from globaleaks.utils.log import log
from globaleaks.utils.utility import datetime_now


def db_get_rfile_list(session, itip_id):
    ifiles = session.query(models.InternalFile) \
                    .filter(models.InternalFile.internaltip_id == itip_id,
                            models.InternalTip.id == itip_id)

    return [serializers.serialize_ifile(session, ifile) for ifile in ifiles]


def db_get_wbfile_list(session, itip_id):
    wbfiles = session.query(models.WhistleblowerFile) \
                     .filter(models.WhistleblowerFile.receivertip_id == models.ReceiverTip.id,
                             models.ReceiverTip.internaltip_id == itip_id)

    return [serializers.serialize_wbfile(session, wbfile) for wbfile in wbfiles]


def db_get_wbtip(session, itip_id, language):
    wbtip, itip = db_get(session,
                         (models.WhistleblowerTip, models.InternalTip),
                         (models.WhistleblowerTip.id == models.InternalTip.id,
                          models.InternalTip.id == itip_id))

    itip.wb_access_counter += 1
    itip.wb_last_access = datetime_now()

    return serialize_wbtip(session, wbtip, itip, language), base64.b64decode(wbtip.crypto_tip_prv_key)


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
def create_comment(session, tid, wbtip_id, content):
    wbtip, itip = db_get(session,
                         (models.WhistleblowerTip, models.InternalTip),
                         (models.WhistleblowerTip.id == wbtip_id,
                          models.InternalTip.id == models.WhistleblowerTip.id,
                          models.InternalTip.enable_two_way_comments.is_(True),
                          models.InternalTip.status != 'closed',
                          models.InternalTip.tid == tid))

    itip.update_date = itip.wb_last_access = datetime_now()

    _content = content
    if itip.crypto_tip_pub_key:
        _content = base64.b64encode(GCE.asymmetric_encrypt(itip.crypto_tip_pub_key, content)).decode()

    comment = models.Comment()
    comment.internaltip_id = wbtip_id
    comment.type = 'whistleblower'
    comment.content = _content
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
def create_message(session, tid, wbtip_id, receiver_id, content):
    wbtip, itip, rtip_id = db_get(session,
                                  (models.WhistleblowerTip, models.InternalTip, models.ReceiverTip.id),
                                  (models.WhistleblowerTip.id == wbtip_id,
                                   models.ReceiverTip.internaltip_id == wbtip_id,
                                   models.ReceiverTip.receiver_id == receiver_id,
                                   models.InternalTip.id == models.WhistleblowerTip.id,
                                   models.InternalTip.enable_two_way_messages.is_(True),
                                   models.InternalTip.status != 'closed',
                                   models.InternalTip.tid == tid))

    itip.update_date = itip.wb_last_access = datetime_now()

    _content = content
    if itip.crypto_tip_pub_key:
        _content = base64.b64encode(GCE.asymmetric_encrypt(itip.crypto_tip_pub_key, content)).decode()

    msg = models.Message()
    msg.receivertip_id = rtip_id
    msg.type = 'whistleblower'
    msg.content = _content
    session.add(msg)
    session.flush()

    ret = serialize_message(session, msg)
    ret['content'] = content

    return ret


@transact
def update_identity_information(session, tid, tip_id, identity_field_id, wbi, language):
    itip = db_get(session,
                  models.InternalTip,
                  (models.InternalTip.id == tip_id,
                   models.InternalTip.status != 'closed',
                   models.InternalTip.tid == tid))

    if itip.crypto_tip_pub_key:
        wbi = base64.b64encode(GCE.asymmetric_encrypt(itip.crypto_tip_pub_key, json.dumps(wbi).encode())).decode()

    db_set_internaltip_data(session, itip.id, 'whistleblower_identity', wbi)

    now = datetime_now()
    itip.update_date = now
    itip.wb_last_access = now


@transact
def store_additional_questionnaire_answers(session, tid, tip_id, answers, language):
    itip, context = session.query(models.InternalTip, models.Context) \
                           .filter(models.InternalTip.id == tip_id,
                                   models.InternalTip.status != 'closed',
                                   models.InternalTip.tid == tid,
                                   models.Context.id == models.InternalTip.context_id).one()

    if not context.additional_questionnaire_id:
        return

    steps = db_get_questionnaire(session, tid, context.additional_questionnaire_id, None)['steps']
    questionnaire_hash = db_archive_questionnaire_schema(session, steps)

    db_save_plaintext_answers(session, tid, itip.id, answers, itip.crypto_tip_pub_key != '')

    if itip.crypto_tip_pub_key:
        answers = base64.b64encode(GCE.asymmetric_encrypt(itip.crypto_tip_pub_key, json.dumps(answers).encode())).decode()

    db_set_internaltip_answers(session, itip.id, questionnaire_hash, answers)


class WBTipInstance(BaseHandler):
    """
    This interface expose the Whistleblower Tip.
    """
    check_roles = 'whistleblower'

    @inlineCallbacks
    def get(self):
        tip, crypto_tip_prv_key = yield get_wbtip(self.session.user_id, self.request.language)

        if crypto_tip_prv_key:
            tip = yield deferToThread(decrypt_tip, self.session.cc, crypto_tip_prv_key, tip)

        returnValue(tip)


class WBTipCommentCollection(BaseHandler):
    """
    This interface expose the Whistleblower Tip Comments
    """
    check_roles = 'whistleblower'

    def post(self):
        request = self.validate_message(self.request.content.read(), requests.CommentDesc)
        return create_comment(self.request.tid, self.session.user_id, request['content'])


class WBTipMessageCollection(BaseHandler):
    """
    This interface expose the Whistleblower Tip Messages
    """
    check_roles = 'whistleblower'

    def post(self, receiver_id):
        request = self.validate_message(self.request.content.read(), requests.CommentDesc)
        return create_message(self.request.tid, self.session.user_id, receiver_id, request['content'])


class WBTipWBFileHandler(WBFileHandler):
    check_roles = 'whistleblower'

    def user_can_access(self, session, tid, wbfile):
        wbtip_id = session.query(models.InternalTip.id) \
                          .filter(models.ReceiverTip.id == wbfile.receivertip_id,
                                  models.InternalTip.id == models.ReceiverTip.internaltip_id,
                                  models.InternalTip.tid == tid).one_or_none()

        return wbtip_id is not None and self.session.user_id == wbtip_id[0]

    def access_wbfile(self, session, wbfile):
        wbfile.downloads += 1
        log.debug("Download of file %s by whistleblower %s",
                  wbfile.id, self.session.user_id)

    @transact
    def download_wbfile(self, session, tid, file_id):
        wbfile, wbtip = db_get(session,
                               (models.WhistleblowerFile, models.WhistleblowerTip),
                               (models.WhistleblowerFile.id == file_id,
                                models.WhistleblowerFile.receivertip_id == models.ReceiverTip.id,
                                models.ReceiverTip.internaltip_id == models.WhistleblowerTip.id))

        if not self.user_can_access(session, tid, wbfile):
            raise errors.ResourceNotFound()

        self.access_wbfile(session, wbfile)

        return serializers.serialize_wbfile(session, wbfile), base64.b64decode(wbtip.crypto_tip_prv_key)


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
