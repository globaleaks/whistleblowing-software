from globaleaks.utils import log
from globaleaks.jobs.base import GLJob
from globaleaks.models.externaltip import ReceiverTip, Comment
from globaleaks.models.internaltip import InternalTip
from datetime import datetime
from twisted.internet.defer import inlineCallbacks
from globaleaks.plugins.base import GLPluginManager

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

        notification_plugins = GLPluginManager().get_types('notification')

        receivertip_iface = ReceiverTip()

        # TODO +check delivery mark - would be moved in task queue
        # TODO digest check missing (but It's better refactor scheduler in the same time)
        not_notified_tips = yield receivertip_iface.get_tips(marker=u'not notified')

        for single_tip in not_notified_tips:

            # XXX This key is guarantee (except if the plugin has not been removed)
            # Actually can't be removed a plugin!
            plugin_code = notification_plugins[single_tip['notification_selected']]

            # temporary way fo get admin settings, it's an XXX

            information = [ single_tip['creation_time'], "New Tip: %s" % single_tip['tip_gus'] ]

            # XXX XXX XXX
            # XXX XXX XXX
            if single_tip['notification_selected'] == 'email':
                settings = { 'admin_fields' :  { 'server' :  'smtp.gmail.com', 'port' : 587,
                                                 'username':'globaleaksnode1@gmail.com', 'password':'Antani1234', 'ssl': True },
                             'receiver_fields' :  { 'mail_addr' : single_tip['notification_fields'] }
                           }
            else: # single_tip['notification_selected'] == 'irc':
                settings = { 'admin_fields' :  { 'server' :  'irc.oftc.net', 'channel' : '#globaleaks',
                                                 'node_user':'GlobaLx' },
                              'receiver_fields' : { 'receiver_user' : 'vecna'}
                           }
            # XXX XXX XXX
            # XXX XXX XXX

            if plugin_code.do_notify(settings, information):
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

                plugin_code = notification_plugins[receiver_info[0]]

                # TODO digest check
                information = [ comment['creation_time'], "New comment from: %s" % source_name ]
                # new scheduler logic will fix also the lacking of comments notification status
                plugin_code.do_notify(receiver_info[1], information)

            # this is not yet related to every receiver, because there are not yet a tracking
            # struct about the notifications statuses.
            yield comment_iface.flip_mark(comment['comment_id'], u'notified')
            # This would be refactored with with the task manager + a comment for every receiver

