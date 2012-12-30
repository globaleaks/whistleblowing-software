# -*- coding: UTF-8
#   backend
#   *******
#
# Notification implementation, documented along the others asynchronousd
# operatios, in Architecture and in jobs/README.md

from globaleaks.utils import log
from globaleaks.jobs.base import GLJob
from globaleaks.models.externaltip import ReceiverTip, Comment
from globaleaks.models.internaltip import InternalTip
from datetime import datetime
from twisted.internet.defer import inlineCallbacks
from globaleaks.plugins.base import GLPluginManager

__all__ = ['APSNotification']


# TEMP -- AARRGHH
settings = { 'admin_fields' : { 'server' :  'box549.bluehost.com', 'port' : 25, # 465,
                                'username':'sendaccount939@globaleaks.org', 'password':'sendaccount939', 'ssl': False # True
                        }, 'receiver_fields':  { 'mail_addr' : None }
    }
# TEMP -- AARRGHH

notification_format = { 'tip_gus' : None, 'creation_time' : None, 'source' : None, 'type' : None, 'receiver' : None}

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

        for single_tip in  not_notified_tips:

            # XXX This key is guarantee (except if the plugin has not been removed)
            # Actually can't be removed a plugin!

            #plugin_code = notification_plugins[single_tip['notification_selected']]
            # remind, now is "none" if not configured in a receiver
            plugin_code = notification_plugins['email']

            # Specification TODO for plugin communication:
            notification_format['tip_gus'] = single_tip['tip_gus']
            notification_format['creation_time'] = single_tip['creation_time']
            notification_format['type'] = u'tip'
            notification_format['source'] = u"GLNodeName"
            notification_format['receiver'] = u"your Name, Receiver!"

            settings['receiver_fields'].update({'mail_addr' : single_tip['notification_fields']})

            if False:
            # if plugin_code.do_notify(settings, notification_format):
                yield receivertip_iface.flip_mark(single_tip['tip_gus'], u'notified')
            else:
                yield receivertip_iface.flip_mark(single_tip['tip_gus'], u'unable to notify')


        # Comment Notification procedure
        comment_iface = Comment()
        internaltip_iface = InternalTip()

        not_notified_comments = yield comment_iface.get_comment_by_mark(marker=u'not notified')

        # A lot to be review
        """
        for comment in not_notified_comments:

            # notification_format = comment['author'] if comment['author'] else comment['source']
            # Remind - at the moment the nome is no more given, but author_gus is used instead.
            # Need to be reused for this utility ? TODO

            receivers_list = yield internaltip_iface.get_receivers_by_itip(comment['internaltip_id'])
            # receivers_list contain all the Receiver description related to InternalTip.id

            for receiver_info in receivers_list:

                settings['receiver_fields'].update({'mail_addr' : receiver_info[1]})

                # plugin_code = notification_plugins[receiver_info[0]]
                # is None receiver_info[0] :( TODO

                plugin_code = notification_plugins['email']

                notification_format['creation_time'] = comment['creation_time']
                notification_format['source'] = comment['source'] # comment['author']
                notification_format['type'] = u'comment'
                notification_format['source'] = u"GLNodeName"
                notification_format['receiver'] = u"your Name, Receiver!"

                # TODO digest check

                # new scheduler logic will fix also the lacking of comments notification status
                # plugin_code.do_notify(settings, notification_format)

            # this is not yet related to every receiver, because there are not yet a tracking
            # struct about the notifications statuses.
            yield comment_iface.flip_mark(comment['comment_id'], u'notified')
            # This would be refactored with with the task manager + a comment for every receiver
        """

