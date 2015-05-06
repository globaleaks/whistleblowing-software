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
from globaleaks.rest.apicache import GLApiCache
from globaleaks.settings import GLSetting, transact_ro
from globaleaks.utils.mailutils import MIME_mail_build, sendmail
from globaleaks.utils.utility import log, datetime_now, is_expired, \
    datetime_to_ISO8601, bytes_to_pretty_str
from globaleaks.utils.tempobj import TempObj


def update_AnomalyQ(event_matrix, alarm_level):
    date = datetime_to_ISO8601(datetime_now())[:-8]

    GLSetting.RecentAnomaliesQ.update({
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
                 (GLSetting.anomaly_seconds_delta,
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

    # Alarm notification get the copy of the latest activities
    yield Alarm.admin_alarm_notification(current_event_matrix)

    defer.returnValue(Alarm.stress_levels['activity'] - previous_activity_sl)


def get_disk_anomaly_conditions(free_workdir_bytes, total_workdir_bytes, free_ramdisk_bytes, total_ramdisk_bytes):
    free_disk_megabytes = free_workdir_bytes / (1024 * 1024)
    free_disk_percentage = free_workdir_bytes / (total_workdir_bytes / 100)
    free_workdir_string = bytes_to_pretty_str(free_workdir_bytes)
    free_ramdisk_string = bytes_to_pretty_str(free_ramdisk_bytes)
    total_workdir_string = bytes_to_pretty_str(total_workdir_bytes)

    def info_msg_0(free_workdir_bytes, total_workdir_bytes, free_ramdisk_bytes, total_ramdisk_bytes):
        return "Disk space < 1%%: %s on %s" % (total_workdir_string, free_workdir_string)

    def info_msg_1(free_workdir_bytes, total_workdir_bytes, free_ramdisk_bytes, total_ramdisk_bytes):
        return "Minimum space available of %d Mb reached: (%s on %s)" % \
                (GLSetting.defaults.minimum_megabytes_required,
                total_workdir_string,
                free_workdir_string)

    def info_msg_2(free_workdir_bytes, total_workdir_bytes, free_ramdisk_bytes, total_ramdisk_bytes):
        return "Ramdisk space not enough space (%s): required 2Kb" % free_ramdisk_string

    def info_msg_3(free_workdir_bytes, total_workdir_bytes, free_ramdisk_bytes, total_ramdisk_bytes):
        return "Disk space ~ 2%% (Critical when reach 1%%): %s on %s" % \
                (total_workdir_string, free_workdir_string)

    def info_msg_4(free_workdir_bytes, total_workdir_bytes, free_ramdisk_bytes, total_ramdisk_bytes):
        return "Minimum space available of %d Mb is near: (%s on %s)" % \
                (GLSetting.defaults.minimum_megabytes_required,
                 total_workdir_string,
                 free_workdir_string)

    def info_msg_5(free_workdir_bytes, total_workdir_bytes, free_ramdisk_bytes, total_ramdisk_bytes):
        return "Disk space permit maximum of %d uploads (%s on %s)" % \
                (Alarm._HIGH_DISK_ALARM, total_workdir_string, free_workdir_string)

    def info_msg_6(free_workdir_bytes, total_workdir_bytes, free_ramdisk_bytes, total_ramdisk_bytes):
        return "Disk space permit maximum of %d uploads (%s on %s)" % \
                (Alarm._MEDIUM_DISK_ALARM, total_workdir_string, free_workdir_string)

    # list of bad conditions ordered starting from the worst case scenario
    conditions = [
        {
            # If percentage is <= 1%: disable the submission
            'condition': free_disk_percentage <= 1,
            'info_msg': info_msg_0,
            'stress_level': 3,
            'accept_submissions': False,
        },
        {
            # If disk has less than the hardcoded minimum amount (1Gb)
            'condition': free_disk_megabytes <= GLSetting.defaults.minimum_megabytes_required,
            'info_msg': info_msg_1,
            'stress_level': 3,
            'accept_submissions': False,
        },
        {
            # If ramdisk has less than 2kbytes
            'condition': free_ramdisk_bytes <= 2048,
            'info_msg': info_msg_2,
            'stress_level': 3,
            'accept_submissions': False,
        },
        {
            # If percentage is 2% start to alert the admin on the upcoming critical situation
            'condition': free_disk_percentage == 2,
            'info_msg': info_msg_3,
            'stress_level': 2,
            'accept_submissions': True,
        },
        {
            # Again to avoid bad surprise, we alert the admin at (minimum disk required * 2)
            'condition': free_disk_megabytes <= (GLSetting.defaults.minimum_megabytes_required * 2),
            'info_msg': info_msg_4,
            'stress_level': 2,
            'accept_submissions': True,
        },
        {
            # if 5 times maximum file can be accepted
            'condition': free_disk_megabytes <= (Alarm._HIGH_DISK_ALARM * GLSetting.memory_copy.maximum_filesize),
            'info_msg': info_msg_5,
            'stress_level': 2,
            'accept_submissions': True,
        },
        {
            # if 15 times maximum file size can be accepted
            'condition': free_disk_megabytes <= (Alarm._MEDIUM_DISK_ALARM * GLSetting.memory_copy.maximum_filesize),
            'info_msg': info_msg_6,
            'stress_level': 1,
            'accept_submissions': True,
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
    }

    # _DISK_ALARM express the number of files upload (at maximum size) that can be stored
    _MEDIUM_DISK_ALARM = 15
    _HIGH_DISK_ALARM = 5
    # is a rough indicator, every file got compression + encryption so the true disk
    # space can't be estimated correctly.

    INCOMING_ANOMALY_MAP = {
    }

    OUTCOMING_ANOMALY_MAP = {
        'failed_logins': 50,
        'successful_logins': 70,
        'started_submissions': 100,
        'completed_submissions': 50,
        'uploaded_files': 100,
        'appended_files': 100,
        'wb_comments': 20,
        'wb_messages': 20,
        'receiver_comments': 30,
        'receiver_messages': 30
    }

    # the level of the alarm in 30 seconds
    _alarm_level = {}
    _anomaly_history = {}

    latest_measured_freespace = None

    # keep track of the last sent email
    last_alarm_email = None

    def __init__(self):
        self.current_time = datetime_now()

        self.difficulty_dict = {
            'human_captcha': False,
            'graph_captcha': False,
            'proof_of_work': False
        }


    @staticmethod
    def reset():
        Alarm.stress_levels = {
            'disk_space': 0,
            'disk_message': None,
            'activity': 0
        }

    def get_token_difficulty(self):
        """
        This function return the difficulty that will be enforced in the
        token, whenever is File or Submission, here is evaluated with a dict.
        """
        # TODO make a proper assessment between pissed off users and defeated DoS
        if Alarm.stress_levels['activity'] >= 1:
            self.difficulty_dict['human_captcha'] = True

        if Alarm.stress_levels['disk_space'] >= 1:
            self.difficulty_dict['human_captcha'] = True

        log.debug("get_token_difficulty in %s is: HC:%s, GC:%s, PoW:%s" % (
            self.current_time,
            "Y" if self.difficulty_dict['human_captcha'] else "N",
            "Y" if self.difficulty_dict['graph_captcha'] else "N",
            "Y" if self.difficulty_dict['proof_of_work'] else "N" ))

        return self.difficulty_dict

    @staticmethod
    @defer.inlineCallbacks
    def admin_alarm_notification(event_matrix):
        """
        This function put a mail in queue for the Admin, if the
        Admin notification is disable or if another Anomaly has been
        raised in the last 15 minutes, email is not send.
        """
        # import here in order to avoid circular import error
        from globaleaks.handlers.admin.notification import get_notification

        do_not_stress_admin_with_more_than_an_email_after_minutes = 15

        @transact_ro
        def _get_node_admin_email(store):
            node = store.find(models.Node).one()
            return node.email

        @transact_ro
        def _get_admin_user_language(store):
            admin_user = store.find(models.User, models.User.username == u'admin').one()
            return admin_user.language

        @transact_ro
        def _get_message_template(store):
            admin_user = store.find(models.User, models.User.username == u'admin').one()
            notif = store.find(models.Notification).one()
            template = notif.admin_anomaly_template
            if admin_user.language in template:
                return template[admin_user.language]
            elif GLSetting.memory_copy.language in template:
                return template[GLSetting.memory_copy.language]
            else:
                raise Exception("Cannot find any language for admin notification")

        def _activity_alarm_level():
            return "%s" % Alarm.stress_levels['activity']

        def _activity_dump():
            retstr = ""
            for event, amount in event_matrix.iteritems():
                retstr = "%s: %d\n%s" % (event, amount, retstr)
            return retstr

        def _disk_alarm_level():
            return "%s" % Alarm.stress_levels['disk_space']

        def _disk_dump():
            return "%s" % bytes_to_pretty_str(Alarm.latest_measured_freespace)

        def _disk_status_message():
            if Alarm.stress_levels['disk_message']:
                return unicode(Alarm.stress_levels['disk_message'])
            else:
                return "Disk space OK"

        @transact_ro
        def _node_name(store):
            node = store.find(models.Node).one()
            return unicode(node.name)

        KeyWordTemplate = {
            "%ActivityAlarmLevel%": _activity_alarm_level,
            "%ActivityDump%": _activity_dump,
            "%DiskAlarmLevel%": _disk_alarm_level,
            "%DiskDump%": _disk_dump,
            "%DiskErrorMessage%": _disk_status_message,
            "%NodeName%": _node_name
        }
        # ------------------------------------------------------------------

        # Here start the Anomaly Notification code, before checking if we have to send email
        if not (Alarm.stress_levels['activity'] or Alarm.stress_levels['disk_space']):
            # lucky, no stress activities recorded: no mail needed
            defer.returnValue(None)

        if not GLSetting.memory_copy.admin_notif_enable:
            # event_matrix is {} if we are here only for disk
            log.debug("Anomaly to be reported %s, but Admin has Notification disabled" %
                      "[%s]" % event_matrix if event_matrix else "")
            defer.returnValue(None)

        if Alarm.last_alarm_email:
            if not is_expired(Alarm.last_alarm_email,
                              minutes=do_not_stress_admin_with_more_than_an_email_after_minutes):
                log.debug("Alert email want be send, but the threshold of %d minutes is not yet reached since %s" % (
                    do_not_stress_admin_with_more_than_an_email_after_minutes,
                    datetime_to_ISO8601(Alarm.last_alarm_email)))
                defer.returnValue(None)

        # and now, processing the template
        message = yield _get_message_template()
        for keyword, templ_funct in KeyWordTemplate.iteritems():

            where = message.find(keyword)

            if where == -1:
                continue

            # based on the type of templ_funct, we've to use 'yield' or not
            # cause some returns a deferred.
            if isinstance(templ_funct, type(sendmail)):
                content = templ_funct()
            else:
                content = yield templ_funct()

            message = "%s%s%s" % (
                message[:where],
                content,
                message[where + len(keyword):])

        admin_email = yield _get_node_admin_email()

        admin_language = yield _get_admin_user_language()

        notification_settings = yield get_notification(admin_language)

        message = MIME_mail_build(GLSetting.memory_copy.notif_source_email,
                                  GLSetting.memory_copy.notif_source_email,
                                  admin_email,
                                  admin_email,
                                  notification_settings['admin_anomaly_mail_title'],
                                  message)

        log.debug('Alarm Email for admin (%s): connecting to [%s:%d], '
                  'the next mail should be in %d minutes' %
                  (event_matrix,
                   GLSetting.memory_copy.notif_server,
                   GLSetting.memory_copy.notif_port,
                   do_not_stress_admin_with_more_than_an_email_after_minutes))

        Alarm.last_alarm_email = datetime_now()

        # Currently the anomaly emails are disabled due to the fact that a
        # good and useful mail templates are still missing.
        #
        # yield sendmail(authentication_username=GLSetting.memory_copy.notif_username,
        #                authentication_password=GLSetting.memory_copy.notif_password,
        #                from_address=GLSetting.memory_copy.notif_source_email,
        #                to_address=admin_email,
        #                message_file=message,
        #                smtp_host=GLSetting.memory_copy.notif_server,
        #                smtp_port=GLSetting.memory_copy.notif_port,
        #                security=GLSetting.memory_copy.notif_security,
        #                event=None)

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

        disk_space = 0
        disk_message = ""
        accept_submissions = True
        old_accept_submissions = GLSetting.memory_copy.accept_submissions

        for c in get_disk_anomaly_conditions(free_workdir_bytes,
                                             total_workdir_bytes,
                                             free_ramdisk_bytes,
                                             total_ramdisk_bytes):
            if c['condition']:
                disk_space = c['stress_level']

                info_msg = c['info_msg'](free_workdir_bytes,
                                         total_workdir_bytes,
                                         free_ramdisk_bytes,
                                         total_ramdisk_bytes)

                if disk_space == 3:
                    disk_message = "Fatal (Submission disabled): %s" % info_msg
                elif disk_space == 2:
                    disk_message = "Critical (Submission near to be disabled): %s" % info_msg
                else:  # == 1
                    disk_message = "Warning: %s" % info_msg

                accept_submissions = c['accept_submissions']

                log.err(disk_message)

                break

        # the value is setted here with a single assignment in order to
        # minimize possible race conditions resetting/settings the values
        Alarm.stress_levels['disk_space'] = disk_space
        Alarm.stress_levels['disk_message'] = disk_message
        GLSetting.memory_copy.accept_submissions = accept_submissions

        if old_accept_submissions != GLSetting.memory_copy.accept_submissions:
            log.info("Switching disk space availability from: %s to %s" % (
                "True" if old_accept_submissions else "False",
                "False" if old_accept_submissions else "True"))

            # Invalidate the cache of node avoiding accesses to the db from here
            GLApiCache.invalidate('node')
