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
from collections import namedtuple

Event = namedtuple('Event',
                   ['type', 'trigger', 'af', 'rf', 'tip_id'])

class APSNotification(GLJob):
    @transact
    def tip_notification(self, store):
        plugin_type = u'notification'
        not_notified_tips = store.find(models.ReceiverTip,
                                       models.ReceiverTip.mark == models.ReceiverTip._marker[0]
        )
        node = store.find(models.Node).one()

        log.debug('tip_notification fired!')

        if not node.notification_settings:
            return

        notification_settings = self._get_notification_settings()

        event = Event(type=u'tip', trigger='diocane', af=notification_settings,
                      rf=None, tip_id=None)

        for cplugin in settings.notification_plugins:
            plugin = getattr(notification, cplugin)(event.af)
            for rtip in not_notified_tips:
                event.rf = rtip.receiver.notification_fields
                event.tip_id = rtip.id
                notify = yield plugin.do_notify(event)

                @notify.addCallback
                def success(self, result):
                    log.debug('notificication sucess')
                    rtip.mark = models.ReceiverTip._marker[1]
                @notify.addErrback
                def error(self, result):
                   log.debug('notificication failure')
                   rtip.mark = models.ReceiverTip._marker[2]


    def operation(self):
        """
        Goal of this event is to check all the:
            Tips
            Comment
            Folder
            System Event

        marked as 'not notified' and perform notification.
        Notification plugin chose if perform a communication or not,
        Then became marked as:
            'notification ignored', or
            'notified'

        Every notification plugin NEED have a checks to verify
        if notification has been correctly performed. If not (eg: wrong
        login/password, network errors) would be marked as:
        'unable to be notified', and a retry logic is in TODO
        """
        return self.tip_notification()
        # TODO results log and stats
        # TODO results log and stats
        # Comment Notification here it's just an incomplete version, that never would supports
        # digest or retry, until Task manager queue is implemented
