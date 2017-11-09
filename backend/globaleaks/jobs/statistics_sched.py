# -*- coding: utf-8 -*-
# Implement collection of statistics
import os

from globaleaks.anomaly import Alarm
from globaleaks.state import State
from globaleaks.jobs.base import LoopingJob
from globaleaks.models import Stats, Anomalies
from globaleaks.orm import transact_sync
from globaleaks.settings import Settings
from globaleaks.utils.utility import log, datetime_now


def get_workingdir_space():
    statvfs = os.statvfs(Settings.working_path)
    free_bytes = statvfs.f_frsize * statvfs.f_bavail
    total_bytes = statvfs.f_frsize * statvfs.f_blocks
    return free_bytes, total_bytes


def get_ramdisk_space():
    statvfs = os.statvfs(Settings.ramdisk_path)
    free_bytes = statvfs.f_frsize * statvfs.f_bavail
    total_bytes = statvfs.f_frsize * statvfs.f_blocks
    return free_bytes, total_bytes


@transact_sync
def save_anomalies(store, anomaly_list):
    for anomaly in anomaly_list:
        newanom = Anomalies()
        newanom.alarm = anomaly[2]
        newanom.date = anomaly[0]
        newanom.events = anomaly[1]
        store.add(newanom)


def get_anomalies():
    anomalies = []
    for when, anomaly_blob in dict(State.RecentAnomaliesQ).items():
        anomalies.append([when, anomaly_blob[0], anomaly_blob[1]])

    return anomalies

def get_statistics():
    statsummary = {}

    for descblob in State.RecentEventQ:
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


class AnomaliesSchedule(LoopingJob):
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


class StatisticsSchedule(LoopingJob):
    """
    Statistics collection scheduler run hourly
    """
    name = "Statistics"
    interval = 3600
    monitor_interval = 5 * 60

    def get_start_time(self):
        current_time = datetime_now()
        return 3600 - (current_time.minute * 60) - current_time.second

    def __init__(self):
        self.stats_collection_start_time = datetime_now()
        LoopingJob.__init__(self)

    def operation(self):
        # ------- BEGIN Anomalies section -------
        anomalies_to_save = get_anomalies()
        if anomalies_to_save:
            save_anomalies(anomalies_to_save)
            log.debug("Stored %d anomalies collected during the last hour", len(anomalies_to_save))

        # ------- END Anomalies section ---------

        # ------- BEGIN Stats section -----------
        current_time = datetime_now()
        statistic_summary = get_statistics()
        if statistic_summary:
            save_statistics(State.stats_collection_start_time, current_time, statistic_summary)
            log.debug("Stored statistics %s collected from %s to %s",
                      statistic_summary,
                      State.stats_collection_start_time,
                      current_time)
        # ------- END Stats section -------------

        # Hourly Resets
        State.reset_hourly()
