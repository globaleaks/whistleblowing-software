# -*- coding: UTF-8
#
#   cleaning_sched
#   **************
#
# Implementation of the cleaning operations (delete incomplete submission,
# delete expired tips, etc)

import os

from twisted.internet.defer import inlineCallbacks

from globaleaks.settings import transact, transact_ro, GLSetting
from globaleaks.utils.utility import log, is_expired, datetime_to_ISO8601, ISO8601_to_datetime, utc_dynamic_date
from globaleaks.jobs.base import GLJob
from globaleaks.models import InternalTip, ReceiverFile, InternalFile, Comment, ReceiverTip
from globaleaks.jobs.notification_sched import EventLogger, serialize_receivertip, save_event_db
from globaleaks.handlers.admin import admin_serialize_context, db_get_context_steps

__all__ = ['CleaningSchedule']


class UpcomingExpireEvent(EventLogger):

    def __init__(self):
        EventLogger.__init__(self)
        self.trigger = 'UpcomingExpireTip'

    @transact
    def switch_tip_marker_and_notify(self, store, tip_id):
        """
        In order to notify only once the ongoing expiration email,
        we have to switch marker.
        https://github.com/globaleaks/GlobaLeaks/issues/921
        """

        tit = store.find(InternalTip, InternalTip.id == tip_id).one()
        # This is the 'hackish' usage of the marker, read comment above
        tit.mark = u'submission'

        expiring_rtips = store.find(ReceiverTip, ReceiverTip.internaltip_id == tip_id)

        self.context_desc = admin_serialize_context(store, tit.context, self.language)

        self.steps_info_desc = db_get_context_steps(store, self.context_desc['id'], self.language)

        for ertip in expiring_rtips:
            self.do_mail = self.import_receiver(ertip.receiver)
            expiring_tip_desc = serialize_receivertip(ertip)
            self.append_event(tip_info=expiring_tip_desc, subevent_info=None)



@transact_ro
def get_tip_timings(store, marker):

    itip_list = store.find(InternalTip, InternalTip.mark == marker)

    tipinfo_list = []
    for itip in itip_list:

        comment_cnt = store.find(Comment, Comment.internaltip_id == itip.id).count()
        files_cnt = store.find(InternalFile, InternalFile.internaltip_id == itip.id).count()

        tip_timetolive = itip.context.tip_timetolive
        submission_timetolive = itip.context.submission_timetolive

        serialized_tipinfo = {
            'id': itip.id,
            'creation_date': datetime_to_ISO8601(itip.creation_date),
            'expiration_date': datetime_to_ISO8601(itip.expiration_date),
            'upcoming_expiration_date':
                datetime_to_ISO8601(utc_dynamic_date(itip.expiration_date, hours=-48)),
            'tip_life_seconds':  tip_timetolive,
            'submission_life_seconds':  submission_timetolive,
            'files': files_cnt,
            'comments': comment_cnt,
            'mark': itip.mark,
        }
        tipinfo_list.append(serialized_tipinfo)

    return tipinfo_list



@transact
def itip_cleaning(store, tip_id):
    """
    @param tip_id: aim for an InternalTip, and delete them.
    """
    tit = store.find(InternalTip, InternalTip.id == tip_id).one()

    if not tit: # gtfo
        log.err("Requested invalid InternalTip id in itip_cleaning! %s" % tip_id)
        return

    comments = store.find(Comment, Comment.internaltip_id == tip_id)
    log.debug("[-] Removing [%d comments] [%d files] [%d rtips] from an InternalTip" %
        (comments.count(), tit.internalfiles.count(), tit.receivertips.count() ))

    for ifile in tit.internalfiles:
        abspath = os.path.join(GLSetting.submission_path, ifile.file_path)
        ifname = unicode(ifile.name)

        if os.path.isfile(abspath):
            try:
                log.debug("Removing internalfile %s" % abspath)
                os.remove(abspath)
            except OSError as excep:
                log.err("Unable to remove %s: %s" % (abspath, excep.strerror))
        else:
            if ifile.mark != u'delivered': # Removed
                log.err("Unable to remove non existent internalfile %s (itip %s, internalfile %s(%d))" %
                        (abspath, tip_id, ifname, ifile.size))

        rfiles = store.find(ReceiverFile, ReceiverFile.internalfile_id == ifile.id)
        for rfile in rfiles:
            # The following code must be bypassed if rfile.file_path == ifile.filepath,
            # this mean that is referenced the plaintext file instead having E2E.
            if rfile.file_path == ifile.file_path:
                continue

            abspath = os.path.join(GLSetting.submission_path, rfile.file_path)

            if os.path.isfile(abspath):
                try:
                    log.debug("Removing receiverfile %s" % abspath)
                    os.remove(abspath)
                except OSError as excep:
                    log.err("Unable to remove %s: %s" % (abspath, excep.strerror))
            else:
                if rfile.status == 'encrypted': # encrypted is the only status where the file need to be deleted.
                                                # other cases are:
                                                # - reference: the ifile removal is handled above
                                                # - nokey and unavailable are the error cases where the file does not exist
                    log.err("Unable to remove non existent receiverfile %s (itip %s, internalfile %s(%d))" %
                            (abspath, tip_id, ifname, ifile.size))

    if tit.mark != u'submission':
        log.err("Developer ---> unexpected marker found: "
                "check https://github.com/globaleaks/GlobaLeaks/issues/921")

    store.remove(tit)


class CleaningSchedule(GLJob):

    @inlineCallbacks
    def operation(self):
        """
        this function, checks all the InternalTips and their expiration date.
        if expired InternalTips are found, it removes that along with
        all the related DB entries comment and tip related.

        this function checks also if two days are missing to the expiration
        date, in that case, sends an email of notice to the involved
        receivers. This is specify in issues #921 and #748, and need
        to be expanded with a database variable in the Receiver preference
        (can be done at the next database update)
        """

        tips = yield get_tip_timings(u'first')
        log.debug("[Tip timings routines / finalized  / upcoming expire ] #%d Tips" % len(tips))

        for tip in tips:

            if is_expired(ISO8601_to_datetime(tip['upcoming_expiration_date'])) and tip['mark'] == u'first':

                log.debug("Spot a tip matching the upcoming expiration date, "
                          "switching marker in 'submission', and triggering notification")

                expiring_tips_events = UpcomingExpireEvent()
                yield expiring_tips_events.switch_tip_marker_and_notify(tip['id'])
                yield save_event_db(expiring_tips_events.events)

        tips = yield get_tip_timings(u'submission')
        log.debug("[Tip timings routines / submission / expiration ] #%d Tips" % len(tips))

        for tip in tips:

            if is_expired(ISO8601_to_datetime(tip['expiration_date'])):
                log.info("Deleting an expired Tip (creation date: %s, expiration %s) files %d comments %d" %
                         (tip['creation_date'], tip['expiration_date'], tip['files'], tip['comments']) )
                yield itip_cleaning(tip['id'])


        # This operation, executed once every hour, clean the exception queue.
        # This is important because we've a limit on the amount of exception to
        # be sent, in order to do not flood our error service.
        GLSetting.exceptions = {}
