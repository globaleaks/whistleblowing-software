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
from globaleaks.utils.logger import LoggedEvent, LogQueue

from globaleaks.settings import transact, transact_ro, GLSettings
from globaleaks.rest import errors


class BaseLogCollection(BaseHandler):
    pass



class AdminLogCollection(BaseLogCollection):

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self, paging):

        unimplemented_paging = 50
        logslist = LogQueue.picklogs('admin', unimplemented_paging)

        retlist = []
        for le in logslist:
            retlist.append(le.serialize_log())
        self.finish(retlist)



class ReceiverLogCollection(BaseLogCollection):

    @transport_security_check('receiver')
    @authenticated('receiver')
    @inlineCallbacks
    def get(self, paging):

        unimplemented_paging = 50
        logslist = LogQueue.picklogs(
                LogQueue.create_subject_uuid('receiver', self.current_user.user_id),
                unimplemented_paging )

        retlist = []
        for le in logslist:
            retlist.append(le.serialize_log())
        self.finish(retlist)


class WbLogCollection(BaseLogCollection):

    @transport_security_check('wb')
    @authenticated('wb')
    @inlineCallbacks
    def get(self, paging):

        unimplemented_paging = 50
        raise Exception("To be implemented")



class RtipLogCollection(BaseLogCollection):

    @transport_security_check('receiver')
    @authenticated('receiver')
    @inlineCallbacks
    def get(self, paging):

        unimplemented_paging = 50
        raise Exception("To be implemented")



