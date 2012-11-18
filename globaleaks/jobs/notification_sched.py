from globaleaks.utils import log
from globaleaks.jobs.base import GLJob
from globaleaks.models.externaltip import ReceiverTip, Comment
from datetime import datetime
from twisted.internet.defer import inlineCallbacks
from globaleaks.plugins.notification.mailclient import GLBMailService

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

        receivertip_iface = ReceiverTip()

        # TODO +check delivery mark - would be moved in task queue
        not_notified_tips = yield receivertip_iface.get_tips(marker=u'not notified')

        for single_tip in not_notified_tips:

            # instead of checking if 'email' is set, in the future, open the plugin called like
            # notification_selected, and pass the notification_fields to them.
            if single_tip['notification_selected'] == u'email':

                if GLBMailService(single_tip['tip_gus'], single_tip['notification_fields']):
                    yield receivertip_iface.flip_mark(single_tip['tip_gus'], u'notified')
                else:
                    yield receivertip_iface.flip_mark(single_tip['tip_gus'], u'unable to notify')

            else:
                log.err("[E]: not yet supported notification %s (%s)" %
                        (single_tip['notification_selected'], single_tip['notification_fields'])
                )

        # Comment to be notified
        # comment_iface = Comment()
        # not_notified_comments = yield comment_iface.get_comment_by_mark(marker=u'not notified')

