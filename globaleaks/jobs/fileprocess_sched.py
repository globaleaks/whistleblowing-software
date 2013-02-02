# -*- coding: UTF-8
#
#   file_process
#   ************
#
# FileProcess is the scheduled operators that perform validation in the submitted file.
# the profiles present would be configured by Administrator, and no receiver settings
# are present.


from globaleaks.jobs.base import GLJob
from twisted.internet.defer import inlineCallbacks
from globaleaks.transactors.asyncoperations import AsyncOperations

__all__ = ['APSFileProcess']


class APSFileProcess(GLJob):

    @inlineCallbacks
    def operation(self):
        """
        Goal of this function is to check all the new files and validate
        thru the configured SystemSettings

        possible marker in the file are:
            'not processed', 'ready', 'blocked', 'stored'
        defined in File._marker

        """
        answer = yield AsyncOperations() .fileprocess()

