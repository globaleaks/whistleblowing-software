from globaleaks.settings import GLSettings
from globaleaks.utils.tempdict import TempDict
from globaleaks.utils.utility import log, datetime_now, datetime_to_ISO8601

# follow the checker, they are executed from handlers/base.py
# by prepare() and/or flush()

def file_upload_check(uri):
    # /submission/ + token_id + /file  = 59 bytes
    return len(uri) == 59 and uri.endswith('/file')

def file_append_check(uri):
    return uri == '/wbtip/upload'

def submission_check(uri):
    # Precise len checks are needed to match only submission urls and not file ones
    # that are like /submission/0SjnzrUhuKx89hePh5Tw9eR3D18ftFZVQG6MaiK1Dy/file
    return uri.startswith('/submission') and (len(uri) == 54 or len(uri) == 11)

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


class EventTrack(object):
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

        EventTrackQueue.set(self.event_id, self)

    def __repr__(self):
        return "%s" % self.serialize_event()

    def synthesis(self):
        return {
            'id': self.event_id,
            'creation_date': datetime_to_ISO8601(self.creation_date)[:-8],
            'event':  self.event_type,
            'duration': round(self.request_time, 1),
        }


class EventTrackQueueClass(TempDict):
    """
    This class has only a class variable, used to stock the queue of the
    event happened on the latest minutes.
    """
    event_absolute_counter = 0

    def expireCallback(self, event):
        """
        On expiration of an event perform the synthesis and
        append them to the RecentEventQueue.
        """
        GLSettings.RecentEventQ.append(event.synthesis())

    def event_number(self):
        self.event_absolute_counter += 1
        return self.event_absolute_counter

    def take_current_snapshot(self):
        return [event_obj.serialize_event() for _, event_obj in EventTrackQueue.iteritems()]

    def reset(self):
        self.clear()
        self.event_absolute_counter = 0


EventTrackQueue = EventTrackQueueClass()
