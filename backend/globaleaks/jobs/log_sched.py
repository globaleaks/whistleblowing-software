# -*- coding: utf-8 -*-
#
#   log_sched
#   *********
#
import os
from twisted.internet.defer import inlineCallbacks, returnValue
from storm.expr import Desc, Asc

from globaleaks.anomaly import Alarm, compute_activity_level
from globaleaks.jobs.base import GLJob
from globaleaks.settings import GLSettings, transact, transact_ro
from globaleaks.models import Stats, Anomalies, Log
from globaleaks.utils.utility import log, datetime_now, datetime_null
from globaleaks.utils.logger import LogQueue, LoggedEvent, initialize_LoggedEvent


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

        if max_id_check.count() == 0:
            log.debug("First initialization spotted!")
            LogSchedule.highest_logged_id = 1
        else:
            LogSchedule.highest_logged_id = max_id_check[0].id


    @transact
    def dump_fresh_logs(self, store):
        """
        Look in the current memory storage of Logs, if there is
        something not yet logged in the DB.

        In the meanwhile, if the number of entries overcome the
        50 elements, delete the old one. This mean that, worst case
        scenario, we have in memory 50 Object x (Tip Numb + Receiver Num + Admin)
        """

        amount_of_flusged_logs = 0
        for subject_uuid, log_sub_dict in LogQueue._all_queues.iteritems():

            cnt = 0
            for id, what in log_sub_dict.iteritems():
                cnt += 1
                if cnt > 50:
                    log.debug("TODO implement memory preserver here! %d, in %s" %
                              (cnt, subject_uuid))
                if id <= LogSchedule.highest_logged_id:
                    continue

                print "Dump new log:", what.log_code, what

                nl = Log()
                nl.id = id
                nl.code = what.log_code
                nl.args = what.args
                nl.log_date = what.log_date
                nl.subject = unicode(what.subject)
                nl.log_level = what.level
                nl.mail = what.mail
                nl.mail_sent = False
                nl.log_message = what.log_message

                if id > LogSchedule.highest_logged_id:
                    LogSchedule.highest_logged_id = id

                store.add(nl)
                amount_of_flusged_logs += 1

        return amount_of_flusged_logs


    def clean_itip_log_in_memory(self, internaltip_id):
        """
        :param internaltip_id:

        When an InternalTip get deleted, all the logs will remain in the
        DB, but not in memory. This is the function to clean it.
        """
        subject_uuid = 'itip_%s' % internaltip_id
        if subject_uuid in LogQueue._all_queues:
            print "Going to delete section of", subject_uuid
            import pprint
            pprint.pprint(LogQueue._all_queues)
            LogQueue._all_queues.remove(subject_uuid)
            pprint.pprint(LogQueue._all_queues)
        else:
            print "No traces of", subject_uuid


    @inlineCallbacks
    def operation(self):

        if not LoggedEvent._incremental_id:
            yield initialize_LoggedEvent()

        if not LogSchedule.highest_logged_id:
            yield self.initialize_highest_id()

        if LoggedEvent._incremental_id > LogSchedule.highest_logged_id:
            yield self.dump_fresh_logs()

        returnValue(None)
