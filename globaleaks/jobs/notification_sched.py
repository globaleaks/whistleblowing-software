from globaleaks.utils import log
from globaleaks.jobs.base import GLJob
from globaleaks.models.tip import ReceiverTip
from datetime import datetime

__all__ = ['APSNotification']

class APSNotification(GLJob):

    def operation(self):
        """
        Goal of this function is to check all the Tips marked as
        'not notified' and perform notification, marking them as 
        'notified'.

        TODO: every notification module would have a verification 
        process to verify if notification is worked correctly,
        if not, switch the appropriate tip from 'notified' to 
        'unable to be notified'
        """
        log.debug("[D]", self.__class__, 'operation', datetime.today().ctime())

        #receivertip_iface = ReceiverTip()

        #not_notified_tips = receivertip_iface.get_tips(status=u'not notified')
        
        #for single_tip in not_notified_tips:
        #    print single_tip
        #    # send notification mail, using: single_tip.notification_fields
        #    receivertip_iface.flip_status(single_tip.tip_gus, u'notified')



"""
class NotificationOps(Job):

    def success(self):
        print "I'm the callLater function", time.asctime()

    def run(self, *arg):

        var = randint(1,5)
        print __file__, "I'm running, now random var is", var, "and are the", time.asctime()

        self.scheduledTime = time.time()
        self.delay = 4

        sleep(2)

        reactor.callLater(10 + var, self.success)
        return True

why I've left the Job/scheduler.worker.add:


INFO:twisted:/home/vecna/progetti/GLBackend/globaleaks/jobs/notification.py I'm running, now random var is 3 and are the Thu Nov  1 03:42:19 2012
INFO:twisted: /home/vecna/progetti/GLBackend/globaleaks/jobs/notification.py I'm running, now random var is 4 and are the Thu Nov  1 03:42:19 2012

INFO:twisted:I'm the callLater function Thu Nov  1 03:42:34 2012
INFO:twisted:I'm the callLater function Thu Nov  1 03:42:35 2012

because all the operations has been duplicated, because the self.scheduledTime and self.delay was
not making what's I'm expecting, and because the amount of code for make the working manager do
not justify the operations.

we need just to run a series of function, scheduled in time, that apply their operations on the existing database.
they do not keep track of their internal status, just because if the software is stopped during the execution, then
the operation in not yet completed, and would be redone in the next execution of this flow.
"""
