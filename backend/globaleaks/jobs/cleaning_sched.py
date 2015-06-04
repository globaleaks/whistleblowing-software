# -*- coding: UTF-8
#
#   cleaning_sched
#   **************
#
# Implementation of the cleaning operations (delete incomplete submission,
# delete expired tips, etc)

import os
from datetime import datetime, timedelta
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers import admin
from globaleaks.jobs.base import GLJob
from globaleaks.jobs.notification_sched import EventLogger, serialize_receivertip, db_save_events_on_db
from globaleaks.models import InternalTip, InternalFile, Receiver, ReceiverTip, ReceiverFile
from globaleaks.plugins.base import Event
from globaleaks.settings import transact, transact_ro, GLSetting
from globaleaks.utils.utility import log, datetime_to_ISO8601, ISO8601_to_datetime, utc_dynamic_date, datetime_now


__all__ = ['CleaningSchedule']


class ExpiringRTipEvent(EventLogger):
    def __init__(self):
        EventLogger.__init__(self)
        self.trigger = 'ExpiringTip'

    @transact
    def process_events(self, store):
        for receiver in store.find(Receiver):
            user_threshold = datetime_now() - timedelta(seconds=receiver.tip_expiration_threshold)
            for rtip in store.find(ReceiverTip, ReceiverTip.receiver_id == receiver.id):
                #if rtip.internaltip.expiration_date < user_threshold:
                self.process_event(store, rtip)

        db_save_events_on_db(store, self.events)

        log.debug("Notification: generated %d notification events of type %s" %
                  (len(self.events), self.trigger))

    def process_event(self, store, rtip):
        do_mail, receiver_desc = self.import_receiver(rtip.receiver)

        context_desc = admin.admin_serialize_context(store,
                                                     rtip.internaltip.context,
                                                     self.language)
        steps_desc = admin.db_get_context_steps(store,
                                                context_desc['id'],
                                                self.language)

        expiring_tip_desc = serialize_receivertip(rtip)

        self.events.append(Event(type=self.template_type,
                                 trigger=self.trigger,
                                 node_info={},
                                 receiver_info=receiver_desc,
                                 context_info=context_desc,
                                 steps_info=steps_desc,
                                 tip_info=expiring_tip_desc,
                                 subevent_info=None,
                                 do_mail=do_mail))


class CleaningSchedule(GLJob):
    @transact
    def perform_cleaning(self, store):
        for itip in store.find(InternalTip, InternalTip.expiration_date < datetime_now()):
            for ifile in itip.internalfiles:
                abspath = os.path.join(GLSetting.submission_path, ifile.file_path)

                if os.path.isfile(abspath):
                    log.debug("Removing internalfile %s" % abspath)
                    try:
                        os.remove(abspath)
                    except OSError as excep:
                        log.err("Unable to remove %s: %s" % (abspath, excep.strerror))

                rfiles = store.find(ReceiverFile, ReceiverFile.internalfile_id == ifile.id)
                for rfile in rfiles:
                    # The following code must be bypassed if rfile.file_path == ifile.filepath,
                    # this mean that is referenced the plaintext file instead having E2E.
                    if rfile.file_path == ifile.file_path:
                        continue

                    abspath = os.path.join(GLSetting.submission_path, rfile.file_path)

                    if os.path.isfile(abspath):
                        log.debug("Removing receiverfile %s" % abspath)
                        try:
                            os.remove(abspath)
                        except OSError as excep:
                            log.err("Unable to remove %s: %s" % (abspath, excep.strerror))

            store.remove(itip)

    @inlineCallbacks
    def operation(self):
        """
        This function, checks all the InternalTips and their expiration date.
        if expired InternalTips are found, it removes that along with
        all the related DB entries comment and tip related.
        """
        # Reset the exception tracking variable of GLSetting
        GLSetting.exceptions = {}

        yield self.perform_cleaning()
        yield ExpiringRTipEvent().process_events()
