# -*- encoding: utf-8 -*-
#
#   mailflush_sched
#   ***************
#
# Flush the email that has to be sent, is based on EventLog
# database table.

import random
from cyclone.util import ObjectDict as OD
from twisted.internet.defer import inlineCallbacks, Deferred, returnValue

from globaleaks.models import EventLogs, Notification
from globaleaks.handlers.admin import db_admin_serialize_node
from globaleaks.handlers.admin.notification import admin_serialize_notification
from globaleaks.jobs.base import GLJob
from globaleaks.settings import transact, transact_ro, GLSettings
from globaleaks.plugins import notification
from globaleaks.utils.mailutils import MIME_mail_build, sendmail
from globaleaks.utils.utility import deferred_sleep, log, datetime_now
from globaleaks.utils.logger import adminLog, LoggerNotification, mail_in_queue
from globaleaks.utils.templating import Templating
from globaleaks.utils.tempobj import TempObj

reactor_override = None


class LastHourMailQueue(object):
    """
    This class has only a class variable, used to stock the queue of the
    event happened on the latest minutes.
    """

    # This event queue is used by the tempObj
    event_queue = {}

    # This dict is used specifically for mail tracking
    per_receiver_lastmails = {}
    _counter = 0

    # This list is used to keep track of the currently suspended mail
    receivers_in_threshold = []

    # This is the utility dict required by TempObj
    blocked_in_queue = {}

    @staticmethod
    def mail_number(receiver_id):
        if receiver_id not in LastHourMailQueue.per_receiver_lastmails:
            return 0
        return LastHourMailQueue.per_receiver_lastmails[receiver_id]

    @staticmethod
    def get_incremental_number():
        LastHourMailQueue._counter += 1
        return LastHourMailQueue._counter


class ReceiverDeniedEmail(TempObj):
    def __init__(self, receiver_id, debug=False):
        self.debug = debug
        self.creation_date = datetime_now()
        self.receiver_id = receiver_id

        if receiver_id in LastHourMailQueue.receivers_in_threshold:
            log.err("Implementation error ? Receiver %s already present" % receiver_id)

        TempObj.__init__(self,
                         LastHourMailQueue.blocked_in_queue,
                         random.randint(0, 0xffff),
                         # seconds of validity:
                         GLSettings.memory_copy.notification_suspension_time,
                         reactor_override)

        log.info("Temporary disable emails for receiver %s for four hours" % self.receiver_id)
        LastHourMailQueue.receivers_in_threshold.append(receiver_id)
        self.expireCallbacks.append(self.reactivate_receiver_mails)

    def reactivate_receiver_mails(self):
        # Receiver return to be usable
        log.info("Expiring email suspension for %s" % self.receiver_id)
        if self.receiver_id not in LastHourMailQueue.receivers_in_threshold:
            log.err("Error while reactivating mails for a receiver")
        else:
            LastHourMailQueue.receivers_in_threshold.remove(self.receiver_id)

    def generate_anomaly_email(self, plausible_event):

        anomalevent = OD()
        anomalevent.type = u'receiver_notification_limit_reached'
        anomalevent.notification_settings = plausible_event.notification_settings
        anomalevent.node_info = plausible_event.node_info
        anomalevent.context_info = None
        anomalevent.receiver_info = plausible_event.receiver_info
        anomalevent.tip_info = None
        anomalevent.subevent_info = None
        anomalevent.orm_id = 0

        return anomalevent


class MailActivities(TempObj):
    def __init__(self, receiver_id, receiver_name, debug=False):

        self.debug = debug
        self.creation_date = datetime_now()
        self.receiver_id = receiver_id
        self.event_id = LastHourMailQueue.get_incremental_number()

        # This variable is just used for debug/log purpose
        self.receiver_name = receiver_name

        TempObj.__init__(self,
                         LastHourMailQueue.event_queue,
                         self.event_id,
                         # seconds of validity:
                         3600,
                         reactor_override)

        LastHourMailQueue.per_receiver_lastmails.setdefault(receiver_id, 0)
        LastHourMailQueue.per_receiver_lastmails[receiver_id] += 1

        self.expireCallbacks.append(self.manage_mail_expiration)

    def manage_mail_expiration(self):
        LastHourMailQueue.per_receiver_lastmails[self.receiver_id] -= 1

    def __repr__(self):
        return self.receiver_id


class NotificationMail:
    def __init__(self, plugin_used):
        self.plugin_used = plugin_used

    @inlineCallbacks
    def do_every_notification(self, eventOD):
        notify = self.plugin_used.do_notify(eventOD)

        if isinstance(notify, Deferred):
            notify.addCallback(self.every_notification_succeeded, eventOD.orm_id)
            notify.addErrback(self.every_notification_failed, eventOD.orm_id)
            yield notify
        else:
            yield self.every_notification_failed(None, eventOD.orm_id)

    @transact
    def every_notification_succeeded(self, store, result, event_id):
        if event_id:
            log.debug("Mail delivered correctly for event %s, [%s]" % (event_id, result))
            evnt = store.find(EventLogs, EventLogs.id == event_id).one()
            evnt.mail_sent = True
        else:
            log.debug("Mail (Digest|Anomaly) correctly sent")

    @transact
    def every_notification_failed(self, store, failure, event_id):
        if event_id:
            log.err("Mail delivery failure for event %s (%s)" % (event_id, failure))
            evnt = store.find(EventLogs, EventLogs.id == event_id).one()
            if not evnt:
                log.info("Race condition spotted: Event has been deleted during the notification process")
            else:
                evnt.mail_sent = True
        else:
            log.err("Mail (Digest|Anomaly) error")


@transact
def mark_event_as_sent(store, event_id):
    """
    Maybe for digest, maybe for filtering, this function mark an event as sent,
    but is not used in the "official notification success"
    """
    evnt = store.find(EventLogs, EventLogs.id == event_id).one()

    if not evnt:
        log.info("Race condition spotted: Event has been deleted during the notification process")
    else:
        evnt.mail_sent = True
        log.debug("Marked event [%s] as sent" % evnt.title)


@transact_ro
def load_complete_events(store, events_limit=GLSettings.notification_limit):
    """
    This function do not serialize, but make an OD() of the description.
    events_limit represent the amount of event that can be returned by the function,
    events to be notified are taken in account later.
    """
    node_desc = db_admin_serialize_node(store, GLSettings.defaults.language)

    event_list = []
    totaleventinqueue = store.find(EventLogs, EventLogs.mail_sent == False).count()
    storedevnts = store.find(EventLogs, EventLogs.mail_sent == False)[:events_limit * 3]

    debug_event_counter = {}
    for i, stev in enumerate(storedevnts):
        if len(event_list) == events_limit:
            log.debug("Maximum number of notification event reach (Mailflush) %d, after %d" %
                      (events_limit, i))
            break

        debug_event_counter.setdefault(stev.event_reference['kind'], 0)
        debug_event_counter[stev.event_reference['kind']] += 1

        if not stev.description['receiver_info']['tip_notification']:
            continue

        eventcomplete = OD()

        # node level information are not stored in the node, but fetch now
        eventcomplete.notification_settings = admin_serialize_notification(
            store.find(Notification).one(), stev.description['receiver_info']['language']
        )

        eventcomplete.node_info = node_desc

        # event level information are decoded form DB in the old 'Event'|nametuple format:
        eventcomplete.receiver_info = stev.description['receiver_info']
        eventcomplete.tip_info = stev.description['tip_info']
        eventcomplete.subevent_info = stev.description['subevent_info']
        eventcomplete.context_info = stev.description['context_info']

        eventcomplete.type = stev.description['type'] # 'Tip', 'Comment'
        eventcomplete.trigger = stev.event_reference['kind'] # 'blah' ...

        eventcomplete.orm_id = stev.id

        event_list.append(eventcomplete)

    if debug_event_counter:
        if totaleventinqueue > (events_limit * 3):
            log.debug("load_complete_events: %s from %d Events" %
                      (debug_event_counter, totaleventinqueue ))
        else:
            log.debug("load_complete_events: %s from %d Events, with a protection limit of %d" %
                      (debug_event_counter, totaleventinqueue, events_limit * 3 ))

    return event_list


def filter_notification_event(notifque):
    """
    :param notifque: the current notification event queue
    :return: a modified queue in the case some email has not to be sent
    Basically performs two filtering; they are defined in:
     1) issue #444
     2) issue #798
    """

    # Here we collect the Storm event of Files having as key the Tip
    files_event_by_tip = {}

    _tmp_list = []
    return_filtered_list = []
    # to be smoked Storm.id
    orm_id_to_be_skipped = []

    for ne in notifque:
        if ne['trigger'] !=  u'Tip':
            continue
        files_event_by_tip.update({ ne['tip_info']['id'] : [] })

    log.debug("Filtering function: iterating over %d Tip" % len(files_event_by_tip.keys()))
    # not files_event_by_tip contains N keys with an empty list,
    # I'm looping two times because dict has random ordering
    for ne in notifque:

        if GLSettings.memory_copy.disable_receiver_notification_emails:
            orm_id_to_be_skipped.append(ne['orm_id'])
            continue

        if ne['trigger'] != u'File':
            _tmp_list.append(ne)
            continue

        if ne['tip_info']['id'] in files_event_by_tip:
            orm_id_to_be_skipped.append(ne['orm_id'])
        else:
            _tmp_list.append(ne)


    if len(orm_id_to_be_skipped):
        if GLSettings.memory_copy.disable_receiver_notification_emails:
            log.debug("All the %d mails will be marked as Sent because Admin has disable notification" %
                      len(orm_id_to_be_skipped))
        else:
            log.debug("Filtering function: Marked %d Files notification to be suppressed as part of the submission" %
                      len(orm_id_to_be_skipped))

    for ne in _tmp_list:
        receiver_id = ne['receiver_info']['id']

        # It add automatically a mail in to the last hour email queue,
        # events here expire after 1 hour; this means that if receiver
        # get one email every 3 minutes, with default threshold (20).
        # NEVER trigger this alarm, because at the 21 the first is
        # already expired.
        MailActivities(receiver_id, ne['receiver_info']['name'])

        email_sent_last_60min = LastHourMailQueue.mail_number(receiver_id)

        if receiver_id in LastHourMailQueue.receivers_in_threshold:
            log.debug("Receiver %s is currently suspended against new mail" %
                      receiver_id)
            orm_id_to_be_skipped.append(ne['orm_id'])
            continue

        if email_sent_last_60min >= GLSettings.memory_copy.notification_threshold_per_hour:
            log.info("Threshold reach of %d email with limit of %d for receiver %s" % (
                email_sent_last_60min,
                GLSettings.memory_copy.notification_threshold_per_hour,
                receiver_id)
            )
            rde = ReceiverDeniedEmail(receiver_id)

            # Append
            anomaly_event = rde.generate_anomaly_email(ne)
            return_filtered_list.append(anomaly_event)

            orm_id_to_be_skipped.append(ne['orm_id'])
            continue

        return_filtered_list.append(ne)

    log.debug("Mails filtering completed passing from #%d to #%d events" %
              (len(notifque), len(return_filtered_list)))

    # return the new list of event and the list of Storm.id
    return return_filtered_list, orm_id_to_be_skipped


class MailflushSchedule(GLJob):
    name = "Mailflush"

    # sorry for the double negation, we are sleeping two seconds below.
    skip_sleep = False

    def ping_mail_flush(self, notification_settings, receivers_synthesis):
        """
        TODO This function should be implemented as a clean and testable plugin in the
        way defined in plugin/base.py and plugin/notification.py, and/or is the opportunity
        to review these classes, at the moment is a simplified version that just create a
        ping email and send it via sendmail.
        """
        for _, data in receivers_synthesis.iteritems():

            receiver_dict, winks = data

            receiver_name = receiver_dict['name']
            receiver_email = receiver_dict['ping_mail_address']

            fakeevent = OD()
            fakeevent.type = u'ping_mail'
            fakeevent.node_info = None
            fakeevent.context_info = None
            fakeevent.receiver_info = receiver_dict
            fakeevent.tip_info = None
            fakeevent.subevent_info = {'counter': winks}

            body = Templating().format_template(
                notification_settings['ping_mail_template'], fakeevent)
            title = Templating().format_template(
                notification_settings['ping_mail_title'], fakeevent)

            # so comfortable for a developer!! :)
            source_mail_name = GLSettings.developer_name if GLSettings.devel_mode \
                else GLSettings.memory_copy.notif_source_name
            message = MIME_mail_build(source_mail_name,
                                      GLSettings.memory_copy.notif_source_email,
                                      receiver_name,
                                      receiver_email,
                                      title,
                                      body)

            fakeevent2 = OD()
            fakeevent2.type = "Ping mail for %s (%d info)" % (receiver_email, winks)

            return sendmail(authentication_username=GLSettings.memory_copy.notif_username,
                            authentication_password=GLSettings.memory_copy.notif_password,
                            from_address= GLSettings.memory_copy.notif_source_email,
                            to_address= [receiver_email],
                            message_file=message,
                            smtp_host=GLSettings.memory_copy.notif_server,
                            smtp_port=GLSettings.memory_copy.notif_port,
                            security=GLSettings.memory_copy.notif_security,
                            event=fakeevent2)

    @inlineCallbacks
    def operation(self):
        """
        Notification has to manage two kind of data: some triggered by the whistleblower activities,
        and some others triggered by "other". the wb-flow-actions are flushed/can be not flushed based
        on some conditions, but the others kind of event now are always reported. that's why they are at
        the beginning
        """
        UNEXPECTED_AMOUNT_OF_QUEUE_LOGS = 10
        logger_events = yield mail_in_queue()

        if len(logger_events) > UNEXPECTED_AMOUNT_OF_QUEUE_LOGS:
            adminLog(['warning'], 'MAIL_QUEUE_0', [ len(logger_events) ])

        if len(logger_events):
            for le in logger_events:
                mailinfo = LoggerNotification.log_event_mail_generation(le)
                yield LoggerNotification.send_log_email(
                    mailinfo['admin_email'],
                    mailinfo['message'] )

        queue_events = yield load_complete_events()

        if not len(queue_events):
            returnValue(None)

        # remove from this list the event that has not to be sent, for example,
        # the Files uploaded during the first submission, like issue #444 (zombie edition)
        filtered_events, to_be_suppressed = filter_notification_event(queue_events)

        if len(to_be_suppressed):
            for eid in to_be_suppressed:
                yield mark_event_as_sent(eid)

        plugin = getattr(notification, GLSettings.notification_plugins[0])()
        # This wrap calls plugin/notification.MailNotification
        notifcb = NotificationMail(plugin)

        for qe_pos, qe in enumerate(filtered_events):
            yield notifcb.do_every_notification(qe)

            if not self.skip_sleep:
                yield deferred_sleep(2)

        # This is the notification of the ping, if configured
        receivers_synthesis = {}
        for qe in filtered_events:
            if not qe.receiver_info['ping_notification']:
                continue

            if qe.receiver_info['id'] not in receivers_synthesis:
                receivers_synthesis[qe.receiver_info['id']] = [qe.receiver_info, 1]
            else:
                receivers_synthesis[qe.receiver_info['id']][1] += 1

        if len(receivers_synthesis.keys()):
            # I'm taking the element [0] of the list but every element has the same
            # notification settings; this value is passed to ping_mail_flush at
            # it is needed by Templating()
            yield self.ping_mail_flush(filtered_events[0].notification_settings,
                                       receivers_synthesis)

