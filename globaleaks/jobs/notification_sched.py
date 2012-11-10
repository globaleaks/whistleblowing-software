from globaleaks.utils import log
from globaleaks.jobs.base import GLJob
from globaleaks.models.externaltip import ReceiverTip
from datetime import datetime
from globaleaks.plugins.notification.mailclient import GLBMailService

__all__ = ['APSNotification']

class APSNotification(GLJob):

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
        not_notified_tips = yield receivertip_iface.get_tips(status=u'not notified')

        for single_tip in not_notified_tips:

            print "sendig email for" , single_tip

            GLBMailService(single_tip['tip_gus'], single_tip['notification_fields'])

