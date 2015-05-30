from globaleaks.settings import GLSetting
from globaleaks.utils.tempobj import TempObj
from globaleaks.utils.utility import log, datetime_now, datetime_to_ISO8601

# needed in order to allow UT override
reactor_override = None

# follow the checker, they are executed from handlers/base.py
# by prepare() and/or flush()

def file_upload_check(uri):
    # /submission/ + token_id + /file  = 59 bytes
    return len(uri) == 59 and uri.endswith('/file')

def file_append_check(uri):
    return uri == '/wbtip/upload'

def submission_check(uri):
    # POST /submission + PUT /submission/$token_id
    return uri.startswith('/submission')

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
        'name': 'rejected_submissions',
        'method': 'PUT',
        'handler_check': submission_check,
        'status_checker': failure_status_check,
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


def update_RecentEventQ(expired_event):
    """
    Called by synthesis in anomaly.py, when an Event expire.
    This mean that we have not the event for 59:30 minutes or
    less, but only the serialisation in memory.
    This is not show anyway.
    """
    date = datetime_to_ISO8601(expired_event.creation_date)[:-8]

    GLSetting.RecentEventQ.append(
        dict({
            'id': expired_event.event_id,
            'creation_date': date,
            'event':  expired_event.event_type,
            'duration': round(expired_event.request_time, 1),
        })
    )


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
            'duration': round(self.request_time, 1)
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
        update_RecentEventQ(self)

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
