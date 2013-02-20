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
        ret = dict((x.id, x.receiver.notification_fields) for x in not_notified_tips)
        return ret

    @transact
    def _get_notification_settings(self, store):

        node = store.find(models.Node).one()
        return node.notification_settings


    @inlineCallbacks
    def do_tip_notification(self, notification_settings):
        log.debug('tip_notification fired!')

        notification_data = yield self._get_notification_data()

        #  for cplugin in settings.notification_plugins:
        cplugin = settings.notification_plugins[0]

        plugin = getattr(notification, cplugin)(notification_settings)
        for rtip in notification_data:
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

        self.do_tip_notification(notification_settings)
        # self.do_file_notification(notification_settings)
        # self.do_comment_notification(notification_settings)

