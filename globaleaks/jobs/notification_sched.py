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
    def _get_notification_data(self, store):
        not_notified_tips = store.find(models.ReceiverTip,
                                       models.ReceiverTip.mark == models.ReceiverTip._marker[0]
        )

        if not_notified_tips:
            log.debug("Present %d Tip that need to be notified" % not_notified_tips.count())

        ret = dict((x.id, x.receiver.notification_fields) for x in not_notified_tips)
        return ret

    @transact
    def _get_notification_settings(self, store):
        """
        notification setting need to contains bot template
        and systemsettings
        """

        node = store.find(models.Node).one()

        if not node.notification_settings.has_key('email_template'):
            log.err("Missing email_template! Notification disabled")
            return None

        return node.notification_settings


    @inlineCallbacks
    def do_tip_notification(self, notification_settings):
        log.debug("Entering in Tip Notification")

        notification_data = yield self._get_notification_data()

        # for cplugin in settings.notification_plugins:
        cplugin = settings.notification_plugins[0]

        # the configuration of the node need to be checked here, because do_notify
        # it's something with obscure callback based

        plugin = getattr(notification, cplugin)(notification_settings)
        for rtip in notification_data:
            af=notification_settings
            rf=notification_data[rtip]

            try:
                host = af['server']
                port = af['port']
                u = af['username']
                p = af['password']
                tls = af['ssl']
                address = rf['mail_address']
            except KeyError, e:
                log.debug("Notification settings: unable to send mail, missing %s" % e)
                return

            event = Event(type=u'tip', trigger='Tip', af=notification_settings,
                          rf=notification_data[rtip],
                          tip_id=rtip)

            notify = yield plugin.do_notify(event)

            @notify.addCallback
            def success(self, result):
                log.debug('OK Notification for %s' % rtip.repr() )
                rtip.mark = models.ReceiverTip._marker[1]

            @notify.addErrback
            def error(self, result):
                log.debug('FAIL Notification for %s FAIL' % rtip.repr() )
                rtip.mark = models.ReceiverTip._marker[2]


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
            log.err("Node has not Notification configured, notification disabled!")
            return

        self.do_tip_notification(notification_settings)

        # self.do_file_notification(notification_settings)
        # self.do_comment_notification(notification_settings)

