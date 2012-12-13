# -*- coding: UTF-8
#   welcome_sched
#   *************
#
# Welcome is the operation performed when a new receiver is registered.
# It obtain a token, permitting to perform settings and configuration before
# start to receive the Tips.


from globaleaks.utils import log
from globaleaks.jobs.base import GLJob
from globaleaks.models.receiver import Receiver
from datetime import date

__all__ = ['APSWelcome']

class APSWelcome(GLJob):

    def operation(self):
        """
        Goal of this function is to check if a new receiver is present, and 
        send to him/she a welcome email. This is not just a nice thing, but
        need to contain a tip-like ID, so the receiver would be able to 
        access to their preferences before receive the first Tip, and then
        configured notification/delivery as prefer, before receive the first
        whistleblowers data.

        the status of a receiver would be:

        'not welcomed'
            when a receiver has been just added, and need to be welcomed
        'welcomed'
            the welcome message has been sent.

        would be expanded to support cases when receiver NEED to configure their profile.
        """
        log.debug("[D]", self.__class__, 'operation', date.today().ctime())

        receiver_iface = Receiver()

        # noobceivers = yield receiver_iface.lookup(status=u'not welcomed')
        # noobceivers = receiver_iface.lookup(status=u'not welcomed')
        noobceivers = []

        for noob in noobceivers:
            print "need to be welcomed", noob
