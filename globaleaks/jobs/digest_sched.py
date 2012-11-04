from globaleaks.utils import log
from globaleaks.jobs.base import GLJob
from datetime import date

__all__ = ['APSDigest']

class APSDigest(GLJob):

    def operation(self):
        """
        This operation would be defined after email notification support.
        The goal of this operation, is collect email for the same receiver,
        and then avoid a massive mailing, in case of strong activities.

        the schedule is based in a receiver/context configuration.
        """
        log.debug("[D]", self.__class__, 'operation', date.today().ctime())
