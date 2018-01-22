# -*- coding: utf-8 -*-
#
# Handlers dealing with tip interface for whistleblowers (wbtip)
from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.rtip import serialize_comment, serialize_message, db_get_itip_comment_list, WBFileHandler
from globaleaks.handlers.submission import serialize_usertip, \
    db_save_questionnaire_answers, db_serialize_archived_questionnaire_schema
from globaleaks.orm import transact
from globaleaks.rest import errors, requests
from globaleaks.utils.utility import log, datetime_now, datetime_to_ISO8601


def wb_serialize_ifile(session, ifile):
    return {
        'id': ifile.id,
        'creation_date': datetime_to_ISO8601(ifile.creation_date),
        'name': ifile.name,
        'size': ifile.size,
        'content_type': ifile.content_type
    }


def wb_serialize_wbfile(session, wbfile):
    receiver_id = session.query(models.ReceiverTip.receiver_id) \
                         .filter(models.ReceiverTip.id == wbfile.receivertip_id).one()

    return {
        'id': wbfile.id,
        'creation_date': datetime_to_ISO8601(wbfile.creation_date),
        'name': wbfile.name,
        'description': wbfile.description,
        'size': wbfile.size,
        'content_type': wbfile.content_type,
        'author': receiver_id
    }


def db_get_rfile_list(session, tid, itip_id):
    return [wb_serialize_ifile(session, ifile) for ifile in session.query(models.InternalFile) \
                                                                   .filter(models.InternalFile.internaltip_id == itip_id,
                                                                           models.InternalTip.id == itip_id)]


def db_get_wbfile_list(session, tid, itip_id):
    wbfiles = session.query(models.WhistleblowerFile) \
                     .filter(models.WhistleblowerFile.receivertip_id == models.ReceiverTip.id,
                             models.ReceiverTip.internaltip_id == itip_id)

    return [wb_serialize_wbfile(session, wbfile) for wbfile in wbfiles]


def db_get_wbtip(session, tid, itip_id, language):
    itip = models.db_get(session,
                         models.InternalTip,
                         models.InternalTip.id == itip_id,
                         models.InternalTip.tid == tid)

    itip.wb_access_counter += 1
    itip.wb_last_access = datetime_now()

    return serialize_wbtip(session, itip, language)


@transact
def get_wbtip(session, tid, itip_id, language):
    return db_get_wbtip(session, tid, itip_id, language)


def serialize_wbtip(session, itip, language):
    ret = serialize_usertip(session, itip, itip, language)

    ret['comments'] = db_get_itip_comment_list(session, itip.tid, itip)
    ret['rfiles'] = db_get_rfile_list(session, itip.tid, itip.id)
    ret['wbfiles'] = db_get_wbfile_list(session, itip.tid, itip.id)

    return ret


@transact
def create_comment(session, tid, wbtip_id, request):
    internaltip = session.query(models.InternalTip).filter(models.InternalTip.id == wbtip_id, models.InternalTip.tid == tid)

    internaltip.update_date = internaltip.wb_last_access = datetime_now()

    comment = models.Comment()
    comment.content = request['content']
    comment.internaltip_id = wbtip_id
    comment.type = u'whistleblower'
    session.add(comment)
    session.flush()

    return serialize_comment(session, comment)


@transact
def get_itip_message_list(session, tid, wbtip_id, receiver_id):
    messages = session.query(models.Message) \
                      .filter(models.Message.receivertip_id == models.ReceiverTip.id,
                              models.ReceiverTip.internaltip_id == wbtip_id,
                              models.ReceiverTip.receiver_id == receiver_id,
                              models.InternalTip.id == wbtip_id,
                              models.InternalTip.tid == tid)

    return [serialize_message(session, message) for message in messages]

@transact
def create_message(session, tid, wbtip_id, receiver_id, request):
    rtip_id, internaltip = session.query(models.ReceiverTip.id, models.InternalTip) \
                                  .filter(models.ReceiverTip.internaltip_id == wbtip_id,
                                          models.InternalTip.id == wbtip_id,
                                          models.ReceiverTip.receiver_id == receiver_id,
                                          models.InternalTip.tid == tid).one_or_none()

    if rtip_id is None:
        raise errors.ModelNotFound(models.ReceiverTip)

    internaltip.update_date = internaltip.wb_last_access = datetime_now()

    msg = models.Message()
    msg.content = request['content']
    msg.receivertip_id = rtip_id
    msg.type = u'whistleblower'
    session.add(msg)
    session.flush()

    return serialize_message(session, msg)


@transact
def update_identity_information(session, tid, tip_id, identity_field_id, identity_field_answers, language):
    internaltip = models.db_get(session, models.InternalTip, models.InternalTip.id == tip_id, models.InternalTip.tid == tid)

    if internaltip.identity_provided:
        return

    aqs = session.query(models.ArchivedSchema).filter(models.ArchivedSchema.hash == internaltip.questionnaire_hash).one()

    questionnaire = db_serialize_archived_questionnaire_schema(session, aqs.schema, language)
    for step in questionnaire:
        for field in step['children']:
            if field['id'] == identity_field_id and field['id'] == 'whistleblower_identity':
                db_save_questionnaire_answers(session, tid, internaltip.id,
                                              {identity_field_id: [identity_field_answers]})
                now = datetime_now()
                internaltip.update_date = now
                internaltip.wb_last_access = now
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
    check_roles = 'whistleblower'

    def get(self):
        return get_wbtip(self.request.tid, self.current_user.user_id, self.request.language)


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
        return create_comment(self.request.tid, self.current_user.user_id, request)


class WBTipMessageCollection(BaseHandler):
    """
    This interface return the lists of the private messages exchanged between
    whistleblower and the specified receiver requested in GET

    Supports the creation of a new message for the requested receiver
    """
    check_roles = 'whistleblower'

    def get(self, receiver_id):
        return get_itip_message_list(self.request.tid, self.current_user.user_id, receiver_id)

    def post(self, receiver_id):
        request = self.validate_message(self.request.content.read(), requests.CommentDesc)

        return create_message(self.request.tid, self.current_user.user_id, receiver_id, request)


class WBTipWBFileHandler(WBFileHandler):
    check_roles = 'whistleblower'
    upload_handler = True

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
