# -*- coding: utf-8
#
#   wbtip
#   *****
#
#   Contains all the logic for handling tip related operations, managed by
#   the whistleblower, handled and executed within /wbtip/* URI PATH interaction.
from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.rtip import serialize_comment, serialize_message, db_get_itip_comment_list, WBFileHandler
from globaleaks.handlers.submission import serialize_usertip, \
    db_save_questionnaire_answers, db_serialize_archived_questionnaire_schema
from globaleaks.orm import transact
from globaleaks.rest import errors, requests
from globaleaks.utils.utility import log, datetime_now, datetime_to_ISO8601


def wb_serialize_ifile(store, ifile):
    return {
        'id': ifile.id,
        'creation_date': datetime_to_ISO8601(ifile.creation_date),
        'name': ifile.name,
        'size': ifile.size,
        'content_type': ifile.content_type
    }


def wb_serialize_wbfile(store, wbfile):
    receiver_id = store.find(models.ReceiverTip.receiver_id,
                             models.ReceiverTip.id == wbfile.receivertip_id,
                             models.ReceiverTip.tid == wbfile.tid).one()

    return {
        'id': wbfile.id,
        'creation_date': datetime_to_ISO8601(wbfile.creation_date),
        'name': wbfile.name,
        'description': wbfile.description,
        'size': wbfile.size,
        'content_type': wbfile.content_type,
        'author': receiver_id
    }


def db_get_rfile_list(store, tid, itip_id):
    return [wb_serialize_ifile(store, ifile) for ifile in store.find(models.InternalFile, internaltip_id=itip_id, tid=tid)]


def db_get_wbfile_list(store, tid, wbtip_id):
    wbfiles = store.find(models.WhistleblowerFile,
                         models.WhistleblowerFile.receivertip_id == models.ReceiverTip.id,
                         models.ReceiverTip.internaltip_id == wbtip_id,
                         tid=tid)

    return [wb_serialize_wbfile(store, wbfile) for wbfile in wbfiles]


def db_get_wbtip(store, tid, wbtip_id, language):
    wbtip, itip = models.db_get(store,
                                (models.WhistleblowerTip, models.InternalTip),
                                models.WhistleblowerTip.id == wbtip_id,
                                models.InternalTip.id == wbtip_id,
                                models.InternalTip.tid == tid)

    itip.wb_access_counter += 1
    itip.wb_last_access = datetime_now()

    return serialize_wbtip(store, wbtip, itip, language)


@transact
def get_wbtip(store, tid, wbtip_id, language):
    return db_get_wbtip(store, tid, wbtip_id, language)


def serialize_wbtip(store, wbtip, itip, language):
    ret = serialize_usertip(store, wbtip, itip, language)

    # filter submission progressive
    # to prevent a fake whistleblower to assess every day how many
    # submissions are received by the platform.
    del ret['progressive']

    ret['id'] = wbtip.id
    ret['comments'] = db_get_itip_comment_list(store, itip.tid, itip)
    ret['rfiles'] = db_get_rfile_list(store, itip.tid, wbtip.id)
    ret['wbfiles'] = db_get_wbfile_list(store, itip.tid, wbtip.id)

    return ret


@transact
def create_comment(store, tid, wbtip_id, request):
    internaltip = models.db_get(store, models.InternalTip, id=wbtip_id, tid=tid)

    internaltip.update_date = internaltip.wb_last_access = datetime_now()

    comment = models.Comment()
    comment.tid = tid
    comment.content = request['content']
    comment.internaltip_id = wbtip_id
    comment.type = u'whistleblower'
    store.add(comment)

    return serialize_comment(store, comment)


@transact
def get_itip_message_list(store, tid, wbtip_id, receiver_id):
    """
    Get the messages content and mark all the unread
    messages as "read"
    """
    rtip = store.find(models.ReceiverTip,
                      models.ReceiverTip.internaltip_id == wbtip_id,
                      models.InternalTip.id == wbtip_id,
                      models.ReceiverTip.receiver_id == receiver_id,
                      tid=tid).one()

    return [serialize_message(store, message) for message in store.find(models.Message, models.Message.receivertip_id == rtip.id, tid=tid)]

@transact
def create_message(store, tid, wbtip_id, receiver_id, request):
    rtip_id, internaltip = store.find((models.ReceiverTip.id, models.InternalTip),
                                      models.ReceiverTip.internaltip_id == wbtip_id,
                                      models.InternalTip.id == wbtip_id,
                                      models.ReceiverTip.receiver_id == receiver_id,
                                      models.ReceiverTip.tid == tid).one()


    if rtip_id is None:
        raise errors.ModelNotFound(models.ReceiverTip)

    internaltip.update_date = internaltip.wb_last_access = datetime_now()

    msg = models.Message()
    msg.tid = tid
    msg.content = request['content']
    msg.receivertip_id = rtip_id
    msg.type = u'whistleblower'
    store.add(msg)

    return serialize_message(store, msg)


@transact
def update_identity_information(store, tid, tip_id, identity_field_id, identity_field_answers, language):
    internaltip = models.db_get(store, models.InternalTip, id=tip_id, tid=tid)

    if internaltip.identity_provided:
        return

    questionnaire = db_serialize_archived_questionnaire_schema(store, tid, internaltip.questionnaire_hash, language)
    for step in questionnaire:
        for field in step['children']:
            if field['id'] == identity_field_id and field['id'] == 'whistleblower_identity':
                db_save_questionnaire_answers(store, tid, internaltip.id,
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
        """
        Parameters: None
        Response: actorsTipDesc

        Check the user id (in the whistleblower case, is authenticated and
        contain the internaltip)
        """
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
        """
        Request: CommentDesc
        Response: CommentDesc
        Errors: InvalidInputFormat, ModelNotFound
        """
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

    def user_can_access(self, store, tid, wbfile):
        wbtip_id = store.find(models.WhistleblowerTip.id,
                              models.WhistleblowerTip.id == models.InternalTip.id,
                              models.InternalTip.id == models.ReceiverTip.internaltip_id,
                              models.ReceiverTip.id == wbfile.receivertip_id,
                              models.ReceiverTip.tid == tid).one()

        return wbtip_id is not None and self.current_user.user_id == wbtip_id

    def access_wbfile(self, store, wbfile):
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
