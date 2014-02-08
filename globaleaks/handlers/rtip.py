# -*- coding: UTF-8
#
#   rtip
#   ****
#
#   Contains all the logic for handling tip related operations, for the
#   receiver side. These classes are executed in the /rtip/* URI PATH 

from twisted.internet.defer import inlineCallbacks
from storm.expr import Desc

from globaleaks.handlers.base import BaseHandler, FileToken, CollectionToken
from globaleaks.handlers.authentication import transport_security_check, authenticated
from globaleaks.rest import requests
from globaleaks.utils.utility import log, pretty_date_time, utc_future_date, datetime_now
from globaleaks.utils.structures import Rosetta
from globaleaks.settings import transact, transact_ro, GLSetting
from globaleaks.models import Node, Comment, ReceiverFile, Message
from globaleaks.rest import errors
from globaleaks.security import access_tip

def receiver_serialize_internal_tip(internaltip, language=GLSetting.memory_copy.default_language):

    itip_dict = {
        'context_gus': unicode(internaltip.context.id),
        'creation_date' : unicode(pretty_date_time(internaltip.creation_date)),
        'expiration_date' : unicode(pretty_date_time(internaltip.expiration_date)),
        'download_limit' : int(internaltip.download_limit),
        'access_limit' : int(internaltip.access_limit),
        'mark' : unicode(internaltip.mark),
        'pertinence' : unicode(internaltip.pertinence_counter),
        'escalation_threshold' : unicode(internaltip.escalation_threshold),
        'fields' : dict(internaltip.wb_fields),

        # these two fields are at the moment unsent by the client, but kept
        # maintained in unitTest. (tickets in wishlist)
        'is_pertinent' : False,
        'global_delete' : False,
        # this field "inform" the receiver of the new expiration date that can
        # be set, only if PUT with extend = True is updated
        'potential_expiration_date' : \
            pretty_date_time(utc_future_date(seconds=internaltip.context.tip_timetolive)),
        'extend' : False,
    }

    # context_name and context_description are localized field
    mo = Rosetta()
    mo.acquire_storm_object(internaltip.context)
    for attr in ['name', 'description' ]:
        key = "context_%s" % attr
        itip_dict[key] = mo.dump_translated(attr, language)

    return itip_dict

def receiver_serialize_file(internalfile, receiverfile, receivertip_id):
    """
    ReceiverFile is the mixing between the metadata present in InternalFile
    and the Receiver-dependent, and for the client sake receivertip_id is
    required to create the download link
    """

    rfile_dict = {
        'href' : unicode("/rtip/" + receivertip_id + "/download/" + FileToken(receiverfile.id).id),
        # if the ReceiverFile has encrypted status, we append ".pgp" to the filename, to avoid mistake on Receiver side.
        'name' : ("%s.pgp" % internalfile.name) if receiverfile.status == ReceiverFile._status_list[2] else internalfile.name,
        'encrypted': True if receiverfile.status == ReceiverFile._status_list[2] else False,
        'sha2sum' : unicode(internalfile.sha2sum),
        'content_type' : unicode(internalfile.content_type),
        'creation_date' : unicode(pretty_date_time(internalfile.creation_date)),
        'size': int(receiverfile.size),
        'downloads': unicode(receiverfile.downloads)
    }
    return rfile_dict


@transact_ro
def get_files_receiver(store, user_id, tip_id):
    rtip = access_tip(store, user_id, tip_id)

    receiver_files = store.find(ReceiverFile,
        (ReceiverFile.internaltip_id == rtip.internaltip_id, ReceiverFile.receiver_id == rtip.receiver_id))

    files_list = []
    for receiverfile in receiver_files:
        internalfile = receiverfile.internalfile
        files_list.append(receiver_serialize_file(internalfile, receiverfile, tip_id))

    return files_list


@transact_ro
def get_internaltip_receiver(store, user_id, tip_id, language=GLSetting.memory_copy.default_language):
    rtip = access_tip(store, user_id, tip_id)

    tip_desc = receiver_serialize_internal_tip(rtip.internaltip)

    # are added here because part of ReceiverTip, not InternalTip
    tip_desc['access_counter'] = int(rtip.access_counter)
    tip_desc['expressed_pertinence'] = int(rtip.expressed_pertinence)
    tip_desc['id'] = unicode(rtip.id)
    tip_desc['receiver_id'] = unicode(user_id)

    node = store.find(Node).one()

    tip_desc['postpone_superpower'] = (node.postpone_superpower or
                                       rtip.internaltip.context.postpone_superpower or
                                       rtip.receiver.postpone_superpower)

    tip_desc['can_delete_submission'] = (node.can_delete_submission or
                                         rtip.internaltip.context.can_delete_submission or
                                         rtip.receiver.can_delete_submission)

    return tip_desc

@transact
def increment_receiver_access_count(store, user_id, tip_id):
    rtip = access_tip(store, user_id, tip_id)

    rtip.access_counter += 1
    rtip.last_access = datetime_now()

    if rtip.access_counter > rtip.internaltip.access_limit:
        raise errors.AccessLimitExceeded

    log.debug(
        "Tip %s access garanted to user %s access_counter %d on limit %d" %
       (rtip.id, rtip.receiver.name, rtip.access_counter, rtip.internaltip.access_limit)
    )
    return rtip.access_counter


@transact
def delete_receiver_tip(store, user_id, tip_id):
    """
    This operation is permitted to every receiver, and trigger
    a System comment on the Tip history.
    """
    rtip = access_tip(store, user_id, tip_id)

    comment = Comment()
    comment.content = "%s personally remove from this Tip" % rtip.receiver.name
    comment.system_content = dict({ "type" : 2,
                                    "receiver_name" : rtip.receiver.name})

    comment.internaltip_id = rtip.internaltip.id
    comment.author = u'System' # The printed line
    comment.type = Comment._types[2] # System
    comment.mark = Comment._marker[0] # Not Notified

    rtip.internaltip.comments.add(comment)

    store.remove(rtip)


@transact
def delete_internal_tip(store, user_id, tip_id):
    """
    Delete internalTip is possible only to Receiver with
    the dedicated property.
    """
    rtip = access_tip(store, user_id, tip_id)

    node = store.find(Node).one()

    if not (node.can_delete_submission or
            rtip.internaltip.context.can_delete_submission or
            rtip.receiver.can_delete_submission):
        raise errors.ForbiddenOperation

    store.remove(rtip.internaltip)


@transact
def manage_pertinence(store, user_id, tip_id, vote):
    """
    Assign in ReceiverTip the expressed vote (checks if already present)
    Roll over all the rTips with a vote
    re-count the Overall Pertinence
    Assign the Overall Pertinence to the InternalTip
    """
    rtip = access_tip(store, user_id, tip_id)

    # expressed_pertinence has these meanings:
    # 0 = unassigned
    # 1 = negative vote
    # 2 = positive vote

    if rtip.expressed_pertinence:
        raise errors.TipPertinenceExpressed

    rtip.expressed_pertinence = 2 if vote else 1

    vote_sum = 0
    for rtip in rtip.internaltip.receivertips:
        if not rtip.expressed_pertinence:
            continue
        if rtip.expressed_pertinence == 1:
            vote_sum -= 1
        else:
            vote_sum += 1

    rtip.internaltip.pertinence_counter = vote_sum
    return vote_sum

@transact
def postpone_expiration_date(store, user_id, tip_id):

    rtip = access_tip(store, user_id, tip_id)

    node = store.find(Node).one()

    if not (node.postpone_superpower or
            rtip.internaltip.context.postpone_superpower or
            rtip.receiver.postpone_superpower):

        raise errors.ExtendTipLifeNotEnabled()
    else:
        log.debug("Postpone check: Node %s, Context %s, Receiver %s" %(
            "True" if node.postpone_superpower else "False",
            "True" if rtip.internaltip.context.postpone_superpower else "False",
            "True" if rtip.receiver.postpone_superpower else "False"
        ))

    rtip.internaltip.expiration_date = \
        utc_future_date(seconds=rtip.internaltip.context.tip_timetolive)

    log.debug(" [%s] in %s has extended expiration time to %s" % (
        rtip.receiver.name,
        pretty_date_time(datetime_now()),
        pretty_date_time(rtip.internaltip.expiration_date)))

    comment = Comment()
    comment.system_content = dict({
           'type': "1", # the first kind of structured system_comments
           'receiver_name': rtip.receiver.name,
           'expire_on' : pretty_date_time(rtip.internaltip.expiration_date)
    })

    # remind: this is put just for debug, it's never used in the flow
    # and a system comment may have nothing to say except the struct
    comment.content = "%s %s %s " % (
                   rtip.receiver.name,
                   pretty_date_time(datetime_now()),
                   pretty_date_time(rtip.internaltip.expiration_date))

    comment.internaltip_id = rtip.internaltip.id
    comment.author = u'System' # The printed line
    comment.type = Comment._types[2] # System
    comment.mark = Comment._marker[4] # skipped

    rtip.internaltip.comments.add(comment)


class RTipInstance(BaseHandler):
    """
    RT1
    This interface expose the Tip.

    """

    @transport_security_check('wb')
    @authenticated('receiver')
    @inlineCallbacks
    def get(self, tip_id, *uriargs):
        """
        Parameters: None
        Response: actorsTipDesc
        Errors: InvalidTipAuthToken

        tip_id can be a valid tip_id (Receiver case) or a random one (because is
        ignored, only authenticated user with whistleblower token can access to
        the wb_tip, this is why tip_is is not checked if self.is_whistleblower)

        This method is decorated as @unauthenticated because in the handler
        the various cases are managed differently.
        """

        yield increment_receiver_access_count(self.current_user['user_id'], tip_id)
        answer = yield get_internaltip_receiver(self.current_user['user_id'], tip_id, self.request.language)
        answer['collection'] = '/rtip/' + CollectionToken(tip_id).id + '/collection'
        answer['files'] = yield get_files_receiver(self.current_user['user_id'], tip_id)

        self.set_status(200)
        self.finish(answer)

    @transport_security_check('wb')
    @authenticated('receiver')
    @inlineCallbacks
    def put(self, tip_id, *uriargs):
        """
        Some special operation over the Tip are handled here
        """

        request = self.validate_message(self.request.body, requests.actorsTipOpsDesc)

        if request['extend']:
            yield postpone_expiration_date(self.current_user['user_id'], tip_id)

        self.set_status(202) # Updated
        self.finish()

    @transport_security_check('wb')
    @authenticated('receiver')
    @inlineCallbacks
    def delete(self, tip_id, *uriargs):
        """
        Request: actorsTipOpsDesc
        Response: None
        Errors: ForbiddenOperation, TipGusNotFound

        global delete: is removed InternalTip and all the things derived
        personal delete: is removed the ReceiverTip and ReceiverFiles
        """

        request = self.validate_message(self.request.body, requests.actorsTipOpsDesc)

        if request['global_delete']:
            yield delete_internal_tip(self.current_user['user_id'], tip_id)
        else:
            yield delete_receiver_tip(self.current_user['user_id'], tip_id)

        self.set_status(200) # Success
        self.finish()


def receiver_serialize_comment(comment):
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
def get_comment_list_receiver(store, user_id, tip_id):
    rtip = access_tip(store, user_id, tip_id)

    comment_list = []
    for comment in rtip.internaltip.comments:
        comment_list.append(receiver_serialize_comment(comment))

    return comment_list


@transact
def create_comment_receiver(store, user_id, tip_id, request):
    rtip = access_tip(store, user_id, tip_id)

    comment = Comment()
    comment.content = request['content']
    comment.internaltip_id = rtip.internaltip.id
    comment.author = rtip.receiver.name # The printed line
    comment.type = Comment._types[0] # Receiver
    comment.mark = Comment._marker[0] # Not notified

    rtip.internaltip.comments.add(comment)

    return receiver_serialize_comment(comment)


class RTipCommentCollection(BaseHandler):
    """
    T2
    Interface use to read/write comments inside of a Tip, is not implemented as CRUD because we've not
    needs, at the moment, to delete/update comments once has been published. Comments is intended, now,
    as a stone written consideration about Tip reliability, therefore no editing and rethinking is
    permitted.
    """

    @transport_security_check('wb')
    @authenticated('receiver')
    @inlineCallbacks
    def get(self, tip_id, *uriargs):
        """
        Parameters: None
        Response: actorsCommentList
        Errors: InvalidTipAuthToken
        """

        comment_list = yield get_comment_list_receiver(self.current_user['user_id'], tip_id)

        self.set_status(200)
        self.finish(comment_list)

    @transport_security_check('wb')
    @authenticated('receiver')
    @inlineCallbacks
    def post(self, tip_id, *uriargs):
        """
        Request: actorsCommentDesc
        Response: actorsCommentDesc
        Errors: InvalidTipAuthToken, InvalidInputFormat, TipGusNotFound, TipReceiptNotFound
        """

        request = self.validate_message(self.request.body, requests.actorsCommentDesc)

        answer = yield create_comment_receiver(self.current_user['user_id'], tip_id, request)

        self.set_status(201) # Created
        self.finish(answer)


@transact_ro
def get_receiver_list_receiver(store, user_id, tip_id, language=GLSetting.memory_copy.default_language):

    rtip = access_tip(store, user_id, tip_id)

    receiver_list = []
    for rtip in rtip.internaltip.receivertips:

        receiver_desc = {
            "gpg_key_status": rtip.receiver.gpg_key_status,
            "can_delete_submission": rtip.receiver.can_delete_submission,
            "name": unicode(rtip.receiver.name),
            "receiver_gus": unicode(rtip.receiver.id),
            "receiver_level": int(rtip.receiver.receiver_level),
            "tags": rtip.receiver.tags,
            "access_counter": rtip.access_counter,
        }

        mo = Rosetta()
        mo.acquire_storm_object(rtip.receiver)
        receiver_desc["description"] = mo.dump_translated("description", language)

        receiver_list.append(receiver_desc)

    return receiver_list


class RTipReceiversCollection(BaseHandler):
    """
    T3
    This interface return the list of the Receiver active in a Tip.
    GET /tip/<auth_tip_id>/receivers
    """

    @transport_security_check('wb')
    @authenticated('receiver')
    @inlineCallbacks
    def get(self, tip_id):
        """
        Parameters: None
        Response: actorsReceiverList
        Errors: InvalidTipAuthToken
        """
        answer = yield get_receiver_list_receiver(self.current_user['user_id'], tip_id, self.request.language)

        self.set_status(200)
        self.finish(answer)

## Direct messages handling function,
# they are quite similar to the Comment, at the moment.
# differences: are personal, in the future can be E2E encrypted,
#              and do not exist system messages

def receiver_serialize_message(msg):

    return {
        'id' : unicode(msg.id),
        # 'unique_number': unicode(msg.receivertip_id): THINK HOW CAN BE DONE ?
        'creation_date' : unicode(pretty_date_time(msg.creation_date)),
        'content' : unicode(msg.content),
        'visualized' : bool(msg.visualized),
        'type' : unicode(msg.type),
        'author' : unicode(msg.author),
        'mark' : unicode(msg.mark)
    }

@transact
def get_messages_list(store, user_id, tip_id):

    rtip = access_tip(store, user_id, tip_id)

    msglist = store.find(Message, Message.receivertip_id == rtip.id)
    msglist.order_by(Desc(Message.creation_date))

    content_list = []
    for msg in msglist:
        content_list.append(receiver_serialize_message(msg))

        if not msg.visualized and msg.type == u'whistleblower':
            log.debug("Marking as readed message [%s] from %s" % (msg.content, msg.author))
            msg.visualized = True

    return content_list

@transact
def create_message_receiver(store, user_id, tip_id, request):

    rtip = access_tip(store, user_id, tip_id)

    msg = Message()
    msg.content = request['content']
    msg.receivertip_id = rtip.id
    msg.author = rtip.receiver.name
    msg.visualized = False

    # remind: is safest use this convention, and probably we've to
    # change in the whole code the usage of Model._type[ndx]
    msg.type = u'receiver'
    msg.mark = u'skipped'

    store.add(msg)

    return receiver_serialize_message(msg)


class ReceiverMsgCollection(BaseHandler):
    """
    RT6
    lost of all the messages exchanged with the WB, ability
    to send direct message to the WB.
    """

    @transport_security_check('wb')
    @authenticated('receiver')
    @inlineCallbacks
    def get(self, tip_id):

        answer = yield get_messages_list(self.current_user['user_id'], tip_id)

        self.set_status(200)
        self.finish(answer)

    @transport_security_check('wb')
    @authenticated('receiver')
    @inlineCallbacks
    def post(self, tip_id):
        """
        Request: actorsCommentDesc
        Response: actorsCommentDesc
        Errors: InvalidTipAuthToken, InvalidInputFormat, TipGusNotFound, TipReceiptNotFound
        """

        request = self.validate_message(self.request.body, requests.actorsCommentDesc)

        message = yield create_message_receiver(self.current_user['user_id'], tip_id, request)

        self.set_status(201) # Created
        self.finish(message)
