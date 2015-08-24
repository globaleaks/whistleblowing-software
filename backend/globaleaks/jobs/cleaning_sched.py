# -*- coding: UTF-8
#
#   cleaning_sched
#   **************
#
# Implementation of the cleaning operations (delete incomplete submission,
# delete expired tips, etc)

from datetime import timedelta
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers import admin
from globaleaks.handlers.rtip import db_delete_itip
from globaleaks.jobs.base import GLJob
from globaleaks.jobs.notification_sched import EventLogger, serialize_receivertip, db_save_events_on_db
from globaleaks.models import InternalTip, Receiver, ReceiverTip, Stats
from globaleaks.plugins.base import Event
from globaleaks.settings import transact, transact_ro, GLSettings
from globaleaks.utils.utility import log, datetime_now


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
                if rtip.internaltip.expiration_date < user_threshold:
                    self.process_event(store, rtip)

        db_save_events_on_db(store, self.events)

        log.debug("Notification: generated %d notification events of type %s" %
                  (len(self.events), self.trigger))

    def process_event(self, store, rtip):
        do_mail, receiver_desc = self.import_receiver(rtip.receiver)

        context_desc = admin.admin_serialize_context(store,
                                                     rtip.internaltip.context,
                                                     self.language)

        expiring_tip_desc = serialize_receivertip(rtip, self.language)

        self.events.append(Event(type=self.template_type,
                                 trigger=self.trigger,
                                 node_info={},
                                 receiver_info=receiver_desc,
                                 context_info=context_desc,
                                 tip_info=expiring_tip_desc,
                                 subevent_info=None,
                                 do_mail=do_mail))


class CleaningSchedule(GLJob):
    name = "Cleaning"

    @transact_ro
    def get_cleaning_map(self, store):
        subjects = store.find(InternalTip, InternalTip.expiration_date < datetime_now())
        log.info("Removal of %d InternalTips starts soon" % subjects.count())

        itip_id_list = []
        for itip in subjects:
            itip_id_list.append(itip.id)

        return itip_id_list

    @transact
    def perform_cleaning(self, itip_id, store):
        itip = store.find(InternalTip, InternalTip.id == itip_id)
        db_delete_itip(store, itip)

    @transact
    def perform_stats_cleaning(self, store):
        # delete stats older than 3 months
        store.find(Stats, Stats.start < datetime_now() - timedelta(3*(365/12))).remove()

    @inlineCallbacks
    def operation(self):
        """
        This function, checks all the InternalTips and their expiration date.
        if expired InternalTips are found, it removes that along with
        all the related DB entries comment and tip related.
        """
        # Reset the exception tracking variable of GLSettings
        GLSettings.exceptions = {}
        GLSettings.exceptions_email_count = 0

        itip_list_id = yield self.get_cleaning_map()
        if itip_list_id:
            for itip_id in itip_list_id:
                yield self.perform_cleaning(itip_id)

        yield self.perform_stats_cleaning()
        yield ExpiringRTipEvent().process_events()
