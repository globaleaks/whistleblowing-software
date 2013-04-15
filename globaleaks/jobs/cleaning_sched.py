# -*- coding: UTF-8
#   cleaning_sched
#   **************
#
# Implementation of the cleaning operations (delete incomplete submission,
# delete expired tips, etc)

import os

from twisted.internet.defer import inlineCallbacks

from globaleaks.settings import transact, GLSetting

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

    for ifile in tit.internalfiles:
        if not os.path.isfile(ifile.file_path):
            log.err("Unable to remove not existent file, in itip %s has an internalfile %s(%d) missing on FS (%s)" %
                (id, ifile.name, ifile.size, ifile.file_path) )
        else:
            try:
                os.unlink( os.path.join(GLSetting.submission_path, ifile.file_path) )
            except OSError as excep:
                log.err("Unable to remove %s: %s" %
                    (ifile.file_path, excep.strerror) )

    store.remove(tit)


@transact
def debug_count_itips_by_marker(store):
    info_list = []
    for marker in InternalTip._marker:
        single_info = {
            marker: store.find(InternalTip, InternalTip.mark == marker).count()
        }
        info_list.append(single_info)

    return info_list


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

        submissions = yield get_tiptime_by_marker(InternalTip._marker[0])
        for submission in submissions:
            if is_expired(iso2dateobj(submission['creation_date']), seconds=submission['submission_life_seconds']):
                log.debug("Deleting an unfinished submission (creation date: %s)" % submission['creation_date'])
                yield itip_cleaning(submission['id'])

        tips = yield get_tiptime_by_marker(InternalTip._marker[1])
        for tip in tips:
            if is_expired(iso2dateobj(tip['creation_date']), seconds=tip['tip_life_seconds']):
                log.debug("Deleting an unfinished tip (creation date: %s)" % tip['creation_date'])
                yield itip_cleaning(tip['id'])


