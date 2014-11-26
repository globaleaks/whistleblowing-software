# -*- coding: utf-8 -*-
#
#   anomaly
#   *******
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
from globaleaks.utils.utility import log, datetime_now, is_expired, datetime_to_ISO8601
from globaleaks.utils.tempobj import TempObj

reactor = None

# follow the checker, they are executed from handlers/base.py
# prepare() or flush()
def file_upload_check(uri):
    return uri.endswith('file')

def submission_check(uri):
    return uri.startswith('/submission/')

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

# evaluate if support regexp matching - look in Cyclone function used by Api

def failure_status_check(HTTP_code):
    # if code is missing is a failure because an Exception is raise before set
    # the status.
    return HTTP_code >= 400

def created_status_check(HTTP_code):
    # if missing, is a failure => False
    return HTTP_code == 201

def ok_status_check(HTTP_code):
    return HTTP_code == 200

def update_status_check(HTTP_code):
    return HTTP_code == 202


incoming_event_monitored = [
    #    {
    #        'name' : 'submission',
    #        'handler_check': submission_check,
    #        'anomaly_management': None,
    #        'method': 'POST'
    #    }
]

outcome_event_monitored = [
    {
        'name': 'login_failure',
        'method': 'POST',
        'handler_check': login_check,
        'status_checker': failure_status_check,
        'anomaly_management': None,
    },
    {
        'name': 'login_success',
        'method': 'POST',
        'handler_check': login_check,
        'status_checker': ok_status_check,
        'anomaly_management': None,
    },
    {
        'name': 'submission_started',
        'method': 'POST',
        'handler_check': submission_check,
        'status_checker': created_status_check,
        'anomaly_management': None,
    },
    {
        'name': 'submission_completed',
        'method': 'PUT',
        'handler_check': submission_check,
        'status_checker': update_status_check,
        'anomaly_management': None,
    },
    {
        'name': 'wb_comment',
        'handler_check' : wb_comment_check,
        'status_checker': created_status_check,
        'anomaly_management': None,
        'method': 'POST'
    },
    {
        'name': 'wb_message',
        'handler_check': wb_message_check,
        'status_checker': created_status_check,
        'anomaly_management': None,
        'method': 'POST'
    },
    {
        'name': 'file',
        'handler_check': file_upload_check,
        'status_checker': created_status_check,
        'anomaly_management': None,
        'method': 'POST'
    },
    {
        'name': 'receiver_comment',
        'handler_check': rcvr_comment_check,
        'status_checker': created_status_check,
        'anomaly_management': None,
        'method': 'POST'
    },
    {
        'name': 'receiver_message',
        'handler_check': rcvr_message_check,
        'status_checker': created_status_check,
        'anomaly_management': None,
        'method': 'POST'
    }
]

ANOMALY_WINDOW_SECONDS = 30

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
            'creation_date' : datetime_to_ISO8601(self.creation_date)[:-8],
            'event' : self.event_type,
            'id' : self.event_id,
            'duration' : self.request_time,
        }

    def __init__(self, event_obj, request_time, debug=False):

        self.debug = debug
        self.creation_date = datetime_now()
        self.event_id = EventTrackQueue.event_number()
        self.event_type = event_obj['name']
        self.request_time = request_time

        if self.debug:
            log.debug("Creation of Event %s" % self.serialize_event() )

        TempObj.__init__(self,
                         EventTrackQueue.queue,
                         self.event_id,
                         # seconds of validity:
                         ANOMALY_WINDOW_SECONDS,
                         reactor)

        self.expireCallbacks.append(self.synthesis)

    def synthesis(self):
        """
        This is a callback append to the expireCallbacks, and
        just make a synthesis of the Event in the Recent
        """
        from globaleaks.handlers.statistics import RecentEventsCollection
        RecentEventsCollection.update_RecentEventQ(self)

    def __repr__(self):
        return "%s" % self.serialize_event()


class EventTrackQueue:
    """
    This class has only a class variable, used to stock the queue of the
    event happened on the latest minutes.
    """
    queue = dict()
    event_absolute_counter = 0

    @classmethod
    def event_number(cls):
        EventTrackQueue.event_absolute_counter += 1
        return EventTrackQueue.event_absolute_counter

    @classmethod
    def take_current_snapshot(cls):
        """
        Called only by the handler /admin/activities
        """
        serialized_ret = []

        for event_id, event_obj in EventTrackQueue.queue.iteritems():
            serialized_ret.append(event_obj.serialize_event())

        return serialized_ret



class Alarm:
    """
    This class implement some classmethod used to report general
    usage of the system and the class itself return and operate
    over the stress level of the box.

    Class variables:
        @stress_levels
            Contain the ALARM [0 to 2] threshold for disk and activities.
    """

    stress_levels = {
        'disk_space' : 0,
        'activity' : 0,
    }

    # _DISK_ALARM express the number of files upload (at maximum size) that can be stored
    _MEDIUM_DISK_ALARM = 15
    _HIGH_DISK_ALARM = 5
    # is a rough indicator, every file got compression + encryption so the true disk
    # space can't be estimated correctly.

    INCOMING_ANOMALY_MAP = {
    }

    OUTCOME_ANOMALY_MAP = {
        'login_failure': 5,
        'login_success': 3,
        'submission_started': 5,
        'submission_completed': 4,
        'wb_comment': 4,
        'wb_message': 4,
        'file': 11,
        'receiver_comment': 3,
        'receiver_message': 3,
    }

    # the level of the alarm in 30 seconds
    _alarm_level = {}
    _anomaly_history = {}

    latest_measured_freespace = None

    # keep track of the last sent email
    last_alarm_email = None

    def __init__(self):
        self.current_time = datetime_now()

    def get_token_difficulty(self):
        """
        THIS FUNCTION IS NOT YET CALL

        This function return the difficulty that will be enforced in the
        token, whenever is File or Submission, here is evaluated with a dict.
        """
        self.difficulty_dict = {
            'human_captcha': False,
            'graph_captcha': False,
            'proof_of_work': False,
        }

        if Alarm.stress_levels['activity'] >= 1:
            self.difficulty_dict['graph_captcha'] = True

        if Alarm.stress_levels['disk_space'] >= 1:
            self.difficulty_dict['human_captcha'] = True

        log.debug("get_token_difficulty in %s is: HC:%s, GC:%s, PoW:%s" % (
                  self.current_time,
                  "Y" if self.difficulty_dict['human_captcha'] else "N",
                  "Y" if self.difficulty_dict['graph_captcha'] else "N",
                  "Y" if self.difficulty_dict['proof_of_work'] else "N" ) )

        return self.difficulty_dict

    @defer.inlineCallbacks
    def compute_activity_level(self, notification=True):
        """
        This function is called by the scheduled task, to update the
        Alarm level.

        At the end of the execution, reset to 0 the counters,
        this is why the content are copied for the statistic
        acquiring later.
        """
        from globaleaks.handlers.statistics import AnomaliesCollection

        debug_reason = ""
        self.number_of_anomalies = 0

        self.current_event_matrix = {}

        requests_timing = []

        for event_id, event_obj in EventTrackQueue.queue.iteritems():

            self.current_event_matrix.setdefault(event_obj.event_type, 0)
            self.current_event_matrix[event_obj.event_type] += 1
            requests_timing.append(event_obj.request_time)

        if len(requests_timing) > 2:
            log.info("worst RTt %f, best %f" %
                     (round(max(requests_timing), 2), round(min(requests_timing), 2) )
            )

        # at the moment there is just the OUTCOME_ catch
        # for event_name, threshold in Alarm.INCOMING_ANOMALY_MAP.iteritems():
        #     if self.current_event_matrix.has_key(event_name):
        #         if self.current_event_matrix[event_name] > threshold:
        #             self.number_of_anomalies += 1
        #             debug_reason = "%s[Incoming %s: %d>%d] " % \
        #                            (debug_reason, event_name,
        #                             self.current_event_matrix[event_name], threshold)

        for event_name, threshold in Alarm.OUTCOME_ANOMALY_MAP.iteritems():
            if self.current_event_matrix.has_key(event_name):
                if self.current_event_matrix[event_name] > threshold:
                    self.number_of_anomalies += 1
                    debug_reason = "%s[Incoming %s: %d>%d] " % \
                                   (debug_reason, event_name,
                                    self.current_event_matrix[event_name], threshold)


        previous_activity_sl = Alarm.stress_levels['activity']

        # Behavior: once the activity has reach a peek, the stress level
        # is raised at RED (two), and then is decremented at YELLOW (one) in the
        # next evaluation.

        if self.number_of_anomalies >= 2:
            report_function = log.msg
            Alarm.stress_levels['activity'] = 2
        elif self.number_of_anomalies == 1:
            report_function = log.info
            Alarm.stress_levels['activity'] = 1
        else:
            report_function = log.debug
            Alarm.stress_levels['activity'] = 0

        # slow downgrade, if something has triggered a two, next step to 1
        if previous_activity_sl == 2 and not Alarm.stress_levels['activity']:
            Alarm.stress_levels['activity'] = 1

        # if there are some anomaly or we're nearby, record it.
        if self.number_of_anomalies >= 1 or Alarm.stress_levels['activity'] >= 1:
            AnomaliesCollection.update_AnomalyQ(self.current_event_matrix,
                                                Alarm.stress_levels['activity'])

        if previous_activity_sl or Alarm.stress_levels['activity']:
            report_function(
                "in Activity stress level switch from %d => %d [%s]" %
                (previous_activity_sl,
                 Alarm.stress_levels['activity'],
                 debug_reason) )

        # Alarm notification get the copy of the latest activities
        if notification:
            yield self.admin_alarm_notification()

        defer.returnValue(Alarm.stress_levels['activity'] - previous_activity_sl)


    @defer.inlineCallbacks
    def admin_alarm_notification(self):
        """
        This function put a mail in queue for the Admin, if the
        configured threshold has been reached for Alarm notification.
        TODO put a GLSetting + Admin configuration variable,
        now is hardcoded to notice at >= 1
        """

        @transact_ro
        def _get_admin_email(store):
            node = store.find(models.Node).one()
            return node.email

        @transact_ro
        def _get_message_template(store):
            admin_user = store.find(models.User, models.User.username == u'admin').one()
            notif = store.find(models.Notification).one()
            template = notif.admin_anomaly_template
            if admin_user.language in template:
                return template[admin_user.language]
            elif GLSetting.memory_copy.default_language in template:
                return template[GLSetting.memory_copy.default_language]
            else:
                raise Exception("Cannot find any language for admin notification")

        def _aal():
            return "%s" % Alarm.stress_levels['activity']

        def _ad():

            retstr = ""
            for event, amount in self.current_event_matrix.iteritems():
                retstr = "%s: %d\n%s" % (event, amount, retstr)
            return retstr

        def _dal():
            return "%s" % Alarm.stress_levels['disk_space']

        def _dd():
            return "%s Megabytes" % self.latest_measured_freespace

        message_required = False
        if self.stress_levels['activity'] >= 1:
            message_required = True
        if self.stress_levels['disk_space'] >= 1:
            message_required = True

        if not message_required:
            # luckly, no mail needed
            return

        KeyWordTemplate = {
            "%ActivityAlarmLevel%" : _aal,
            "%ActivityDump%" : _ad,
            "%DiskAlarmLevel%" : _dal,
            "%DiskDump%" : _dd,
        }

        message = yield _get_message_template()
        for keyword, function in KeyWordTemplate.iteritems():
            where = message.find(keyword)
            message = "%s%s%s" % (
                message[:where],
                function(),
                message[where + len(keyword):])

        if Alarm.last_alarm_email:
            if not is_expired(Alarm.last_alarm_email, minutes=10):
                log.debug("Alert email want be send, but the threshold of 10 minutes is not yet reached since %s" %
                    datetime_to_ISO8601(Alarm.last_alarm_email))
                return

        to_address = yield _get_admin_email()
        message = MIME_mail_build(GLSetting.memory_copy.notif_source_name,
                                    GLSetting.memory_copy.notif_source_email,
                                    "Tester",
                                    to_address,
                                    "ALERT: Anomaly detection",
                                    message)

        log.debug('Alarm Email for admin: connecting to [%s:%d]' %
                    (GLSetting.memory_copy.notif_server,
                     GLSetting.memory_copy.notif_port) )

        Alarm.last_alarm_email = datetime_now()

        yield sendmail(authentication_username=GLSetting.memory_copy.notif_username,
                       authentication_password=GLSetting.memory_copy.notif_password,
                       from_address=GLSetting.memory_copy.notif_source_email,
                       to_address=[ to_address ],
                       message_file=message,
                       smtp_host=GLSetting.memory_copy.notif_server,
                       smtp_port=GLSetting.memory_copy.notif_port,
                       security=GLSetting.memory_copy.notif_security,
                       event=None)


    def report_disk_usage(self, free_mega_bytes):
        """
        Here in Alarm is written the threshold to say if we're in disk alarm
        or not. Therefore the function "report" the amount of free space and
        the evaluation + alarm shift is performed here.
        """

        # Mediam alarm threshold
        mat = Alarm._MEDIUM_DISK_ALARM * GLSetting.memory_copy.maximum_filesize
        hat = Alarm._HIGH_DISK_ALARM * GLSetting.memory_copy.maximum_filesize

        Alarm.latest_measured_freespace = free_mega_bytes

        if free_mega_bytes < hat:
            log.err("Warning: free space HIGH ALARM: only %d Mb" % free_mega_bytes)
            Alarm.stress_levels['disk_space'] = 2
        elif free_mega_bytes < mat:
            log.info("Warning: free space medium alarm: %d Mb" % free_mega_bytes)
            Alarm.stress_levels['disk_space'] = 1
        else:
            Alarm.stress_levels['disk_space'] = 0


    def get_description_status(self):
        """
        This function is useful to get some debug log
        """
        return "Alarm CPU %d, Disk %d" % (
            self.stress_levels['activity'],
            self.stress_levels['disk_space'] )



def pollute_Event_for_testing(number_of_times=1):

    for _ in xrange(number_of_times):
        for event_obj in outcome_event_monitored:

            for x in xrange(2):
                EventTrack(event_obj, 1.0 * x)
