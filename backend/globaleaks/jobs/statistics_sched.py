# -*- coding: utf-8 -*-
#
#   statistics_sched
#   ****************
#
#  Statistics works collecting every N-th minutes the amount of important
#  operations happened
#
#  This impact directly the statistics collection for OpenData purpose and
#  private information.
#  The anomaly detection based on stress level measurement.

import os

from globaleaks.anomaly import Alarm
from globaleaks.jobs.base import GLJob
from globaleaks.models import Stats, Anomalies
from globaleaks.orm import transact_sync
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import log, datetime_now


def get_workingdir_space():
    statvfs = os.statvfs(GLSettings.working_path)
    free_bytes = statvfs.f_frsize * statvfs.f_bavail
    total_bytes = statvfs.f_frsize * statvfs.f_blocks
    return free_bytes, total_bytes

def get_ramdisk_space():
    statvfs = os.statvfs(GLSettings.ramdisk_path)
    free_bytes = statvfs.f_frsize * statvfs.f_bavail
    total_bytes = statvfs.f_frsize * statvfs.f_blocks
    return free_bytes, total_bytes


@transact_sync
def save_anomalies(store, anomaly_list):
    for anomaly in anomaly_list:
        anomaly_date, anomaly_desc, alarm_raised = anomaly

        newanom = Anomalies()
        newanom.alarm = alarm_raised
        newanom.date = anomaly_date
        newanom.events = anomaly_desc
        log.debug("adding new anomaly in to the record: %s, %s, %s" % (alarm_raised, anomaly_date, anomaly_desc))
        store.add(newanom)

    if len(anomaly_list):
        log.debug("save_anomalies: Saved %d anomalies collected during the last hour" % len(anomaly_list))


def get_anomalies():
    anomalies = []
    for when, anomaly_blob in dict(GLSettings.RecentAnomaliesQ).iteritems():
        anomalies.append([when, anomaly_blob[0], anomaly_blob[1]])

    return anomalies

def get_statistics():
    statsummary = {}

    for descblob in GLSettings.RecentEventQ:
        if 'event' not in descblob:
            continue

        statsummary.setdefault(descblob['event'], 0)
        statsummary[descblob['event']] += 1

    return statsummary

@transact_sync
def save_statistics(store, start, end, activity_collection):
    newstat = Stats()
    newstat.start = start
    newstat.summary = dict(activity_collection)
    newstat.free_disk_space = get_workingdir_space()[0]
    store.add(newstat)

    if activity_collection:
        log.debug("save_statistics: Saved statistics %s collected from %s to %s" %
                  (activity_collection, start, end))


class AnomaliesSchedule(GLJob):
    """
    This job checks for anomalies and take care of saving them on the db.
    """
    name = "Anomalies"
    interval = 30

    def operation(self):
        Alarm.compute_activity_level()

        free_disk_bytes, total_disk_bytes = get_workingdir_space()
        free_ramdisk_bytes, total_ramdisk_bytes = get_ramdisk_space()

        Alarm.check_disk_anomalies(free_disk_bytes, total_disk_bytes, free_ramdisk_bytes, total_ramdisk_bytes)


class StatisticsSchedule(GLJob):
    """
    Statistics collection scheduler runned hourly
    """
    name = "Statistics"
    interval = 3600
    monitor_interval = 5 * 60

    def get_start_time(self):
         current_time = datetime_now()
         return 3600 - (current_time.minute * 60) - current_time.second

    def __init__(self):
        self.stats_collection_start_time = datetime_now()
        GLJob.__init__(self)

    def operation(self):
        # ------- BEGIN Anomalies section -------
        anomalies_to_save = get_anomalies()
        save_anomalies(anomalies_to_save)
        # ------- END Anomalies section ---------

        # ------- BEGIN Stats section -----------
        current_time = datetime_now()
        statistic_summary = get_statistics()
        save_statistics(GLSettings.stats_collection_start_time, current_time, statistic_summary)
        # ------- END Stats section -------------

        # Hourly Resets
        GLSettings.reset_hourly()

        log.debug("Saved stats and time updated, keys saved %d" % len(statistic_summary.keys()))
