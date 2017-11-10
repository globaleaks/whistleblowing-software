# -*- coding: utf-8 -*-
#
# anomaly
# *******
#
# GlobaLeaks cannot perform ratelimit and DoS protection based on source IP address
# because is designed to run in the Darknet. Therefore we've to implement a strict
# anomaly detection in order to raise alarm and trigger ratelimit of various nature.
#
# If you want know more:
# https://docs.google.com/a/apps.globaleaks.org/document/d/1P-uHM5K3Hhe_KD6YvARbRTuqjVOVj0VkI7qPO9aWFQw/edit
#
import copy

from twisted.internet import defer

from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.admin.user import db_get_admin_users
from globaleaks.orm import transact
from globaleaks.rest.apicache import ApiCache
from globaleaks.settings import Settings
from globaleaks.state import State
from globaleaks.transactions import db_schedule_email
from globaleaks.utils.singleton import Singleton
from globaleaks.utils.templating import Templating
from globaleaks.utils.utility import log, datetime_now, datetime_null, is_expired

ANOMALY_MAP = {
    'started_submissions': 50,
    'completed_submissions': 5,
    'failed_submissions': 5,
    'failed_logins': 8,
    'successful_logins': 20,
    'files': 10,
    'comments': 30,
    'messages': 30
}


def get_disk_anomaly_conditions(free_workdir_bytes, total_workdir_bytes, free_ramdisk_bytes, total_ramdisk_bytes):
    threshold_free_ramdisk_megabytes = 1
    free_disk_megabytes = free_workdir_bytes / (1024 * 1024)
    free_disk_percentage = free_workdir_bytes / (total_workdir_bytes / 100)
    free_ramdisk_megabytes = free_ramdisk_bytes / (1024 * 1024)

    def info_msg_0():
        return "free_disk_megabytes <= %d or free_disk_percentage <= %d" % \
            (State.tenant_cache[1].threshold_free_disk_megabytes_high,
             State.tenant_cache[1].threshold_free_disk_percentage_high)

    def info_msg_1():
        return "free_ramdisk_megabytes <= %d" % threshold_free_ramdisk_megabytes

    def info_msg_2():
        return "free_disk_megabytes <= %d or free_disk_percentage <= %d" % \
            (State.tenant_cache[1].threshold_free_disk_megabytes_low,
             State.tenant_cache[1].threshold_free_disk_percentage_low)

    # list of bad conditions ordered starting from the worst case scenario
    conditions = [
        {
            'condition': free_disk_megabytes <= State.tenant_cache[1].threshold_free_disk_megabytes_high or \
                         free_disk_percentage <= State.tenant_cache[1].threshold_free_disk_percentage_high,
            'info_msg': info_msg_0,
            'stress_level': 2,
            'accept_submissions': False
        },
        {
            'condition': free_ramdisk_megabytes <= threshold_free_ramdisk_megabytes,
            'info_msg': info_msg_1,
            'stress_level': 2,
            'accept_submissions': False
        },
        {
            'condition': free_disk_megabytes <= State.tenant_cache[1].threshold_free_disk_megabytes_low or \
                         free_disk_percentage <= State.tenant_cache[1].threshold_free_disk_percentage_low,
            'info_msg': info_msg_2,
            'stress_level': 1,
            'accept_submissions': True
        }
    ]

    return conditions


@transact
def generate_admin_alert_mail(store, alert):
    for user_desc in db_get_admin_users(store, 1):
        user_language = user_desc['language']

        data = {
            'type': u'admin_anomaly',
            'node': db_admin_serialize_node(store, 1, user_language),
            'notification': db_get_notification(store, 1, user_language),
            'alert': alert,
            'user': user_desc,
        }

        subject, body = Templating().get_mail_subject_and_body(data)

        db_schedule_email(store, 1, user_desc['mail_address'], subject, body)


class AlarmClass(object):
    """
    This class implement some classmethod used to report general
    usage of the system and the class itself return and operate
    over the stress level of the box.

    Class variables:
        @stress_levels
            Contain the ALARM [0 to 2] threshold for disk and activities.
    """
    __metaclass__ = Singleton

    # the level of the alarm in 30 seconds
    _alarm_level = {}
    _anomaly_history = {}

    latest_measured_freespace = 0
    latest_measured_totalspace = 0

    # keep track of the last sent email
    last_alarm_email = datetime_null()

    def __init__(self):
        self.current_time = datetime_now()

        self.difficulty_dict = {
            'human_captcha': False
        }

        self.reset()


    def reset(self):
        self.stress_levels = {
            'disk_space': 0,
            'disk_message': None,
            'activity': 0
        }

    @defer.inlineCallbacks
    def compute_activity_level(self):
        """
        This function update the Alarm level.

        """
        self.number_of_anomalies = 0

        current_event_matrix = {}

        requests_timing = []

        for tid in State.tenant_state:
            for event in State.tenant_state[tid].RecentEventQ:
                current_event_matrix.setdefault(event.event_type, 0)
                current_event_matrix[event.event_type] += 1

        for event_name, threshold in ANOMALY_MAP.items():
            if event_name in current_event_matrix:
                if current_event_matrix[event_name] > threshold:
                    self.number_of_anomalies += 1
                else:
                    log.debug("[compute_activity_level] %s %d < %d: it's OK (Anomalies recorded so far %d)",
                              event_name,
                              current_event_matrix[event_name],
                              threshold, self.number_of_anomalies)

        previous_activity_sl = self.stress_levels['activity']

        # Behavior: once the activity has reach a peek, the stress level
        # is raised at RED (two), and then is decremented at YELLOW (one) in the
        # next evaluation.

        report_function = log.debug
        self.stress_levels['activity'] = 0

        if self.number_of_anomalies == 1:
            report_function = log.info
            self.stress_levels['activity'] = 1
        elif self.number_of_anomalies > 1:
            report_function = log.info
            self.stress_levels['activity'] = 2

        # slow downgrade, if something has triggered a two, next step to 1
        if previous_activity_sl == 2 and not self.stress_levels['activity']:
            self.stress_levels['activity'] = 1

        # if there are some anomaly or we're nearby, record it.
        if self.number_of_anomalies >= 1 or self.stress_levels['activity'] >= 1:
            State.tenant_state[tid].AnomaliesQ.append([datetime_now(), current_event_matrix, self.stress_levels['activity']])

        if previous_activity_sl or self.stress_levels['activity']:
            report_function("in Activity stress level switch from %d => %d" %
                            (previous_activity_sl,
                             self.stress_levels['activity']))


        yield self.generate_admin_alert_mail(current_event_matrix)

        ret = self.stress_levels['activity'] - previous_activity_sl

        defer.returnValue(ret if ret > 0 else 0)

    def generate_admin_alert_mail(self, event_matrix):
        """
        This function put a mail in queue for the Admin, if the
        Admin notification is disable or if another Anomaly has been
        raised in the last 15 minutes, email is not send.
        """
        do_not_stress_admin_with_more_than_an_email_every_minutes = 120

        if not (self.stress_levels['activity'] or self.stress_levels['disk_space']):
            # we are lucky! no stress activities detected, no mail needed
            return

        if State.tenant_cache[1].notif.disable_admin_notification_emails:
            return

        if not is_expired(self.last_alarm_email, minutes=do_not_stress_admin_with_more_than_an_email_every_minutes):
            return

        alert = {
            'stress_levels': copy.deepcopy(self.stress_levels),
            'latest_measured_freespace': copy.deepcopy(self.latest_measured_freespace),
            'latest_measured_totalspace': copy.deepcopy(self.latest_measured_totalspace),
            'event_matrix': copy.deepcopy(event_matrix)
        }

        self.last_alarm_email = datetime_now()
        return generate_admin_alert_mail(alert)

    def check_disk_anomalies(self, free_workdir_bytes, total_workdir_bytes, free_ramdisk_bytes, total_ramdisk_bytes):
        """
        Here in Alarm is written the threshold to say if we're in disk alarm
        or not. Therefore the function "report" the amount of free space and
        the evaluation + alarm shift is performed here.

        workingdir: is performed a percentage check (at least 1% and an absolute comparison)
        ramdisk: a 2kbytes is expected at least to store temporary encryption keys

        "unusable node" threshold: happen when the space is really shitty.
        https://github.com/globaleaks/GlobaLeaks/issues/297
        https://github.com/globaleaks/GlobaLeaks/issues/872
        """

        self.latest_measured_freespace = free_workdir_bytes
        self.latest_measured_totalspace = total_workdir_bytes

        disk_space = 0
        disk_message = ""
        accept_submissions = True
        old_accept_submissions = State.accept_submissions

        for c in get_disk_anomaly_conditions(free_workdir_bytes,
                                             total_workdir_bytes,
                                             free_ramdisk_bytes,
                                             total_ramdisk_bytes):
            if c['condition']:
                disk_space = c['stress_level']

                info_msg = c['info_msg']()

                if disk_space == 2:
                    disk_message = "[FATAL] Disk anomaly, submissions disabled: %s" % info_msg
                else:  # == 1
                    disk_message = "[WARNING]: Disk anomaly: %s" % info_msg

                accept_submissions = c['accept_submissions']
                break

        # This check is temporarily, want to be verified that the switch can be
        # logged as part of the Anomalies via this function
        old_stress_level = self.stress_levels['disk_space']
        if old_stress_level != disk_space:
            if disk_message:
                log.err(disk_message)
            else:
                log.err("Available disk space returned to normal levels")

        # the value is set here with a single assignment in order to
        # minimize possible race conditions resetting/settings the values
        self.stress_levels['disk_space'] = disk_space
        self.stress_levels['disk_message'] = disk_message

        # if not on testing change accept_submission to the new value
        State.accept_submissions = accept_submissions if not Settings.testing else True

        if old_accept_submissions != State.accept_submissions:
            log.info("Switching disk space availability from: %s to %s",
                     old_accept_submissions, accept_submissions)

            # Must invalidate the cache here becuase accept_subs served in /public has changed
            ApiCache.invalidate()


# Alarm is a singleton class exported once
Alarm = AlarmClass()
