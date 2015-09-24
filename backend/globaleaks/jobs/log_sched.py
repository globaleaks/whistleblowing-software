# -*- coding: utf-8 -*-
#
#   log_sched
#   ****************
#
import os
from twisted.internet.defer import inlineCallbacks, returnValue
from storm.expr import Desc, Asc

from globaleaks.anomaly import Alarm, compute_activity_level
from globaleaks.jobs.base import GLJob
from globaleaks.settings import GLSettings, transact, transact_ro
from globaleaks.models import Stats, Anomalies, Log
from globaleaks.utils.utility import log, datetime_now, datetime_null
from globaleaks.utils.logger import LogQueue, LoggedEvent


class LogSchedule(GLJob):
    """
    This class just flush the logs in the Database, is executed quite
    frequently, and the goal is to record the event safely. the events
    are kept in memory, by the globaleaks.utils.logger.Log* classes

    """
    name = "Log"

    highest_logged_id = 0

    @transact_ro
    def initialize_highest_id(self, store):

        max_id_check = store.find(Log)
        max_id_check.order_by(Desc(Log.id))

        if max_id_check.count() < 2:
            print "spiacente! si esce"
            return

        print "Desc", max_id_check[-1], max_id_check[0]

        max_id_check = store.find(Log)
        max_id_check.order_by(Asc(Log.id))
        print "Asc", max_id_check[-1], max_id_check[0]


    @transact
    def dump_fresh_logs(self, store):

        for who, whatzz in LogQueue._all_queues.iteritems():
            for what in whatzz:
                print who, what
                nl = Log()

                nl.id = what.id
                nl.code = what.log_code
                nl.args = what.args
                nl.log_date = what.log_code
                nl.subject = what.subject
                nl.subject_id = what.subject_id
                nl.log_level = what.level
                nl.mail = what.mail
                nl.mail_sent = False
                nl.repeated = what.repeated
                nl.last_repetition_date = what.last_repetition_date

                store.add(nl)

        print "done!"


    @inlineCallbacks
    def operation(self):

        if not LogSchedule.highest_logged_id:
            yield self.initialize_highest_id()

        if LoggedEvent.get_last_log_id() > LogSchedule.highest_logged_id:
            yield self.dump_fresh_logs()

        returnValue(None)
