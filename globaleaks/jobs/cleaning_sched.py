# -*- coding: UTF-8
#   cleaning_sched
#   **************
#
# Implementation of the cleaning operations (delete incomplete submission,
# delete expired tips, etc)

from twisted.internet.defer import inlineCallbacks

from globaleaks.settings import transact

from globaleaks.utils import log, pretty_date_time
from globaleaks.jobs.base import GLJob
from globaleaks.models import InternalTip, ReceiverTip, ReceiverFile, InternalFile, Comment
from datetime import datetime

__all__ = ['APSCleaning']

@transact
def get_tiptime_by_marker(store, marker):
    assert marker in InternalTip._marker

    itip_list = store.find(InternalTip, InternalTip.mark == marker)

    tipinfo_list = []
    for itip in itip_list:

        serialized_tipinfo = {
            'id': itip.id,
            'creation_date': pretty_date_time(itip.creation_date),
            'tip_life_seconds':  itip.context.tip_timetolive,
            'submission_life_seconds':  itip.context.submission_timetolive,
        }
        tipinfo_list.append(serialized_tipinfo)

    return tipinfo_list


class APSCleaning(GLJob):


    @inlineCallbacks
    def operation(self):
        """
        Goal of this function is to check all the submission not
        finalized, and, if the expiration time sets in the context has
        been reached, then clean the submission_gus along with the fields,
        and, if present, the uploaded folder/files.

        Second goal of this function, is to check all the internaltips
        and their expiration date, if match, remove that, all the folder,
        comment and tip related.
        """

        log.debug("Enterig cleaning sched")
        submissions = yield get_tiptime_by_marker(InternalTip._marker[0])
        for submission in submissions:
            creation_dateobj = datetime(submission['creation_time'])
            log.debug("submission readed date: %s" % pretty_date_time(creation_dateobj))
            # timedelta

        tips = yield get_tiptime_by_marker(InternalTip._marker[1])
        for tip in tips:
            creation_dateobj = datetime(tip['creation_time'])
            log.debug("tip readed date: %s" % pretty_date_time(creation_dateobj))
            # timedelta


