# -*- coding: UTF-8
#
# log
# ***
#
# This interface is used by Admin, Receivers and $PEOPLE_ACCESSING_TIP
# to get the list, in chronological reverse order, of the event in their interest
# Is in fact our way to display a log, with different level of alarm

import os
import logging

from twisted.internet.defer import inlineCallbacks
from storm.expr import Desc, And

from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import transport_security_check, authenticated
from globaleaks.utils.logger import LoggedEvent, LogQueue
from globaleaks.rest import requests

from globaleaks.settings import transact, transact_ro, GLSettings
from globaleaks.rest import errors



class AdminLogManagement(BaseHandler):

    # @transport_security_check('admin')
    # @authenticated('admin')
    def post(self):
        """
        This REST permit to the admin to switch the loglevel, in order
        to get more details about the running operations.
        """
        request = self.validate_message(self.request.body, requests.AdminLogManagement)

        if request['log_level'] not in [0, 1]:
            raise errors.InvalidInputFormat("Expected 0 or 1 as log level")

        if request['log_level'] == 0:
            GLSettings.loglevel = logging.DEBUG

        if request['log_level'] == 1:
            GLSettings.loglevel = logging.INFO

        # I'm ignoring log_level 2 or more, ERRORS/CRITICAL because they
        # will be always reported.
        self.set_status(202)
        self.finish()


class BaseLogCollection(BaseHandler):

    def serialize_logs(self, logslist):
        if not logslist:
            return []
        retlist = []
        for le in logslist:
            retlist.append(le.serialize_log())
        return retlist

class AdminLogCollection(BaseLogCollection):

    # @transport_security_check('admin')
    # @authenticated('admin')
    @inlineCallbacks
    def get(self, paging):

        unimplemented_paging = 50
        logslist = yield LogQueue.picklogs('admin', unimplemented_paging)

        self.finish(self.serialize_logs(logslist))

class ReceiverLogCollection(BaseLogCollection):

    @transport_security_check('receiver')
    @authenticated('receiver')
    @inlineCallbacks
    def get(self, paging):

        unimplemented_paging = 50

        logslist = yield LogQueue.picklogs(
                LogQueue.create_subject_uuid('receiver', self.current_user.user_id),
                unimplemented_paging )

        self.finish(self.serialize_logs(logslist))


class WbLogCollection(BaseLogCollection):

    @transport_security_check('wb')
    @authenticated('wb')
    # @inlineCallbacks
    def get(self, paging):

        unimplemented_paging = 50
        raise Exception("To be implemented")



class RtipLogCollection(BaseLogCollection):

    @transport_security_check('receiver')
    @authenticated('receiver')
    # @inlineCallbacks
    def get(self, paging):

        unimplemented_paging = 50
        raise Exception("To be implemented")



