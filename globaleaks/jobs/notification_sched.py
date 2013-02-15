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
        ret = dict((x.id, x.notification_settings) for x in not_notified_tips)
        print ret
        node = store.find(models.Node).one()
        ret['node'] = node.notification_settings
        return ret

    @inlineCallbacks
    def tip_notification(self):
        log.debug('tip_notification fired!')

        notification_data = yield self._get_notification_data()
        notification_settings = notification_data.pop('node')

        if not notification_settings:
            return

        event = Event(type=u'tip', trigger='diocane', af=notification_settings,
                      rf=None, tip_id=None)
        for cplugin in settings.notification_plugins:
            plugin = getattr(notification, cplugin)(event.af)
            for rtip in notification_data:
                event.rf = notification_data[rtip]
                event.tip_id = rtip
                notify = yield plugin.do_notify(event)

#                 @notify.addCallback
#                 def success(self, result):
#                     log.debug('notificication sucess')
#                     rtip.mark = models.ReceiverTip._marker[1]
#                 @notify.addErrback
#                 def error(self, result):
#                    log.debug('notificication failure')
#                    rtip.mark = models.ReceiverTip._marker[2]


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
