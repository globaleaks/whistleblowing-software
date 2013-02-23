# -*- coding: UTF-8
#   cleaning_sched
#   **************
#
# Implementation of the cleaning operations (delete incomplete submission,
# delete expired tips, etc)

from twisted.internet.defer import inlineCallbacks

from globaleaks.settings import transact

from globaleaks.utils import log
from globaleaks.jobs.base import GLJob
from globaleaks.models import InternalTip
from datetime import datetime

__all__ = ['APSCleaning']

class APSCleaning(GLJob):

    @transact
    def get_expired_itip(self, store):
        allitip = store.find(InternalTip)
        return None

    @transact
    def get_expired_session(self, store):
        unfinished = store.find(InternalTip)
        return None

    @inlineCallbacks
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

        # for each Context get expiration time
        expired_itip = yield self.get_expired_itip()
        if expired_itip:
            log.debug("Delete expired itip %s" % expired_itip )

        expired_session = yield self.get_expired_session()
        if expired_session:
            log.debug("Delete unfinished submission %s" % expired_session )


