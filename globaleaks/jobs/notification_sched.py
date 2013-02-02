# -*- coding: UTF-8
#
#   notification_sched
#   ******************
#
# Notification implementation, documented along the others asynchronous
# operations, in Architecture and in jobs/README.md

from globaleaks.jobs.base import GLJob
from globaleaks.transactors.asyncoperations import AsyncOperations
from twisted.internet.defer import inlineCallbacks

__all__ = ['APSNotification']

class APSNotification(GLJob):

    @inlineCallbacks
    def operation(self):
        """
        Goal of this event is to check all the:
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

        results = yield AsyncOperations().tip_notification()

        # TODO results log and stats

        results = yield AsyncOperations().comment_notification()

        # TODO results log and stats

        # Comment Notification here it's just an incomplete version, that never would supports
        # digest or retry, until Task manager queue is implemented


