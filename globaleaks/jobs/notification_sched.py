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
from globaleaks.plugins.manager import PluginManager
from globaleaks import models
from globaleaks.settings import transact
from globaleaks.utils import log
from globaleaks.transactors.asyncoperations import AsyncOperations


class APSNotification(GLJob):
    @transact
    def tip_notification(self, store):
        plugin_type = u'notification'
        not_notified_tips = store.find(models.ReceiverTip,
                                       models.ReceiverTip.notification_mark == u'not notified'
        )
        node = store.find(models.Node).one()

        log.debug('tip_notification fired!')

        if not node.notification_settings:
            return

        plugin = PluginManager.instance_plugin(u'Mail')
        plugin.initialize(node.notification_settings)
        for rtip in not_notified_tips:
            return_code = plugin.do_notify(Event(type=u'tip', trigger='diocane'),
                                            af=node.notification_settings,
                                            rf=rtip.receiver.notification_fields,
            )
            if return_code:
               receivertip_iface.flip_mark(single_tip['tip_gus'], u'notified')
            else:
               receivertip_iface.flip_mark(single_tip['tip_gus'], u'unable to notify')

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

        #d.addCallback(lambda x: AsyncOperations().comment_notification)

        # TODO results log and stats

        # Comment Notification here it's just an incomplete version, that never would supports
        # digest or retry, until Task manager queue is implemented
        return d
