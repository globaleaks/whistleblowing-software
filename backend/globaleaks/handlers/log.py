# -*- coding: UTF-8
#
# log
# ***
#
# This interface is used by Admin, Receivers and $PEOPLE_ACCESSING_TIP
# to get the list, in chronological reverse order, of the event in their interest
# Is in fact our way to display a log, with different level of alarm

import os

from twisted.internet.defer import inlineCallbacks
from storm.expr import Desc, And

from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import transport_security_check, authenticated
from globaleaks.utils.logger import LoggedEvent

from globaleaks.settings import transact, transact_ro, GLSettings
from globaleaks.rest import errors


class BaseLogCollection(BaseHandler):

    def serialize_all_logs(self):
        """
        This function is just for development testing
        """
        import pprint
        pprint.pprint(LoggedEvent.LogQueue)

        return_list = []

        for log_id, log_info in LoggedEvent.LogQueue.iteritems():
            return_list.append(
                LoggedEvent.get(log_id).serialize_log()
            )

        return return_list


class AdminLogCollection(BaseLogCollection):

    # @transport_security_check('admin')
    # @authenticated('admin')
    # @inlineCallbacks
    def get(self, paging):
        self.finish(self.serialize_all_logs())


class ReceiverLogCollection(BaseLogCollection):

    # @transport_security_check('receiver')
    # @authenticated('receiver')
    # @inlineCallbacks
    def get(self, paging):
        self.finish(self.serialize_all_logs())

class WbLogCollection(BaseLogCollection):

    # @transport_security_check('wb')
    # @authenticated('wb')
    # @inlineCallbacks
    def get(self, paging):
        self.finish(self.serialize_all_logs())


class RtipLogCollection(BaseLogCollection):

    # @transport_security_check('receiver')
    # @authenticated('receiver')
    # @inlineCallbacks
    def get(self, paging):
        self.finish(self.serialize_all_logs())
