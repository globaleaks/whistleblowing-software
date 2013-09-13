# -*- coding: UTF-8
#
#   tip
#   ***
#
#   Contains all the logic for handling tip related operations, handled and
#   executed with /tip/* URI PATH interaction.

from twisted.internet.defer import inlineCallbacks
from storm.expr import Desc

from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import transport_security_check, unauthenticated
from globaleaks.rest import requests
from globaleaks.utils import log, pretty_date_time, l10n, utc_future_date, utc_dynamic_date

from globaleaks.settings import transact, transact_ro
from globaleaks.models import *
from globaleaks.rest import errors


def actor_serialize_internal_tip(internaltip, language=GLSetting.memory_copy.default_language):
    itip_dict = {
        'context_gus': unicode(internaltip.context.id),
        'creation_date' : unicode(pretty_date_time(internaltip.creation_date)),
        # XXX not yet used
        'last_activity' : unicode(pretty_date_time(internaltip.creation_date)),
        'expiration_date' : unicode(pretty_date_time(internaltip.expiration_date)),
        'download_limit' : int(internaltip.download_limit),
        'access_limit' : int(internaltip.access_limit),
        'mark' : unicode(internaltip.mark),
        'pertinence' : unicode(internaltip.pertinence_counter),
        'escalation_threshold' : unicode(internaltip.escalation_threshold),
        'fields' : dict(internaltip.wb_fields),

        # these fields are default false and selected as true only
        # if the receiver has the possibility. anyway are put here
        # because whistleblowers may have other flag, and I prefer
        # avoid in splitting shared default value among the handlers
        'im_whistleblower' : False,
        'im_receiver' : False,

        # This field is used angualr.js side, to know if show the option at
        # users interfaces. It's enabled node level by the admin
        'im_receiver_postponer' : False,

        # these two fields are at the moment unsent by the client, but kept
        # maintained in unitTest. (tickets in wishlist)
        'is_pertinent' : False,
        'global_delete' : False,
        # this field "inform" the receiver of the new expiration date that can
        # be set, only if PUT with extend = True is updated
        'potential_expiration_date' : \
            pretty_date_time(utc_dynamic_date(internaltip.expiration_date,
                                      seconds=internaltip.context.tip_timetolive)),
        'extend' : False,
    }

    # context_name and context_description are localized field
    for attr in ['name', 'description' ]:
        key = "context_%s" % attr
        itip_dict[key] = l10n(getattr(internaltip.context, attr), language)

    return itip_dict

def receiver_serialize_file(internalfile, receiverfile, receivertip_id):
    """
    ReceiverFile is the mixing between the metadata present in InternalFile
    and the Receiver-dependent, and for the client sake receivertip_id is
    required to create the download link
    """
    rfile_dict = {
        'href' : unicode("/tip/" + receivertip_id + "/download/" + receiverfile.id),
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


def wb_serialize_file(internalfile):
    wb_file_desc = {
        'name' : unicode(internalfile.name),
        'sha2sum' : unicode(internalfile.sha2sum),
        'content_type' : unicode(internalfile.content_type),
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

@transact_ro
def get_files_receiver(store, user_id, tip_id):
    rtip = strong_receiver_validate(store, user_id, tip_id)

    receiver_files = store.find(ReceiverFile,
        (ReceiverFile.internaltip_id == rtip.internaltip_id, ReceiverFile.receiver_id == rtip.receiver_id))

    files_list = []
    for receiverfile in receiver_files:
        internalfile = receiverfile.internalfile
        files_list.append(receiver_serialize_file(internalfile, receiverfile, tip_id))

    return files_list

def strong_receiver_validate(store, user_id, tip_id):
    """
    Utility: TODO description
    """

    rtip = store.find(ReceiverTip, ReceiverTip.id == unicode(tip_id)).one()

    if not rtip:
        raise errors.TipGusNotFound

    receiver = store.find(Receiver, Receiver.id == unicode(user_id)).one()

    if not receiver:
        raise errors.ReceiverGusNotFound

    if receiver.id != rtip.receiver.id:
        # This in attack!!
        raise errors.TipGusNotFound

    if not rtip.internaltip:
        # inconsistency! InternalTip removed but rtip not
        log.debug("Inconsintency + Access deny to a receiver on an expired submission! (%s)" %
                  receiver.name)
        raise errors.TipGusNotFound

    return rtip


@transact_ro
def get_internaltip_wb(store, tip_id, language=GLSetting.memory_copy.default_language):
    wbtip = store.find(WhistleblowerTip, WhistleblowerTip.id == unicode(tip_id)).one()

    if not wbtip or not wbtip.internaltip:
        raise errors.TipReceiptNotFound

    tip_desc = actor_serialize_internal_tip(wbtip.internaltip)
    tip_desc['access_counter'] = int(wbtip.access_counter)
    tip_desc['id'] = unicode(wbtip.id)

    tip_desc['im_whistleblower'] = True

    return tip_desc

@transact_ro
def get_internaltip_receiver(store, user_id, tip_id, language=GLSetting.memory_copy.default_language):
    rtip = strong_receiver_validate(store, user_id, tip_id)

    tip_desc = actor_serialize_internal_tip(rtip.internaltip)
    tip_desc['access_counter'] = int(rtip.access_counter)
    tip_desc['expressed_pertinence'] = int(rtip.expressed_pertinence)
    tip_desc['id'] = unicode(rtip.id)
    tip_desc['receiver_id'] = unicode(user_id)

    tip_desc['im_receiver'] = True

    node = store.find(Node).one()
    tip_desc['im_receiver_postponer'] = node.postpone_superpower

    return tip_desc

@transact
def increment_receiver_access_count(store, user_id, tip_id):
    rtip = strong_receiver_validate(store, user_id, tip_id)

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
    rtip = strong_receiver_validate(store, user_id, tip_id)

    comment = Comment()

    comment.content = "%s personally remove from this Tip" % rtip.receiver.name
    comment.system_content = dict({ "type" : 2,
                                    "receiver_name" : rtip.receiver.name,
                                    "now": pretty_date_time(datetime_now()) })

    comment.internaltip_id = rtip.internaltip.id
    comment.author = u'System' # The printed line
    comment.type = Comment._types[2] # System
    comment.mark = Comment._marker[0] # Not Notified
    store.add(comment)
    rtip.internaltip.comments.add(comment)

    store.remove(rtip)


@transact
def delete_internal_tip(store, user_id, tip_id):
    """
    Delete internalTip is possible only to Receiver with
    the dedicated properties. The ON CASCADE directive in SQL
    causes the removal of Comments, InternalFile, R|W tips
    """
    rtip = strong_receiver_validate(store, user_id, tip_id)

    if rtip.receiver.can_delete_submission:
        internaltip_backup = rtip.internaltip

        for receivertip in rtip.internaltip.receivertips:
            store.remove(receivertip)
        store.remove(internaltip_backup)

    else:
        raise errors.ForbiddenOperation


@transact
def manage_pertinence(store, user_id, tip_id, vote):
    """
    Assign in ReceiverTip the expressed vote (checks if already present)
    Roll over all the rTips with a vote
    re-count the Overall Pertinence
    Assign the Overall Pertinence to the InternalTip
    """
    rtip = strong_receiver_validate(store, user_id, tip_id)

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

    rtip = strong_receiver_validate(store, user_id, tip_id)

    node = store.find(Node).one()

    if not node.postpone_superpower:
        raise errors.ExtendTipLifeNotEnabled()

    rtip.internaltip.expiration_date = \
        utc_future_date(seconds=rtip.internaltip.context.tip_timetolive)

    log.debug(" [%s] in %s has extended expiration time to %s" % (
        rtip.receiver.name,
        pretty_date_time(datetime_now()),
        pretty_date_time(utc_dynamic_date(rtip.internaltip.expiration_date,
                         seconds=rtip.internaltip.context.tip_timetolive))))

    comment = Comment()

    comment.system_content = dict({
           'type': "1", # the first kind of structured system_comments
           'receiver_name': rtip.receiver.name,
           'now' : pretty_date_time(datetime_now()),
           'expire_on' : pretty_date_time(utc_dynamic_date(
                     rtip.internaltip.expiration_date,
                     seconds=rtip.internaltip.context.tip_timetolive))
    })

    # remind: this is put just for debug, it's never used in the flow
    # and a system comment may have nothing to say except the struct
    comment.content = "%s %s %s " % (
                   rtip.receiver.name,
                   pretty_date_time(datetime_now()),
                   utc_dynamic_date(rtip.internaltip.expiration_date,
                                    seconds=rtip.internaltip.context.tip_timetolive))

    comment.internaltip_id = rtip.internaltip.id
    comment.author = u'System' # The printed line
    comment.type = Comment._types[2] # System
    comment.mark = Comment._marker[4] # skipped

    store.add(comment)
    rtip.internaltip.comments.add(comment)


class TipInstance(BaseHandler):
    """
    T1
    This interface expose the Tip.

    Tip is the safe area, created with an expiration time, where Receivers (and optionally)
    Whistleblower can discuss about the submission, comments, collaborative voting, forward,
    promote, and perform other operation in this closed environment.
    In the request is present an unique token, aim to authenticate the users accessing to the
    resource, and giving accountability in resource accesses.
    Some limitation in access, security extensions an special token can exists, implemented by
    the extensions plugins.

    /tip/<tip_id>/
    tip_id is either a receiver_tip_gus or a whistleblower auth token
    """

    @transport_security_check('tip')
    @unauthenticated
    @inlineCallbacks
    def get(self, tip_id, *uriargs):
        """
        Parameters: None
        Response: actorsTipDesc
        Errors: InvalidTipAuthToken

        tip_id can be: a tip_gus for a receiver, or a WhistleBlower receipt, understand
        the format, help in addressing which kind of Tip need to be handled.
        """
        if self.is_whistleblower:
            answer = yield get_internaltip_wb(self.current_user['user_id'], self.request.language)
            answer['files'] = yield get_files_wb(self.current_user['user_id'])
        else:
            yield increment_receiver_access_count(self.current_user['user_id'], tip_id)
            answer = yield get_internaltip_receiver(self.current_user['user_id'], tip_id, self.request.language)
            answer['files'] = yield get_files_receiver(self.current_user['user_id'], tip_id)

        self.set_status(200)
        self.finish(answer)

    @transport_security_check('tip')
    @unauthenticated
    @inlineCallbacks
    def put(self, tip_id, *uriargs):
        """
        Request: actorsTipOpsDesc
        Response: None
        Errors: InvalidTipAuthToken, InvalidInputFormat, ForbiddenOperation

        This interface modify some tip status value. pertinence and complete removal
        are handled here.

        This interface return None, because may execute a delete operation. The client
        know which kind of operation has been requested. If a pertinence vote, would
        perform a refresh on get() API, if a delete, would bring the user in other places.

        When an uber-receiver decide to "total delete" a Tip, is handled by this call.
        """

        if self.is_whistleblower:
            raise errors.ForbiddenOperation

        request = self.validate_message(self.request.body, requests.actorsTipOpsDesc)

        if False and request['global_delete']: # disabled because client have not to send them,
            yield delete_internal_tip(self.current_user['user_id'], tip_id)

        elif False and request['is_pertinent']: # disabled too
            yield manage_pertinence(self.current_user['user_id'], tip_id, request['is_pertinent'])

        elif request['extend']:
            yield postpone_expiration_date(self.current_user['user_id'], tip_id)

        self.set_status(202) # Updated
        self.finish()

    @transport_security_check('tip')
    @unauthenticated
    @inlineCallbacks
    def delete(self, tip_id, *uriargs):
        """
        Request: None
        Response: None
        Errors: ForbiddenOperation, TipGusNotFound
        """

        if self.is_whistleblower:
            raise errors.ForbiddenOperation

        yield delete_receiver_tip(self.current_user['user_id'], tip_id)

        self.set_status(200) # Success
        self.finish()


def serialize_comment(comment):
    comment_desc = {
        'comment_id' : unicode(comment.id),
        'source' : unicode(comment.type),
        'content' : unicode(comment.content),
        'system_content' : comment.system_content if comment.system_content else {},
        'author' : unicode(comment.author),
        'creation_date' : unicode(pretty_date_time(comment.creation_date))
    }
    return comment_desc

def get_comment_list(internaltip):
    """
    @param internaltip:
    This function is used by both Receiver and WB.
    """

    comment_list = []
    for comment in internaltip.comments:
        comment_list.append(serialize_comment(comment))

    return comment_list

@transact_ro
def get_comment_list_wb(store, wb_tip_id):
    wb_tip = store.find(WhistleblowerTip,
                        WhistleblowerTip.id == unicode(wb_tip_id)).one()
    if not wb_tip:
        raise errors.TipReceiptNotFound

    return get_comment_list(wb_tip.internaltip)

@transact_ro
def get_comment_list_receiver(store, user_id, tip_id):
    rtip = strong_receiver_validate(store, user_id, tip_id)
    return get_comment_list(rtip.internaltip)

@transact
def create_comment_wb(store, wb_tip_id, request):
    wbtip = store.find(WhistleblowerTip, WhistleblowerTip.id== unicode(wb_tip_id)).one()

    if not wbtip:
        raise errors.TipReceiptNotFound

    comment = Comment()
    comment.content = request['content']
    comment.internaltip_id = wbtip.internaltip.id
    comment.author = u'whistleblower' # The printed line
    comment.type = Comment._types[1] # WB
    comment.mark = Comment._marker[0] # Not notified

    store.add(comment)
    wbtip.internaltip.comments.add(comment)

    return serialize_comment(comment)

@transact
def create_comment_receiver(store, user_id, tip_id, request):
    rtip = strong_receiver_validate(store, user_id, tip_id)

    comment = Comment()
    comment.content = request['content']
    comment.internaltip_id = rtip.internaltip.id
    comment.author = rtip.receiver.name # The printed line
    comment.type = Comment._types[0] # Receiver
    comment.mark = Comment._marker[0] # Not notified

    store.add(comment)
    rtip.internaltip.comments.add(comment)

    return serialize_comment(comment)


class TipCommentCollection(BaseHandler):
    """
    T2
    Interface use to read/write comments inside of a Tip, is not implemented as CRUD because we've not
    needs, at the moment, to delete/update comments once has been published. Comments is intended, now,
    as a stone written consideration about Tip reliability, therefore no editing and rethinking is
    permitted.
    """

    @transport_security_check('tip')
    @unauthenticated
    @inlineCallbacks
    def get(self, tip_id, *uriargs):
        """
        Parameters: None
        Response: actorsCommentList
        Errors: InvalidTipAuthToken
        """

        if self.is_whistleblower:
            comment_list = yield get_comment_list_wb(self.current_user['user_id'])
        else:
            comment_list = yield get_comment_list_receiver(self.current_user['user_id'], tip_id)

        self.set_status(200)
        self.finish(comment_list)

    @transport_security_check('tip')
    @unauthenticated
    @inlineCallbacks
    def post(self, tip_id, *uriargs):
        """
        Request: actorsCommentDesc
        Response: actorsCommentDesc
        Errors: InvalidTipAuthToken, InvalidInputFormat, TipGusNotFound, TipReceiptNotFound
        """

        request = self.validate_message(self.request.body, requests.actorsCommentDesc)

        if self.is_whistleblower:
            answer = yield create_comment_wb(self.current_user['user_id'], request)
        else:
            answer = yield create_comment_receiver(self.current_user['user_id'], tip_id, request)

        self.set_status(201) # Created
        self.finish(answer)


def serialize_receiver(receiver, access_counter, language=GLSetting.memory_copy.default_language):
    receiver_dict = {
        "can_delete_submission": receiver.can_delete_submission,
        "name": unicode(receiver.name),
        "receiver_gus": unicode(receiver.id),
        "receiver_level": int(receiver.receiver_level),
        "contexts": [],
        "tags": receiver.tags,
        "access_counter": access_counter,
    }
    for context in receiver.contexts:
        receiver_dict['contexts'].append(unicode(context.id))

    receiver_dict["description"] = l10n(receiver.description, language)

    return receiver_dict

@transact_ro
def get_receiver_list_wb(store, wb_tip_id, language):
    wb_tip = store.find(WhistleblowerTip, WhistleblowerTip.id == unicode(wb_tip_id)).one()
    if not wb_tip:
        raise errors.TipReceiptNotFound

    receiver_list = []
    for rtip in wb_tip.internaltip.receivertips:

        receiver_list.append(serialize_receiver( rtip.receiver, rtip.access_counter, language ))

    return receiver_list


@transact_ro
def get_receiver_list_receiver(store, user_id, tip_id, language):
    rtip = strong_receiver_validate(store, user_id, tip_id)

    receiver_list = []
    for rtip in rtip.internaltip.receivertips:

        receiver_list.append(serialize_receiver(rtip.receiver, rtip.access_counter, language ))

    return receiver_list


class TipReceiversCollection(BaseHandler):
    """
    T3
    This interface return the list of the Receiver active in a Tip.
    GET /tip/<auth_tip_id>/receivers
    """

    @transport_security_check('tip')
    @unauthenticated
    @inlineCallbacks
    def get(self, tip_id):
        """
        Parameters: None
        Response: actorsReceiverList
        Errors: InvalidTipAuthToken
        """
        if self.is_whistleblower:
            answer = yield get_receiver_list_wb(self.current_user['user_id'], self.request.language)
        elif self.is_receiver:
            answer = yield get_receiver_list_receiver(self.current_user['user_id'], tip_id, self.request.language)
        else:
            raise errors.NotAuthenticated

        self.set_status(200)
        self.finish(answer)

