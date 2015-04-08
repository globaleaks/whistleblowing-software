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

from globaleaks import models
from globaleaks.settings import GLSetting, transact_ro
from globaleaks.utils.mailutils import MIME_mail_build, sendmail
from globaleaks.utils.utility import log, datetime_now, is_expired, \
    datetime_to_ISO8601, bytes_to_pretty_str
from globaleaks.utils.tempobj import TempObj

# needed in order to allow UT override
reactor_override = None

# follow the checker, they are executed from handlers/base.py
# prepare() or flush()
def file_upload_check(uri):
    # /submission/ + token_id + /file  = 59 bytes
    return len(uri) == 59 and uri.endswith('/file')


def file_append_check(uri):
    return uri == '/wbtip/upload'


def submission_check(uri):
    return uri == '/submission'


def login_check(uri):
    return uri == '/authentication'


def wb_message_check(uri):
    return uri.startswith('/wbtip/messages/')


def wb_comment_check(uri):
    return uri == '/wbtip/comments'


def rcvr_message_check(uri):
    return uri.startswith('/rtip/messages/')


def rcvr_comment_check(uri):
    return uri.startswith('/rtip/comments')


def failure_status_check(http_code):
    # if code is missing is a failure because an Exception is raise before set
    # the status.
    return http_code >= 400


def created_status_check(http_code):
    # if missing, is a failure => False
    return http_code == 201


def ok_status_check(HTTP_code):
    return HTTP_code == 200


def update_status_check(http_code):
    return http_code == 202


incoming_event_monitored = [
    # {
    # 'name' : 'submission',
    # 'handler_check': submission_check,
    # 'anomaly_management': None,
    # 'method': 'POST'
    # }
]

outcoming_event_monitored = [
    {
        'name': 'failed_logins',
        'method': 'POST',
        'handler_check': login_check,
        'status_checker': failure_status_check,
        'anomaly_management': None,
    },
    {
        'name': 'successful_logins',
        'method': 'POST',
        'handler_check': login_check,
        'status_checker': ok_status_check,
        'anomaly_management': None,
    },
    {
        'name': 'started_submissions',
        'method': 'POST',
        'handler_check': submission_check,
        'status_checker': created_status_check,
        'anomaly_management': None,
    },
    {
        'name': 'completed_submissions',
        'method': 'PUT',
        'handler_check': submission_check,
        'status_checker': update_status_check,
        'anomaly_management': None,
    },
    {
        'name': 'wb_comments',
        'handler_check': wb_comment_check,
        'status_checker': created_status_check,
        'anomaly_management': None,
        'method': 'POST'
    },
    {
        'name': 'wb_messages',
        'handler_check': wb_message_check,
        'status_checker': created_status_check,
        'anomaly_management': None,
        'method': 'POST'
    },
    {
        'name': 'uploaded_files',
        'handler_check': file_upload_check,
        'status_checker': created_status_check,
        'anomaly_management': None,
        'method': 'POST'
    },
    {
        'name': 'appended_files',
        'handler_check': file_append_check,
        'status_checker': created_status_check,
        'anomaly_management': None,
        'method': 'POST'
    },
    {
        'name': 'receiver_comments',
        'handler_check': rcvr_comment_check,
        'status_checker': created_status_check,
        'anomaly_management': None,
        'method': 'POST'
    },
    {
        'name': 'receiver_messages',
        'handler_check': rcvr_message_check,
        'status_checker': created_status_check,
        'anomaly_management': None,
        'method': 'POST'
    }

]


class EventTrack(TempObj):
    """
    Every event that is kept in memory, is a temporary object.
    Once a while, they disappear. The statistics just take
    account of the expiration of the events collected, once a while.

    - Anomaly check is based on those elements.
    - Real-time analysis is based on these, too.
    """

    def serialize_event(self):
        return {
            # if the [:-8] I'll strip "." + $millisecond "Z"
            'creation_date': datetime_to_ISO8601(self.creation_date)[:-8],
            'event': self.event_type,
            'id': self.event_id,
            'duration': round(self.request_time, 1),
        }

    def __init__(self, event_obj, request_time, debug=False):
        self.debug = debug
        self.creation_date = datetime_now()
        self.event_id = EventTrackQueue.event_number()
        self.event_type = event_obj['name']
        self.request_time = request_time

        if self.debug:
            log.debug("Creation of Event %s" % self.serialize_event())

        TempObj.__init__(self,
                         EventTrackQueue.queue,
                         self.event_id,
                         # seconds of validity:
                         GLSetting.anomaly_seconds_delta,
                         reactor_override)

        self.expireCallbacks.append(self.synthesis)

    def synthesis(self):
        """
        This is a callback append to the expireCallbacks, and
        just make a synthesis of the Event in the Recent
        """
        from globaleaks.handlers.admin.statistics import RecentEventsCollection

        RecentEventsCollection.update_RecentEventQ(self)

    def __repr__(self):
        return "%s" % self.serialize_event()


class EventTrackQueue(object):
    """
    This class has only a class variable, used to stock the queue of the
    event happened on the latest minutes.
    """
    queue = dict()
    event_absolute_counter = 0

    @staticmethod
    def event_number():
        EventTrackQueue.event_absolute_counter += 1
        return EventTrackQueue.event_absolute_counter

    @staticmethod
    def take_current_snapshot():
        """
        Called only by the handler /admin/activities
        """
        serialized_ret = []

        for _, event_obj in EventTrackQueue.queue.iteritems():
            serialized_ret.append(event_obj.serialize_event())

        return serialized_ret

    @staticmethod
    def reset():
        EventTrackQueue.queue = dict()
        EventTrackQueue.event_absolute_counter = 0


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
        'failed_logins': 5,
        'successful_logins': 3,
        'started_submissions': 5,
        'completed_submissions': 4,
        'uploaded_files': 11,
        'appended_files': 4,
        'wb_comments': 4,
        'wb_messages': 4,
        'receiver_comments': 3,
        'receiver_messages': 3,
        # 'homepage_access': 60,
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
            'proof_of_work': False,
        }


    @staticmethod
    def reset():
        Alarm.stress_levels = {
            'disk_space': 0,
            'disk_message': None,
            'activity': 0,
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
    def compute_activity_level():
        """
        This function is called by the scheduled task, to update the
        Alarm level.

        At the end of the execution, reset to 0 the counters,
        this is why the content are copied for the statistic
        acquiring later.
        """
        from globaleaks.handlers.admin.statistics import AnomaliesCollectionDesc

        debug_reason = ""
        Alarm.number_of_anomalies = 0

        current_event_matrix = {}

        requests_timing = []

        for _, event_obj in EventTrackQueue.queue.iteritems():
            current_event_matrix.setdefault(event_obj.event_type, 0)
            current_event_matrix[event_obj.event_type] += 1
            requests_timing.append(event_obj.request_time)

        if len(requests_timing) > 2:
            log.info("In latest %d seconds: worst RTT %f, best %f" %
                     ( GLSetting.anomaly_seconds_delta,
                       round(max(requests_timing), 2),
                       round(min(requests_timing), 2) )
                     )

        for event_name, threshold in Alarm.OUTCOMING_ANOMALY_MAP.iteritems():
            if event_name in current_event_matrix:
                if current_event_matrix[event_name] > threshold:
                    Alarm.number_of_anomalies += 1
                    debug_reason = "%s[Incoming %s: %d>%d] " % \
                                   (debug_reason, event_name,
                                    current_event_matrix[event_name], threshold)
                else:
                    pass
                    log.debug("[compute_activity_level] %s %d < %d: it's OK (Anomalies recorded so far %d)" % (
                        event_name,
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
            AnomaliesCollectionDesc.update_AnomalyQ(current_event_matrix,
                                                Alarm.stress_levels['activity'])

        if previous_activity_sl or Alarm.stress_levels['activity']:
            report_function(
                "in Activity stress level switch from %d => %d [%s]" %
                (previous_activity_sl,
                 Alarm.stress_levels['activity'],
                 debug_reason))

        # Alarm notification get the copy of the latest activities
        yield Alarm.admin_alarm_notification(current_event_matrix)

        defer.returnValue(Alarm.stress_levels['activity'] - previous_activity_sl)

    @staticmethod
    @defer.inlineCallbacks
    def admin_alarm_notification(event_matrix):
        """
        This function put a mail in queue for the Admin, if the
        Admin notification is disable or if another Anomaly has been
        raised in the last 15 minutes, email is not send.
        """
        from globaleaks.handlers.admin.notification import get_notification

        do_not_stress_admin_with_more_than_an_email_after_minutes = 15

        # ------------------------------------------------------------------
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
            "%NodeName%": _node_name,
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

        admin_email = yield get_node_admin_email()

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
        # authentication_password=GLSetting.memory_copy.notif_password,
        # from_address=GLSetting.memory_copy.notif_source_email,
        # to_address=admin_email,
        # message_file=message,
        # smtp_host=GLSetting.memory_copy.notif_server,
        # smtp_port=GLSetting.memory_copy.notif_port,
        # security=GLSetting.memory_copy.notif_security,
        # event=None)

    def report_disk_usage(self, free_workdir_bytes, workdir_space_bytes, free_ramdisk_bytes):
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

        free_disk_megabs = free_workdir_bytes / (1024 * 1024)
        free_workdir_string = bytes_to_pretty_str(free_workdir_bytes)
        free_ramdisk_string = bytes_to_pretty_str(free_ramdisk_bytes)
        avail_percentage = free_workdir_bytes / (workdir_space_bytes / 100)
        max_workdir_string = bytes_to_pretty_str(workdir_space_bytes)

        # is kept a copy because we report a change in this status (in worst or in better)
        past_condition = GLSetting.memory_copy.disk_availability

        # Note: is not an if/elif/elif/else or we've to care about ordering,
        # so we start setting the default condition:
        Alarm.stress_levels['disk_space'] = 0
        GLSetting.memory_copy.disk_availability = True

        def space_condition_check(condition, info_msg, stress_level, accept_submissions):

            if condition:

                if stress_level == 3:
                    info_msg = "Fatal - Submission disabled | %s" % info_msg
                elif stress_level == 2:
                    info_msg = "Critical - Submission can be disabled soon | %s" % info_msg
                else:  # == 1
                    info_msg = "Warning | %s" % info_msg

                log.info(info_msg)
                Alarm.stress_levels['disk_space'] = stress_level
                Alarm.stress_levels['disk_message'] = info_msg
                GLSetting.memory_copy.disk_availability = accept_submissions

            return condition

        # is used a list starting from the worst case scenarios, when is meet
        # a condition, the others are skipped.
        conditions = [
            {
                # If percentage is <= 1%: disable the submission
                'condition': avail_percentage <= 1,
                'info_msg': "Disk space < 1%%: %s on %s" %
                            (max_workdir_string, free_workdir_string),
                'stress_level': 3,
                'accept_submissions': False,
            },
            {
                # If disk has less than the hardcoded minimum amount (1Gb)
                'condition': free_disk_megabs <= GLSetting.defaults.minimum_megabytes_required,
                'info_msg': "Minimum space available of %d Mb reached: (%s on %s)" %
                            (GLSetting.defaults.minimum_megabytes_required,
                             max_workdir_string,
                             free_workdir_string),
                'stress_level': 3,
                'accept_submissions': False,
            },
            {
                # If ramdisk has less than 2kbytes
                'condition': free_ramdisk_bytes <= 2048,
                'info_msg': "Ramdisk space not enough space (%s): required 2K" %
                            free_ramdisk_string,
                'stress_level': 3,
                'accept_submissions': False,
            },
            {
                # If percentage is 2% start to alert the admin on the upcoming critical situation
                'condition': avail_percentage == 2,
                'info_msg': "Disk space ~ 2%% (Critical when reach 1%%): %s on %s" %
                            (max_workdir_string, free_workdir_string),
                'stress_level': 2,
                'accept_submissions': True,
            },
            {
                # Again to avoid bad surprise, we alert the admin at (minimum disk required * 2)
                'condition': free_disk_megabs <= (GLSetting.defaults.minimum_megabytes_required * 2),
                'info_msg': "Minimum space available of %d Mb is near: (%s on %s)" %
                            (GLSetting.defaults.minimum_megabytes_required,
                             max_workdir_string,
                             free_workdir_string),
                'stress_level': 2,
                'accept_submissions': True,
            },
            {
                # if 5 times maximum file can be accepted
                'condition': free_disk_megabs <= (Alarm._HIGH_DISK_ALARM * GLSetting.memory_copy.maximum_filesize),
                'info_msg': "Disk space permit maximum of %d uploads (%s on %s)" %
                            (Alarm._HIGH_DISK_ALARM, max_workdir_string, free_workdir_string),
                'stress_level': 2,
                'accept_submissions': True,
            },
            {
                # if 15 times maximum file size can be accepted
                'condition': free_disk_megabs <= (Alarm._MEDIUM_DISK_ALARM * GLSetting.memory_copy.maximum_filesize),
                'info_msg': "Disk space permit maximum of %d uploads (%s on %s)" %
                            (Alarm._MEDIUM_DISK_ALARM, max_workdir_string, free_workdir_string),
                'stress_level': 1,
                'accept_submissions': True,
            },
        ]

        for c in conditions:
            if space_condition_check(c['condition'], c['info_msg'],
                                     c['stress_level'], c['accept_submissions']):
                break

        if past_condition != GLSetting.memory_copy.disk_availability:
            # import here to avoid circular import error
            from globaleaks.handlers.base import GLApiCache

            log.info("Switching disk space availability from: %s to %s" % (
                "True" if past_condition else "False",
                "False" if past_condition else "True"))

            # is an hack of the GLApiCache, but I can't manage a DB access here
            GLApiCache.memory_cache_dict['node']['disk_availability'] = \
                GLSetting.memory_copy.disk_availability


# a simple utility required when something has to send an email to the Admin
@transact_ro
def get_node_admin_email(store):
    node = store.find(models.Node).one()
    return unicode(node.email)
