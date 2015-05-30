# -*- coding: UTF-8
#  inspector
#  *********
#
# This handler is loaded optionally (only if specific command line switch
# are present) and permit to dump statistics and details on GlobaLeaks
# running. Is used in stress testing and development.

import os

from twisted.internet.defer import inlineCallbacks

from globaleaks import models, LANGUAGES_SUPPORTED
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import transport_security_check, unauthenticated
from globaleaks.utils.utility import datetime_to_ISO8601
from globaleaks.utils.structures import Rosetta, get_localized_values
from globaleaks.settings import transact_ro, GLSetting
from globaleaks.rest.apicache import GLApiCache


class JDT(BaseHandler):
    """
    JDT, JSON Dump Timing
    """

    @transport_security_check("unauth")
    @unauthenticated
    # @inlineCallbacks
    def get(self):
        """
        Dump the current collection of request/answer timings
        """

        print "TODO"
        self.finish(ret)
