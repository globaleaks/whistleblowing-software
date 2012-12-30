# -*- coding: UTF-8
#   delivery_sched
#   **************
#
# Implements the delivery operations performed when a new submission
# is created, or a new file is append to an existing Tip. delivery 
# works on the file and on the fields, not in the comments.

from globaleaks.utils import log
from globaleaks.jobs.base import GLJob
from globaleaks.models.internaltip import InternalTip
from globaleaks.models.externaltip import File, ReceiverTip
from datetime import datetime

__all__ = ['APSDelivery']

class APSDelivery(GLJob):

    def operation(self):
        """
        Goal of this function is to check all the Folder linked to an InternalTip
        marked as 'not delivered' and perform delivery.

        the possible status value are:

            'no data available': 
            'not yet delivered': when a tip has data not delivered
            'delivery available': when the deliver is ready, but need to be performed by
            receiver (eg: download zipped + encrypted file)
            'delivery performed': when is performed only one time, like remote copy
            'unable to be delivered': when something is goes wrong.

        act on the single Folder.
        TODO when file uploader / folder models is correctly managed.
        """
        log.debug("[D]", self.__class__, 'operation', datetime.today().ctime())
