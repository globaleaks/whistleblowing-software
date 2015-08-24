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
from globaleaks.settings import GLSettings

CurrentStatQueue = []
EventTypeCounter = {
    'submission': 1,
    'delivery': 1,
    'comment': 1,
}

def add_measured_event(method, uri, secs_elapsed, event_id, start_time):

    # This is an hack of the event tracking, just has to keep in account
    # also some periodic scheduled event like Delivery phases

    if method == 'PUT' and uri.startswith('/submission'):
        event_type = 'submission'
    elif method == 'POST' and uri == '/wbtips/comments':
        event_type = 'comment'
    elif method == None and uri == None:
        event_type = 'delivery'
    else:
        return

    log.debug("add_measured_event %s %s %d %d = %s, start time %s" %
              (method, uri, secs_elapsed,
               event_id, event_type, start_time))
    print type(start_time)

    assert event_type in EventTypeCounter.keys(), "Invalid event_type %s not in %s" % \
                                                  (event_type, EventTypeCounter.keys())
    measured_event = {
        'event_id': event_id,
        'event_type' : event_type,
        'millisecs_elapsed': round(secs_elapsed * 1000, 2),
        'event_counter': EventTypeCounter[event_type],
        'start_time': start_time
    }

    EventTypeCounter[event_type] += 1
    CurrentStatQueue.append(measured_event)


class CurrentStats(BaseHandler):

    def get(self):

        if not GLSettings.json_stats:
            raise errors.InvalidInputFormat("Enable only with -S --stats cmdline switch")

        self.set_status(200)

        # transform in CSV
        last_i = 0
        ret_csv = "number,millisec,type\n"
        for i, event in enumerate(CurrentStatQueue):
            this_event = "%d,%d,%s" % (i, event['millisecs_elapsed'], event['event_type'])
            ret_csv += this_event + "\n"
            last_i = i
        log.debug("CurrentStats rolled %d events, %s" % (last_i, EventTypeCounter) )
        self.finish(ret_csv)


class ReportEvent(BaseHandler):

    def get(self, eventstring):

        print "Now received notice of", eventstring
        add_measured_event(None, None, 0, eventstring, self.start_time)

        if not GLSettings.json_stats:
            self.set_status(405)
            self.finish()
        else:
            self.set_status(201)
            self.finish()

