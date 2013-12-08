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
from globaleaks.utils.utility import log, pretty_date_time
from globaleaks.utils.structures import Rosetta
from globaleaks.settings import transact, transact_ro, GLSetting
from globaleaks.models import WhistleblowerTip, Comment
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


@transact_ro
def get_internaltip_wb(store, tip_id, language=GLSetting.memory_copy.default_language):
    wbtip = store.find(WhistleblowerTip, WhistleblowerTip.id == unicode(tip_id)).one()

    if not wbtip:
        raise errors.TipReceiptNotFound

    tip_desc = wb_serialize_tip(wbtip.internaltip)

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

    @transport_security_check('tip')
    @authenticated('wb')
    @inlineCallbacks
    def get(self, *uriargs):
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
        'source' : unicode(comment.type),
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

    @transport_security_check('tip')
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

    @transport_security_check('tip')
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
    """

    wb_tip = store.find(WhistleblowerTip,
                        WhistleblowerTip.id == unicode(wb_tip_id)).one()

    if not wb_tip:
        raise errors.TipReceiptNotFound

    receiver_list = []
    for rtip in wb_tip.internaltip.receivertips:

        receiver_desc = {
            "name": unicode(rtip.receiver.name),
            "receiver_gus": unicode(rtip.receiver.id),
            "tags": rtip.receiver.tags,
            "access_counter" : rtip.access_counter,
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

    @transport_security_check('tip')
    @authenticated('wb')
    @inlineCallbacks
    def get(self, tip_id):
        """
        Parameters: None
        Response: actorsReceiverList
        Errors: InvalidTipAuthToken
        """
        answer = yield get_receiver_list_wb(self.current_user['user_id'], self.request.language)

        self.set_status(200)
        self.finish(answer)

