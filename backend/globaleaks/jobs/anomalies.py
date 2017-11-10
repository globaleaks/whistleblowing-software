# -*- coding: utf-8 -*-

# Implement anomalies check
from globaleaks import models
from globaleaks.anomaly import Alarm
from globaleaks.settings import Settings
from globaleaks.state import State
from globaleaks.jobs.base import LoopingJob
from globaleaks.orm import transact_sync
from globaleaks.utils.utility import get_disk_space


@transact_sync
def save_anomalies(store):
    for tid in State.tenant_state:
        for anomaly in State.tenant_state[tid].AnomaliesQ:
            a = models.Anomalies()
            a.tid = tid
            a.alarm = anomaly[2]
            a.date = anomaly[0]
            a.events = anomaly[1]
            store.add(a)


class Anomalies(LoopingJob):
    """
    This job checks for anomalies and take care of saving them on the db.
    """
    interval = 60

    def operation(self):
        Alarm.compute_activity_level()

        free_disk_bytes, total_disk_bytes = get_disk_space(Settings.working_path)
        free_ramdisk_bytes, total_ramdisk_bytes = get_disk_space(Settings.ramdisk_path)

        Alarm.check_disk_anomalies(free_disk_bytes, total_disk_bytes, free_ramdisk_bytes, total_ramdisk_bytes)

        save_anomalies()
