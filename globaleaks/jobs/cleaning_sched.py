# -*- coding: UTF-8
#   cleaning_sched
#   **************
# 
# Implementation of the cleaning operations (delete incomplete submission,
# delete expired tips, etc)


from globaleaks.utils import log
from globaleaks.jobs.base import GLJob
from globaleaks.models.submission import Submission
from globaleaks.models.context import Context
from globaleaks.models.internaltip import InternalTip
from datetime import datetime

__all__ = ['APSCleaning']

class APSCleaning(GLJob):

    def operation(self):
        """
        Goal of this function is to check all the submission not 
        finalized, and, if the expiration time sets in the context has
        been reached, then clean the submission_gus along with the fields,
        and, if present, the uploaded folder/files.

        Second goal of this function, is to check all the internaltips 
        and their expiration date, if match, remove that, all the folder,
        comment and tip related.
        """
        log.debug("[D]", self.__class__, 'operation', datetime.today().ctime())

        # for each Context get expiratin time, 
        # for each context get submission_gus
        # check and act if the time is expired

        # for each InternalTip get expiration time,
        # check and remove 

