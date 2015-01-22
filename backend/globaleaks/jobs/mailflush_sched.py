# -*- encoding: utf-8 -*-
#
#   mailflush_sched
#   ***************
#
# Flush the email that has to be sent, is based on EventLog
# database table.

from cyclone.util import ObjectDict as OD
from twisted.internet.defer import inlineCallbacks

from globaleaks.utils.mailutils import MIME_mail_build, sendmail
from globaleaks.models import EventLogs, Notification
from globaleaks.handlers.admin import db_admin_serialize_node
from globaleaks.handlers.admin.notification import admin_serialize_notification
from globaleaks.jobs.base import GLJob
from globaleaks.settings import transact, transact_ro, GLSetting
from globaleaks.plugins import notification
from globaleaks.utils.utility import deferred_sleep, log
from globaleaks.utils.templating import Templating


class NotificationMail:

    def __init__(self, plugin_used):
        self.plugin_used = plugin_used

    @inlineCallbacks
    def do_every_notification(self, eventOD):

        notify = self.plugin_used.do_notify(eventOD)

        if notify:
            notify.addCallback(self.every_notification_succeeded, eventOD.storm_id)
            notify.addErrback(self.every_notification_failed, eventOD.storm_id)
            yield notify

    @transact
    def every_notification_succeeded(self, store, result, event_id):

        log.debug("Mail delivered correctly for event %s, [%s]" % (event_id, result))
        evnt = store.find(EventLogs, EventLogs.id == event_id).one()
        evnt.mail_sent = True

    @transact
    def every_notification_failed(self, store, failure, event_id):

        log.err("Mail delivery failure for event %s (%s)" % (event_id, failure))
        evnt = store.find(EventLogs, EventLogs.id == event_id).one()
        evnt.mail_sent = True


@transact_ro
def load_complete_events(store):
    """
    _complete_ is explicit because do not serialize, but make an OD() of the description.

    Note: there are a bug in this logic: is are loaded, let say, 3k mail, only 50 are flush
    in the time window between each mailflush_sched. The next time, 2950 are put in this
    list, and so on. is better that in this loop only the first email is taken, and then
    the loop continue, one mail per time.
    """

    node_desc = db_admin_serialize_node(store, GLSetting.defaults.default_language)

    event_list = []
    storedevnts = store.find(EventLogs, EventLogs.mail_sent == False)

    for stev in storedevnts:

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
        eventcomplete.steps_info = stev.description['steps_info']

        eventcomplete.type = stev.description['type'] # 'Tip', 'Comment'
        eventcomplete.trigger = stev.event_reference['kind'] # 'plaintext_blah' ...

        eventcomplete.storm_id = stev.id

        event_list.append(eventcomplete)

    return event_list


class MailflushSchedule(GLJob):

    def ping_mail_flush(self, notification_settings, receivers_syntesis):
        """
        TODO This function should be implemented as a clean and testable pligin in the
        way defined in plugin/base.py and plugin/notification.py, and/or is the opportunity
        to review these classes, at the moment is a simplified version that just create a
        ping email and send it via sendmail.
        """

        for receiver_id, data in receivers_syntesis.iteritems():

            receiver_dict, winks = data

            receiver_name = receiver_dict['name']
            receiver_email = receiver_dict['ping_mail_address']

            fakeevent = OD()
            fakeevent.type = u'ping_mail'
            # we've to accomplish the same amount of Attrs looked in templating.py TemplatClass
            fakeevent.node_info = None
            fakeevent.context_info = None
            fakeevent.steps_info = None
            fakeevent.receiver_info = receiver_dict
            fakeevent.tip_info = None
            fakeevent.subevent_info = {'counter': winks}

            body = Templating().format_template(
                notification_settings['ping_mail_template'], fakeevent)
            title = Templating().format_template(
                notification_settings['ping_mail_title'], fakeevent)

            message = MIME_mail_build(GLSetting.memory_copy.notif_source_name,
                                      GLSetting.memory_copy.notif_source_email,
                                      receiver_name,
                                      receiver_email,
                                      title,
                                      body)

            fakeevent2 = OD()
            fakeevent2.type = "Ping mail for %s (%d info)" % (receiver_email, winks)

            return sendmail(authentication_username=GLSetting.memory_copy.notif_username,
                            authentication_password=GLSetting.memory_copy.notif_password,
                            from_address= GLSetting.memory_copy.notif_source_email,
                            to_address= [receiver_email],
                            message_file=message,
                            smtp_host=GLSetting.memory_copy.notif_server,
                            smtp_port=GLSetting.memory_copy.notif_port,
                            security=GLSetting.memory_copy.notif_security,
                            event=fakeevent2)

    @inlineCallbacks
    def operation(self):

        queue_events = yield load_complete_events()

        plugin = getattr(notification, GLSetting.notification_plugins[0])()
        notifcb = NotificationMail(plugin)

        notification_counter = 0

        for qe in queue_events:

            notifcb.do_every_notification(qe)
            yield deferred_sleep(3)

            # note, this settings has to be multiply for 3 (seconds in this iteration)
            # and the results (30 * 3) need to be shorter than the periodic running time
            # specified in runner.py, that's why is set at FIVE minutes.
            if notification_counter >= GLSetting.notification_limit:
                log.debug("Notification counter has reached the suggested limit: %d (tip)" %
                          notification_counter)
                break

        # TODO: implement ping as an appropriate plugin
        receivers_synthesis = {}
        for qe in queue_events:

            if not qe.receiver_info['ping_notification']:
                continue

            if qe.receiver_info['id'] not in receivers_synthesis:
                receivers_synthesis[qe.receiver_info['id']] = [qe.receiver_info, 1]
            else:
                receivers_synthesis[qe.receiver_info['id']][1] += 1

        if len(receivers_synthesis.keys()):
            # I'm taking the element [0] of the list but every element has the same
            # notification setting. is passed to ping_mail_flush because of the Templating()
            yield self.ping_mail_flush(queue_events[0].notification_settings,
                                       receivers_synthesis)

        # Whishlist: implement digest as an appropriate plugin



