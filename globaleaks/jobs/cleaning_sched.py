# -*- coding: UTF-8
#   cleaning_sched
#   **************
#
# Implementation of the cleaning operations (delete incomplete submission,
# delete expired tips, etc)

from twisted.internet.defer import inlineCallbacks

from globaleaks.settings import transact

from globaleaks.utils import log, pretty_date_time, is_expired
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

def iso2dateobj(str) :
    try:
        ret = datetime.strptime(str, "%Y-%m-%dT%H:%M:%S")
    except ValueError :
        ret = datetime.strptime(str, "%Y-%m-%dT%H:%M:%S.%f")
        ret.replace(microsecond=0)
    return ret

@transact
def itip_cleaning(store, id):
    """
    @param id: aim for an InternalTip, and delete them.
    """
    tit = store.find(InternalTip, InternalTip.id == id).one()

    if not tit: # gtfo
        log.err("Requested invalid InternalTip id in itip_cleaning! %s" % id)
        return

    store.remove(tit)
    log.debug("Removed InternalTip id %s" % id)



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
            if is_expired(iso2dateobj(submission['creation_date']), seconds=submission['submission_life_seconds']):
                itip_cleaning(submission['id'])

        tips = yield get_tiptime_by_marker(InternalTip._marker[1])
        for tip in tips:
            if is_expired(iso2dateobj(tip['creation_date']), seconds=tip['tip_life_seconds']):
                itip_cleaning(tip['id'])


