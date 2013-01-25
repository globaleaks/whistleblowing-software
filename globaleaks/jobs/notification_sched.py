# -*- coding: UTF-8
#
#   notification_sched
#   ******************
#
# Notification implementation, documented along the others asynchronousd
# operatios, in Architecture and in jobs/README.md

from globaleaks.utils import log
from globaleaks.jobs.base import GLJob
from globaleaks.models.externaltip import ReceiverTip, Comment
from globaleaks.models.internaltip import InternalTip
from globaleaks.models.options import PluginProfiles, ReceiverConfs
from datetime import datetime
from twisted.internet.defer import inlineCallbacks
from globaleaks.plugins.manager import PluginManager

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
        plugin_type = u'notification'

        log.debug("[D]", self.__class__, 'operation', datetime.today().ctime())

        receivertip_iface = ReceiverTip()
        receivercfg_iface = ReceiverConfs()
        profile_iface = PluginProfiles()

        # TODO digest check missing it's required refactor the scheduler using a dedicated Storm table
        not_notified_tips = yield receivertip_iface.get_tips_by_notification_mark(u'not notified')

        for single_tip in not_notified_tips:

            # from a single tip, we need to extract the receiver, and then, having
            # context + receiver, find out which configuration setting has active

            receivers_map = yield receivertip_iface.get_receivers_by_tip(single_tip['tip_gus'])

            receiver_info = receivers_map['actor']

            receiver_conf = yield receivercfg_iface.get_active_conf(receiver_info['receiver_gus'],
                single_tip['context_gus'], plugin_type)

            if receiver_conf is None:
                print "Receiver", receiver_info['receiver_gus'], \
                    "has not an active notification settings in context", single_tip['context_gus'], "for", plugin_type

                # TODO applicative log, database tracking of queue
                continue

            # Ok, we had a valid an appropriate receiver configuration for the notification task
            related_profile = yield profile_iface.get_single(receiver_conf['profile_gus'])

            settings_dict = { 'admin_settings' : related_profile['admin_settings'],
                              'receiver_settings' : receiver_conf['receiver_settings']}

            plugin = PluginManager.instance_plugin(related_profile['plugin_name'])

            updated_tip = yield receivertip_iface.update_notification_date(single_tip['tip_gus'])
            return_code = plugin.do_notify(settings_dict, u'tip', updated_tip)

            if return_code:
                yield receivertip_iface.flip_mark(single_tip['tip_gus'], u'notified')
            else:
                yield receivertip_iface.flip_mark(single_tip['tip_gus'], u'unable to notify')


        # Comment Notification here it's just an incomplete version, that never would supports
        # digest or retry, until Task manager queue is implemented

        comment_iface = Comment()
        internaltip_iface = InternalTip()

        not_notified_comments = yield comment_iface.get_comment_by_mark(marker=u'not notified')

        for comment in not_notified_comments:

            receivers_list = yield internaltip_iface.get_receivers_by_itip(comment['internaltip_id'])

            # needed to obtain context!
            itip_info = yield internaltip_iface.get_single(comment['internaltip_id'])

            for receiver_info in receivers_list:

                receiver_conf = yield receivercfg_iface.get_active_conf(receiver_info['receiver_gus'],
                    itip_info['context_gus'], plugin_type)

                if receiver_conf is None:
                    # TODO applicative log, database tracking of queue
                    continue

                # Ok, we had a valid an appropriate receiver configuration for the notification task
                related_profile = yield profile_iface.get_single(receiver_conf['profile_gus'])

                settings_dict = { 'admin_settings' : related_profile['admin_settings'],
                                  'receiver_settings' : receiver_conf['receiver_settings']}

                plugin = PluginManager.instance_plugin(related_profile['plugin_name'])

                return_code = plugin.do_notify(settings_dict, u'comment', comment)

                if return_code:
                    print "Notification of comment successful for user", receiver_conf['receiver_gus']
                else:
                    print "Notification of comment failed for user", receiver_conf['receiver_gus']

            # remind: comment are not guarantee until Task manager is not developed
            yield comment_iface.flip_mark(comment['comment_id'], u'notified')
