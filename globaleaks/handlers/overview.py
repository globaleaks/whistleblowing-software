# -*- coding: UTF-8
#
#   overview
#   ********
# Implementation of the code executed when an HTTP client reach /overview/* URI


from globaleaks.settings import transact
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import authenticated, transport_security_check
from globaleaks import models

from twisted.internet.defer import inlineCallbacks
from globaleaks import utils
from globaleaks.utils import log


@transact
def collect_tip_overview(store):

    tip_description_list = []
    all_itips = store.find(models.InternalTip)

    for itip in all_itips:
        tip_description = {
            "id": itip.id,
            "creation_date": utils.pretty_date_time(itip.creation_date),
            "expiration_date": utils.pretty_date_time(itip.expiration_date),
            "context_id": itip.context_id,
            "pertinence_counter": itip.pertinence_counter,
            "status": itip.mark,
            "receivertips": [],
            "internalfiles": [],
            "receivers": [],
            "comments": [],
        }

        for rtip in itip.receivertips:
            tip_description['receivertips'].append({
                'access_counter': rtip.access_counter,
                'notification_date': utils.pretty_date_time(rtip.notification_date),
                'creation_date': utils.pretty_date_time(rtip.creation_date),
                'status': rtip.mark,
                'receiver_id': rtip.receiver.id,
                # last_access censored willingly
            })

        for ifile in itip.internalfiles:
            tip_description['internalfiles'].append({
                'name': ifile.name,
                'size': ifile.size,
                'status': ifile.mark,
                'content_type': ifile.content_type
            })

        for rcvr in itip.receivers:
            tip_description['receivers'].append({
                'receiver_id': rcvr.id
            })

        for comment in itip.comments:
            tip_description['comments'].append({
                'type': comment.type,
                'creation_date': utils.pretty_date_time(comment.creation_date),
            })

        # whistleblower tip has not a reference from itip, then:
        wbtip = store.find(models.WhistleblowerTip,
            models.WhistleblowerTip.internaltip_id == itip.id).one()

        if wbtip is not None:
            tip_description.update({
                'wb_access_counter': wbtip.access_counter,
                'wb_last_access': utils.pretty_date_time(wbtip.last_access)
            })
        else:
            tip_description.update({
                'wb_access_counter': u'Deleted', 'wb_last_access': u'Never'
            })

        tip_description_list.append(tip_description)

    return tip_description_list


@transact
def collect_users_overview(store):

    users_description_list = []

    all_receivers = store.find(models.Receiver)

    for receiver in all_receivers:
        # all public of private infos are stripped, because know between the Admin resources
        user_description = {
            'id': receiver.id,
            'failed_login': receiver.failed_login,
            'receiverfiles': [],
            'receivertips': [],
        }

        rcvr_files = store.find(models.ReceiverFile, models.ReceiverFile.receiver_id == receiver.id )
        for rfile in rcvr_files:
            user_description['receiverfiles'].append({
                'internatip_id': rfile.id,
                'downloads': rfile.downloads,
                'last_access': utils.pretty_date_time(rfile.last_access),
                'status': rfile.mark,
            })

        rcvr_tips = store.find(models.ReceiverTip, models.ReceiverTip.receiver_id == receiver.id )
        for rtip in rcvr_tips:
            user_description['receivertips'].append({
                'internaltip_id': rtip.id,
                'status': rtip.mark,
                'last_access': utils.pretty_date_time(rtip.last_access),
                'notification_date': utils.pretty_date_time(rtip.notification_date),
                'access_counter': rtip.access_counter,
            })

        users_description_list.append(user_description)

    return users_description_list


class Tips(BaseHandler):
    """
    A9

    /admin/overview/tips
    """

    @inlineCallbacks
    @transport_security_check('admin')
    @authenticated('admin')
    def get(self, *uriargs):
        """
        Parameters: None
        Response: NotYetDefinedList
        Errors: None
        """
        tips_complete_list = yield collect_tip_overview()
        log.debug("Tip overview counter: %d" % len(tips_complete_list) )

        self.set_status(200)
        self.finish(tips_complete_list)


class Users(BaseHandler):
    """
    AA

    /admin/overview/users
    """

    @inlineCallbacks
    @transport_security_check('admin')
    @authenticated('admin')
    def get(self, *uriargs):
        """
        Parameters: None
        Response: NotYetDefinedList
        Errors: None
        """
        users_complete_list = yield collect_users_overview()
        log.debug("Users overview counter: %d" % len(users_complete_list) )

        self.set_status(200)
        self.finish(users_complete_list)

