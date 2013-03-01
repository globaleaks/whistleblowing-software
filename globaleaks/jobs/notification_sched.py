# -*- coding: UTF-8
#
#   notification_sched
#   ******************
#
# Notification implementation, documented along the others asynchronous
# operations, in Architecture and in jobs/README.md

from twisted.internet.defer import inlineCallbacks

from globaleaks.jobs.base import GLJob
from globaleaks.plugins.base import Event
from globaleaks import models
from globaleaks.settings import transact
from globaleaks.utils import log
from globaleaks.plugins import notification
from globaleaks import settings


from collections import namedtuple

Event = namedtuple('Event',
                   ['type', 'trigger', 'af', 'rf', 'tip_id'])

class APSNotification(GLJob):


    @transact
    def _get_notification_settings(self, store):
        """
        notification setting need to contains bot template
        and systemsettings
        """
        from globaleaks.handlers.admin import admin_serialize_notification

        notif = store.find(models.Notification).one()

        if not notif.server:
            return None

        return admin_serialize_notification(notif)


    @transact
    def do_tip_notification(self, store, notification_settings):
        log.debug("Entering in Tip Notification")

        # for cplugin in settings.notification_plugins:
        cplugin = settings.notification_plugins[0]

        # the configuration of the node need to be checked here, because do_notify
        # it's something with obscure callback based

        plugin = getattr(notification, cplugin)(notification_settings)

        not_notified_tips = store.find(models.ReceiverTip,
            models.ReceiverTip.mark == models.ReceiverTip._marker[0]
        )

        for rtip in not_notified_tips:

            # admin fields are the same for all the notification, atm

            if not rtip.receiver.notification_fields.has_key('mail_address'):
                log.debug("Receiver %s lack of email address!" % rtip.receiver.name)
                # this is actually impossible, but a check is never bad
                return

            event = Event(type=u'tip', trigger='Tip', af=notification_settings,
                          rf=rtip.receiver.notification_fields,
                          tip_id=rtip)

            notify = plugin.do_notify(event)

            @notify.addCallback
            def success(result):
                log.debug('OK Notification for %s' % rtip.receiver.username )
                rtip.mark = models.ReceiverTip._marker[1]

            @notify.addErrback
            def error(result):
                log.debug('FAIL Notification for %s FAIL' % rtip.receiver.username )
                rtip.mark = models.ReceiverTip._marker[2]

            yield notify

        log.debug("Completed notification of %d receiver tips " % not_notified_tips.count() )


    @inlineCallbacks
    def operation(self):
        """
        Goal of this event is to check all the:
            Tips
            Comment
            New files
            System Event

        Only the Models with the 'notification_status' can track which elements has been
        notified or not.
        """

        # Initialize Notification setting system wide
        notification_settings = yield self._get_notification_settings()

        if not notification_settings:
            log.err("Node has not Notification configured, Notification disabled!")
            return

        # Else, checks tip/file/comment/activation link

        yield self.do_tip_notification(notification_settings)

        # self.do_file_notification(notification_settings)
        # self.do_comment_notification(notification_settings)

