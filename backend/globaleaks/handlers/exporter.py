# -*- coding: utf-8 -*-
#
# Exporter
# ********
#
# Class containing special function to export data from GlobaLeaks instances during
# research and development. The API Below are enabled only if the system runs in
# development mode.

from twisted.internet.defer import inlineCallbacks
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.files import download_all_files, serialize_receiver_file
from globaleaks.handlers.authentication import transport_security_check, authenticated
from globaleaks.handlers import admin
from globaleaks.rest import errors
from globaleaks.settings import transact_ro
from globaleaks.plugins.base import Event
from globaleaks.jobs.notification_sched import serialize_receivertip
from globaleaks.models import ReceiverTip, ReceiverFile
from globaleaks.utils.zipstream import ZipStream, get_compression_opts
from globaleaks.utils.utility import log
from globaleaks.utils.templating import Templating



class CurrentStats(BaseHandler):

    def get(self):

        self.set_status(200)
        self.finish()


class ReportEvent(BaseHandler):

    def get(self, eventstring):

        print "Now received notice of", eventstring

        self.set_status(201)
        self.finish()
