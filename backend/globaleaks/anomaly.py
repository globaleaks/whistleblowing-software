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
from twisted.internet import defer

from globaleaks import models, event
from globaleaks.orm import transact_ro
from globaleaks.handlers.admin.user import get_admin_users
from globaleaks.handlers.admin.notification import get_notification
from globaleaks.rest.apicache import GLApiCache
from globaleaks.settings import GLSettings
from globaleaks.utils.mailutils import sendmail
from globaleaks.utils.utility import log, datetime_now, is_expired, \
    datetime_to_ISO8601, bytes_to_pretty_str


def update_AnomalyQ(event_matrix, alarm_level):
    date = datetime_now()

    GLSettings.RecentAnomaliesQ.update({
        date: [event_matrix, alarm_level]
    })


@defer.inlineCallbacks
def compute_activity_level():
    """
    This function is called by the scheduled task, to update the
    Alarm level.

    At the end of the execution, reset to 0 the counters,
    this is why the content are copied for the statistic
    acquiring later.
    """
    Alarm.number_of_anomalies = 0

    current_event_matrix = {}

    requests_timing = []

    for _, event_obj in event.EventTrackQueue.queue.iteritems():
        current_event_matrix.setdefault(event_obj.event_type, 0)
        current_event_matrix[event_obj.event_type] += 1
        requests_timing.append(event_obj.request_time)

    if len(requests_timing) > 2:
        log.info("In latest %d seconds: worst RTT %f, best %f" %
                 (GLSettings.anomaly_delta,
                  round(max(requests_timing), 2),
                  round(min(requests_timing), 2)))

    for event_name, threshold in Alarm.OUTCOMING_ANOMALY_MAP.iteritems():
        if event_name in current_event_matrix:
            if current_event_matrix[event_name] > threshold:
                Alarm.number_of_anomalies += 1
            else:
                log.debug("[compute_activity_level] %s %d < %d: it's OK (Anomalies recorded so far %d)" %
                          (event_name,
                           current_event_matrix[event_name],
                           threshold, Alarm.number_of_anomalies))

    previous_activity_sl = Alarm.stress_levels['activity']

    # Behavior: once the activity has reach a peek, the stress level
    # is raised at RED (two), and then is decremented at YELLOW (one) in the
    # next evaluation.

    if Alarm.number_of_anomalies >= 2:
        report_function = log.msg
        Alarm.stress_levels['activity'] = 2
    elif Alarm.number_of_anomalies == 1:
        report_function = log.info
        Alarm.stress_levels['activity'] = 1
    else:
        report_function = log.debug
        Alarm.stress_levels['activity'] = 0

    # slow downgrade, if something has triggered a two, next step to 1
    if previous_activity_sl == 2 and not Alarm.stress_levels['activity']:
        Alarm.stress_levels['activity'] = 1

    # if there are some anomaly or we're nearby, record it.
    if Alarm.number_of_anomalies >= 1 or Alarm.stress_levels['activity'] >= 1:
        update_AnomalyQ(current_event_matrix,
                        Alarm.stress_levels['activity'])

    if previous_activity_sl or Alarm.stress_levels['activity']:
        report_function("in Activity stress level switch from %d => %d" %
                        (previous_activity_sl,
                         Alarm.stress_levels['activity']))


    mailinfos = yield Alarm.admin_alarm_generate_mail(current_event_matrix)
    for mailinfo in mailinfos:
        Alarm.last_alarm_email = datetime_now()
        yield sendmail(mailinfo['mail_address'], mailinfo['subject'], mailinfo['body'])

    defer.returnValue(Alarm.stress_levels['activity'] - previous_activity_sl)


def get_disk_anomaly_conditions(free_workdir_bytes, total_workdir_bytes, free_ramdisk_bytes, total_ramdisk_bytes):
    threshold_free_ramdisk_megabytes = 1
    free_disk_megabytes = free_workdir_bytes / (1024 * 1024)
    free_disk_percentage = free_workdir_bytes / (total_workdir_bytes / 100)
    free_ramdisk_megabytes = free_ramdisk_bytes / (1024 * 1024)
    free_workdir_string = bytes_to_pretty_str(free_workdir_bytes)
    free_ramdisk_string = bytes_to_pretty_str(free_ramdisk_bytes)
    total_workdir_string = bytes_to_pretty_str(total_workdir_bytes)
    total_ramdisk_string = bytes_to_pretty_str(total_ramdisk_bytes)

    def info_msg_0():
        return "free_disk_megabytes <= %d or free_disk_percentage <= %d" % \
            (GLSettings.memory_copy.threshold_free_disk_megabytes_high,
             GLSettings.memory_copy.threshold_free_disk_percentage_high)

    def info_msg_1():
        return "free_ramdisk_megabytes <= %d" % threshold_free_ramdisk_megabytes

    def info_msg_2():
        return "free_disk_megabytes <= %d or free_disk_percentage <= %d" % \
            (GLSettings.memory_copy.threshold_free_disk_megabytes_medium,
             GLSettings.memory_copy.threshold_free_disk_percentage_medium)

    def info_msg_3():
        return "free_disk_megabytes <= %d or free_disk_percentage <= %d" % \
            (GLSettings.memory_copy.threshold_free_disk_megabytes_low,
             GLSettings.memory_copy.threshold_free_disk_percentage_low)

    # list of bad conditions ordered starting from the worst case scenario
    conditions = [
        {
            'condition': free_disk_megabytes <= GLSettings.memory_copy.threshold_free_disk_megabytes_high or \
                         free_disk_percentage <= GLSettings.memory_copy.threshold_free_disk_percentage_high,
            'info_msg': info_msg_0,
            'stress_level': 3,
            'accept_submissions': False
        },
        {
            'condition': free_ramdisk_megabytes <= threshold_free_ramdisk_megabytes,
            'info_msg': info_msg_1,
            'stress_level': 3,
            'accept_submissions': False
        },
        {
            'condition': free_disk_megabytes <= GLSettings.memory_copy.threshold_free_disk_megabytes_medium or \
                         free_disk_percentage <= GLSettings.memory_copy.threshold_free_disk_percentage_medium,
            'info_msg': info_msg_2,
            'stress_level': 2,
            'accept_submissions': True
        },
        {
            'condition': free_disk_megabytes <= GLSettings.memory_copy.threshold_free_disk_megabytes_low or \
                         free_disk_percentage <= GLSettings.memory_copy.threshold_free_disk_percentage_low,
            'info_msg': info_msg_3,
            'stress_level': 1,
            'accept_submissions': True
        }
    ]

    return conditions


class Alarm(object):
    """
    This class implement some classmethod used to report general
    usage of the system and the class itself return and operate
    over the stress level of the box.

    Class variables:
        @stress_levels
            Contain the ALARM [0 to 2] threshold for disk and activities.
    """

    stress_levels = {
        'disk_space': 0,
        'disk_message': None,
        'activity': 0,
        'notification': [],
    }

    # _DISK_ALARM express the number of files upload (at maximum size) that can be stored
    _MEDIUM_DISK_ALARM = 15
    _HIGH_DISK_ALARM = 5
    # is a rough indicator, every file got compression + encryption so the true disk
    # space can't be estimated correctly.

    INCOMING_ANOMALY_MAP = {
    }

    OUTCOMING_ANOMALY_MAP = {
         # Remind: started submission at the moment can be triggered also by a crawler
        'started_submissions': 50,
        'completed_submissions': 5,
        'rejected_submissions': 5,
        'failed_logins': 8,
        'successful_logins': 20,
        'uploaded_files': 10,
        'appended_files': 10,
        'wb_comments': 20,
        'wb_messages': 20,
        'receiver_comments': 30,
        'receiver_messages': 30
    }

    # the level of the alarm in 30 seconds
    _alarm_level = {}
    _anomaly_history = {}

    latest_measured_freespace = 0
    latest_measured_totalspace = 0

    # keep track of the last sent email
    last_alarm_email = None

    def __init__(self):
        self.current_time = datetime_now()

        self.difficulty_dict = {
            'human_captcha': False,
            'graph_captcha': False
        }


    @staticmethod
    def reset():
        Alarm.stress_levels = {
            'disk_space': 0,
            'disk_message': None,
            'activity': 0,
            'notification': [],
        }

    @staticmethod
    @defer.inlineCallbacks
    def admin_alarm_generate_mail(event_matrix):
        """
        This function put a mail in queue for the Admin, if the
        Admin notification is disable or if another Anomaly has been
        raised in the last 15 minutes, email is not send.
        """
        ret = []

        do_not_stress_admin_with_more_than_an_email_every_minutes = 120

        def replace_keywords(text):
            iterations = 3
            stop = False
            while (stop == False and iterations > 0):
                iterations -= 1
                count = 0
                for keyword, function in KeywordTemplate.iteritems():
                    where = text.find(keyword)
                    if where == -1:
                        continue

                    count += 1

                    text = "%s%s%s" % (
                        text[:where],
                        function(notification_dict),
                        text[where + len(keyword):])

                    if count == 0:
                        # finally!
                        stop = True
                        break

        def _disk_anomaly_detail(notification_dict):
            # This happens all the time anomalies are present but disk is ok
            if Alarm.stress_levels['disk_space'] == 0:
                return u''

            if Alarm.stress_levels['disk_space'] == 1:
                return notification_dict['admin_anomaly_disk_low']
            elif Alarm.stress_levels['disk_space'] == 2:
                return notification_dict['admin_anomaly_disk_medium']
            else:
                return notification_dict['admin_anomaly_disk_high']

        def _activities_anomaly_detail(notification_dict):
            # This happens all the time there is not anomalous traffic
            if Alarm.stress_levels['activity'] == 0:
                return u''

            return notification_dict['admin_anomaly_activities']

        def _activity_alarm_level(notification_dict):
            return "%s" % Alarm.stress_levels['activity']

        def _activity_dump(notification_dict):
            retstr = ""

            for event, amount in event_matrix.iteritems():
                if not amount:
                    continue
                retstr = "%s%s%d\n%s" % \
                         (event, (25 - len(event)) * " ", amount, retstr)

            return retstr

        def _node_name(notification_dict):
            return unicode(GLSettings.memory_copy.nodename)

        def _free_disk_space(notification_dict):
            return "%s" % bytes_to_pretty_str(Alarm.latest_measured_freespace)

        def _total_disk_space(notification_dict):
            return "%s" % bytes_to_pretty_str(Alarm.latest_measured_totalspace)

        def _notifications_suppressed(notification_dict):
            if Alarm.stress_levels['notification'] == []:
                return u''
            return "** %s **" % Alarm.stress_levels['notification']

        KeywordTemplate = {
            "%AnomalyDetailDisk%": _disk_anomaly_detail,
            "%AnomalyDetailActivities%": _activities_anomaly_detail,
            "%ActivityAlarmLevel%": _activity_alarm_level,
            "%ActivityDump%": _activity_dump,
            "%NotificationsSuppressed%": _notifications_suppressed,
            "%NodeName%": _node_name,
            "%FreeMemory%": _free_disk_space,
            "%TotalMemory%": _total_disk_space,
        }
        # ------------------------------------------------------------------

        if not (Alarm.stress_levels['activity'] or
                    Alarm.stress_levels['disk_space'] or
                    Alarm.stress_levels['notification']):
            # we are lucky! no stress activities detected, no mail needed
            defer.returnValue([])

        if GLSettings.memory_copy.disable_admin_notification_emails:
            defer.returnValue([])

        if Alarm.last_alarm_email:
            if not is_expired(Alarm.last_alarm_email,
                              minutes=do_not_stress_admin_with_more_than_an_email_every_minutes):
                defer.returnValue([])

        admin_users = yield get_admin_users()
        for u in admin_users:
            notification_dict = yield get_notification(u['language'])

            subject = notification_dict['admin_anomaly_mail_title']
            body = notification_dict['admin_anomaly_mail_template']

            replace_keywords(subject)
            replace_keywords(body)

            ret.append({
                'mail_address': u['mail_address'],
                'subject': subject,
                'body': body
            })

        defer.returnValue(ret)


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

        Alarm.latest_measured_freespace = free_workdir_bytes
        Alarm.latest_measured_totalspace = total_workdir_bytes

        disk_space = 0
        disk_message = ""
        accept_submissions = True
        old_accept_submissions = GLSettings.memory_copy.accept_submissions

        for c in get_disk_anomaly_conditions(free_workdir_bytes,
                                             total_workdir_bytes,
                                             free_ramdisk_bytes,
                                             total_ramdisk_bytes):
            if c['condition']:
                disk_space = c['stress_level']

                info_msg = c['info_msg']()

                if disk_space <= GLSettings.disk_alarm_threshold:
                    # No alarm to be concerned, then
                    disk_space = 0
                else:
                    if disk_space == 3:
                        disk_message = "Fatal (Submission disabled): %s" % info_msg
                    elif disk_space == 2:
                        disk_message = "Critical (Submission near to be disabled): %s" % info_msg
                    else:  # == 1
                        disk_message = "Warning: %s" % info_msg

                    accept_submissions = c['accept_submissions']
                    log.err(disk_message)
                    break

        # This check is temporarily, want to be verified that the switch can be
        # logged as part of the Anomalies via this function
        old_stress_level = Alarm.stress_levels['disk_space']
        if old_stress_level != disk_space:
            log.debug("Switch in Disk space available status, %d => %d" %
                      (old_stress_level, disk_space))

        # the value is set here with a single assignment in order to
        # minimize possible race conditions resetting/settings the values
        Alarm.stress_levels['disk_space'] = disk_space
        Alarm.stress_levels['disk_message'] = disk_message

        GLSettings.memory_copy.accept_submissions = accept_submissions

        if old_accept_submissions != GLSettings.memory_copy.accept_submissions:
            log.info("Switching disk space availability from: %s to %s" % (
                "True" if old_accept_submissions else "False",
                "False" if old_accept_submissions else "True"))

            # Invalidate the cache of node avoiding accesses to the db from here
            GLApiCache.invalidate('node')
