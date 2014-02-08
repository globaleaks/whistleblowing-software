# -*- coding: UTF-8
#
#   wbtip
#   *****
#
#   Contains all the logic for handling tip related operations, managed by
#   the whistleblower, handled and executed within /wbtip/* URI PATH interaction.

from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import transport_security_check, authenticated
from globaleaks.rest import requests
from globaleaks.utils.utility import log, pretty_date_time, datetime_now
from globaleaks.utils.structures import Rosetta
from globaleaks.settings import transact, transact_ro, GLSetting
from globaleaks.models import WhistleblowerTip, Comment, Message, ReceiverTip
from globaleaks.rest import errors


def wb_serialize_tip(internaltip, language=GLSetting.memory_copy.default_language):
    itip_dict = {
        'context_gus': unicode(internaltip.context.id),
        'creation_date' : unicode(pretty_date_time(internaltip.creation_date)),
        'last_activity' : unicode(pretty_date_time(internaltip.creation_date)),
        'expiration_date' : unicode(pretty_date_time(internaltip.expiration_date)),
        'download_limit' : int(internaltip.download_limit),
        'access_limit' : int(internaltip.access_limit),
        'mark' : unicode(internaltip.mark),
        'pertinence' : unicode(internaltip.pertinence_counter),
        'escalation_threshold' : unicode(internaltip.escalation_threshold),
        'fields' : dict(internaltip.wb_fields),
    }

    # context_name and context_description are localized field
    mo = Rosetta()
    mo.acquire_storm_object(internaltip.context)
    for attr in ['name', 'description' ]:
        key = "context_%s" % attr
        itip_dict[key] = mo.dump_translated(attr, language)

    return itip_dict

def wb_serialize_file(internalfile):
    wb_file_desc = {
        'name' : unicode(internalfile.name),
        'sha2sum' : unicode(internalfile.sha2sum),
        'content_type' : unicode(internalfile.content_type),
        'creation_date' : unicode(pretty_date_time(internalfile.creation_date)),
        'size': int(internalfile.size),
    }
    return wb_file_desc


@transact_ro
def get_files_wb(store, wb_tip_id):
    wbtip = store.find(WhistleblowerTip, WhistleblowerTip.id == unicode(wb_tip_id)).one()

    file_list = []
    for internalfile in wbtip.internaltip.internalfiles:
        file_list.append(wb_serialize_file(internalfile))

    file_list.reverse()

    return file_list


@transact
def get_internaltip_wb(store, tip_id, language=GLSetting.memory_copy.default_language):
    wbtip = store.find(WhistleblowerTip, WhistleblowerTip.id == unicode(tip_id)).one()

    if not wbtip:
        raise errors.TipReceiptNotFound

    # there is not a limit in the WB access counter, but is kept track
    wbtip.access_counter += 1

    tip_desc = wb_serialize_tip(wbtip.internaltip, language)

    # two elements from WhistleblowerTip
    tip_desc['access_counter'] = int(wbtip.access_counter)
    tip_desc['id'] = unicode(wbtip.id)

    return tip_desc


class WbTipInstance(BaseHandler):
    """
    WT1
    This interface expose the Whistleblower Tip.

    Tip is the safe area, created with an expiration time, where Receivers (and optionally)
    Whistleblower can discuss about the submission, comments, collaborative voting, forward,
    promote, and perform other operation in this closed environment.
    In the request is present an unique token, aim to authenticate the users accessing to the
    resource, and giving accountability in resource accesses.
    """

    @transport_security_check('wb')
    @authenticated('wb')
    @inlineCallbacks
    def get(self):
        """
        Parameters: None
        Response: actorsTipDesc
        Errors: InvalidTipAuthToken

        Check the user id (in the whistleblower case, is authenticated and
        contain the internaltip)
        """

        answer = yield get_internaltip_wb(self.current_user['user_id'], self.request.language)
        answer['files'] = yield get_files_wb(self.current_user['user_id'])

        self.set_status(200)
        self.finish(answer)


def wb_serialize_comment(comment):
    comment_desc = {
        'comment_id' : unicode(comment.id),
        'type' : unicode(comment.type),
        'content' : unicode(comment.content),
        'system_content' : comment.system_content if comment.system_content else {},
        'author' : unicode(comment.author),
        'creation_date' : unicode(pretty_date_time(comment.creation_date))
    }

    return comment_desc


@transact_ro
def get_comment_list_wb(store, wb_tip_id):
    wb_tip = store.find(WhistleblowerTip,
                        WhistleblowerTip.id == unicode(wb_tip_id)).one()

    if not wb_tip:
        raise errors.TipReceiptNotFound

    comment_list = []
    for comment in wb_tip.internaltip.comments:
        comment_list.append(wb_serialize_comment(comment))

    return comment_list


@transact
def create_comment_wb(store, wb_tip_id, request):
    wbtip = store.find(WhistleblowerTip,
                       WhistleblowerTip.id == unicode(wb_tip_id)).one()

    if not wbtip:
        raise errors.TipReceiptNotFound

    comment = Comment()
    comment.content = request['content']
    comment.internaltip_id = wbtip.internaltip.id
    comment.author = u'whistleblower' # The printed line
    comment.type = Comment._types[1] # WB
    comment.mark = Comment._marker[0] # Not notified

    wbtip.internaltip.comments.add(comment)

    return wb_serialize_comment(comment)

class WbTipCommentCollection(BaseHandler):
    """
    T2
    Interface use to read/write comments inside of a Tip, is not implemented as CRUD because we've not
    needs, at the moment, to delete/update comments once has been published. Comments is intended, now,
    as a stone written consideration about Tip reliability, therefore no editing and rethinking is
    permitted.
    """

    @transport_security_check('wb')
    @authenticated('wb')
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: actorsCommentList
        Errors: InvalidTipAuthToken
        """
        wb_comment_list = yield get_comment_list_wb(self.current_user['user_id'])

        self.set_status(200)
        self.finish(wb_comment_list)

    @transport_security_check('wb')
    @authenticated('wb')
    @inlineCallbacks
    def post(self, *uriargs):
        """
        Request: actorsCommentDesc
        Response: actorsCommentDesc
        Errors: InvalidTipAuthToken, InvalidInputFormat, TipGusNotFound, TipReceiptNotFound
        """

        request = self.validate_message(self.request.body, requests.actorsCommentDesc)
        answer = yield create_comment_wb(self.current_user['user_id'], request)

        self.set_status(201) # Created
        self.finish(answer)


@transact_ro
def get_receiver_list_wb(store, wb_tip_id, language=GLSetting.memory_copy.default_language):
    """
    @return:
        This function contain the serialization of the receiver, this function is
        used only by /wbtip/receivers API

        The returned struct contain information on read/unread messages
    """

    wb_tip = store.find(WhistleblowerTip,
                        WhistleblowerTip.id == unicode(wb_tip_id)).one()

    if not wb_tip:
        raise errors.TipReceiptNotFound

    # This part of code is used only in the short time between the first
    # WB access and the delivery schedule. In this moment
    # wb_tip.internaltips.receivertips is EMPTY, therefore we force
    # the Receivers values below
    if not wb_tip.internaltip.receivertips.count():
        receiver_list = []

        log.debug("Early access from the WB to the Tip (creation_date: %s),"\
                  " Receiver not yet present: fallback on receiver list" %
                  pretty_date_time(wb_tip.creation_date))

        for receiver in wb_tip.internaltip.receivers:

            # This is the reduced version of Receiver serialization
            receiver_desc = {
                "name": unicode(receiver.name),
                "receiver_gus": unicode(receiver.id),
                "id": unicode(receiver.id),
                "gpg_key_status": receiver.gpg_key_status,
                "tags": receiver.tags,
                "access_counter" : 0,
                "unread_messages" : 0,
                "read_messages" : 0,
                "your_messages" : 0,
                "creation_date" : unicode(pretty_date_time(datetime_now())),
                # XXX ReceiverTip last activity ?
            }

            mo = Rosetta()
            mo.acquire_storm_object(receiver)
            receiver_desc["description"] = mo.dump_translated("description", language)
            receiver_list.append(receiver_desc)

        return receiver_list
    else:
        receiver_list = []
        for rtip in wb_tip.internaltip.receivertips:


            your_messages = store.find(Message,
                                       Message.receivertip_id == rtip.id,
                                       Message.type == u'whistleblower').count()

            unread_messages = store.find(Message,
                                         Message.receivertip_id == rtip.id,
                                         Message.type == u'receiver',
                                         Message.visualized == False).count()

            read_messages = store.find(Message,
                                       Message.receivertip_id == rtip.id,
                                       Message.type == u'receiver',
                                       Message.visualized == True).count()

            # if you change something here, check also 20 lines before!
            receiver_desc = {
                "name": unicode(rtip.receiver.name),
                "receiver_gus": unicode(rtip.receiver.id),
                "id": unicode(rtip.receiver.id),
                "tags": rtip.receiver.tags,
                "access_counter" : rtip.access_counter,
                "unread_messages" : unread_messages,
                "read_messages" : read_messages,
                "your_messages" : your_messages,
                "creation_date" : unicode(pretty_date_time(datetime_now())),
                # XXX ReceiverTip last activity ?
            }

            mo = Rosetta()
            mo.acquire_storm_object(rtip.receiver)
            receiver_desc["description"] = mo.dump_translated("description", language)

            receiver_list.append(receiver_desc)

        return receiver_list


class WbTipReceiversCollection(BaseHandler):
    """
    T3
    This interface return the list of the Receiver active in a Tip.
    GET /tip/<auth_tip_id>/receivers
    """

    @transport_security_check('wb')
    @authenticated('wb')
    @inlineCallbacks
    def get(self):
        """
        Parameters: None
        Response: actorsReceiverList
        Errors: InvalidTipAuthToken
        """
        answer = yield get_receiver_list_wb(self.current_user['user_id'], self.request.language)

        self.set_status(200)
        self.finish(answer)

## Direct messages handling function

def wb_serialize_message(msg):
    return {
        'id' : unicode(msg.id),
        'creation_date' : unicode(pretty_date_time(msg.creation_date)),
        'content' : unicode(msg.content),
        'visualized' : bool(msg.visualized),
        'type' : unicode(msg.type),
        'author' : unicode(msg.author),
        'mark' : unicode(msg.mark)
    }

@transact
def get_messages_content(store, wb_tip_id, receiver_id):
    """
    Get the messages content and mark all the unread
    messages as "read"
    """
    wb_tip = store.find(WhistleblowerTip,
                        WhistleblowerTip.id == unicode(wb_tip_id)).one()

    if not wb_tip:
        raise errors.TipReceiptNotFound

    rtip = store.find(ReceiverTip, ReceiverTip.internaltip_id == wb_tip.internaltip.id,
                      ReceiverTip.receiver_id == unicode(receiver_id)).one()

    if not rtip:
        raise errors.TipGusNotFound

    messages = store.find(Message, Message.receivertip_id == rtip.id)

    messages_list = []
    for msg in messages:
        messages_list.append(wb_serialize_message(msg))

        if not msg.visualized and msg.type == u'receiver':
            log.debug("Marking as readed message [%s] from %s" % (msg.content, msg.author))
            msg.visualized = True

    store.commit()
    return messages_list


@transact
def create_message_wb(store, wb_tip_id, receiver_id, request):

    wb_tip = store.find(WhistleblowerTip,
                        WhistleblowerTip.id == unicode(wb_tip_id)).one()

    if not wb_tip:
        log.err("Invalid wb_tip supply: %s" % wb_tip)
        raise errors.TipReceiptNotFound

    rtip = store.find(ReceiverTip, ReceiverTip.internaltip_id == wb_tip.internaltip.id,
                                   ReceiverTip.receiver_id == unicode(receiver_id)).one()

    if not rtip:
        log.err("No ReceiverTip found: receiver_id %s itip %s" %
                (receiver_id, wb_tip.internaltip.id))
        raise errors.TipGusNotFound

    msg = Message()
    msg.content = request['content']
    msg.receivertip_id = rtip.id
    msg.author = u'Whistleblower'
    msg.visualized = False

    # remind: is safest use this convention, and probably we've to
    # change in the whole code the usage of Model._type[ndx]
    msg.type = u'whistleblower'
    msg.mark = u'not notified'

    try:
        store.add(msg)
    except Exception as dberror:
        log.err("Unable to add WB message from %s: %s" % (rtip.receiver.name, dberror))
        raise dberror

    return wb_serialize_message(msg)


class WbMessageCollection(BaseHandler):
    """
    W5
    """

    @transport_security_check('wb')
    @authenticated('wb')
    @inlineCallbacks
    def get(self, receiver_id):

        messages = yield get_messages_content(self.current_user['user_id'], receiver_id)

        self.set_status(200)
        self.finish(messages)

    @transport_security_check('wb')
    @authenticated('wb')
    @inlineCallbacks
    def post(self, receiver_id):

        request = self.validate_message(self.request.body, requests.actorsCommentDesc)

        message = yield create_message_wb(self.current_user['user_id'], receiver_id, request)

        self.set_status(201) # Created
        self.finish(message)
