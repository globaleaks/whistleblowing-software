from globaleaks.utils import log
from globaleaks.jobs.base import GLJob
from globaleaks.models.externaltip import ReceiverTip, Comment
from globaleaks.models.internaltip import InternalTip
from datetime import datetime
from twisted.internet.defer import inlineCallbacks
from globaleaks.plugins import GLPluginManager

__all__ = ['APSNotification']

class APSNotification(GLJob):

    @inlineCallbacks
    def operation(self):
        """
        Goal of this function is to check all the:
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
        log.debug("[D]", self.__class__, 'operation', datetime.today().ctime())

        notification_plugins = GLPluginManager('notification')

        receivertip_iface = ReceiverTip()

        # TODO +check delivery mark - would be moved in task queue
        not_notified_tips = yield receivertip_iface.get_tips(marker=u'not notified')

        for single_tip in not_notified_tips:

            # XXX This key is guarantee (except if the plugin has not been removed)
            plugin_code = notification_plugins.get(single_tip['notificaton_selected'])

            print "XXX selected plugin", plugin_code.plugin_name, plugin_code.plugin_type, "XXXXXXXXX"

            # TODO digest (but It's better refactor scheduler in the same time)

            information = [ single_tip['creation_time'], "New Tip: %s" % single_tip['tip_gus'] ]

            if plugin_code.do_notify(single_tip['notification_fields'], information):
                yield receivertip_iface.flip_mark(single_tip['tip_gus'], u'notified')
            else:
                yield receivertip_iface.flip_mark(single_tip['tip_gus'], u'unable to notify')


        # Comment Notification procedure
        internaltip_iface = InternalTip()
        comment_iface = Comment()

        not_notified_comments = yield comment_iface.get_comment_by_mark(marker=u'not notified')

        for comment in not_notified_comments:

            source_name = comment['author'] if comment['author'] else comment['source']
            receivers_list = yield internaltip_iface.get_notification_list(comment['internaltip_id'])
            # receiver_list is composed by [ notification_selected, notification_fields ]

            for receiver_info in receivers_list:

                plugin_code = notification_plugins.get(receiver_info[0])

                # TODO digest check
                information = [ comment['creation_time'], "New comment from: %s" % source_name ]
                # new scheduler logic will fix also the lacking of comments notification status
                plugin_code.do_notify(receiver_info[1], information)

            # this is not yet related to every receiver, because there are not yet a tracking
            # struct about the notifications statuses.
            yield comment_iface.flip_mark(comment['comment_id'], u'notified')
            # This would be refactored with with the task manager + a comment for every receiver

