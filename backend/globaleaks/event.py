# -*- coding: utf-8

from globaleaks.state import State
from globaleaks.utils.tempdict import TempDict
from globaleaks.utils.utility import datetime_now, datetime_to_ISO8601


# follow the checker, they are executed from handlers/base.py
# by prepare() and/or flush()

def file_upload_check(uri):
    # /submission/ + token_id + /file  = 59 bytes
    return (len(uri) == 59 and uri.endswith('/file')) or uri == '/wbtip/upload'


def submission_check(uri):
    # Precise len checks are needed to match only submission urls and not file ones
    # that are like /submission/0SjnzrUhuKx89hePh5Tw9eR3D18ftFZVQG6MaiK1Dy/file
    return uri.startswith('/submission') and (len(uri) == 54 or len(uri) == 11)


def login_check(uri):
    return uri == '/authentication'


def message_check(uri):
    return uri.startswith('/wbtip/messages/') or uri.startswith('/rtip/messages/')


def comment_check(uri):
    return uri == '/wbtip/comments' or uri.startswith('/rtip/comments')


def failure_status_check(http_code):
    # if code is missing is a failure because an Exception is raise before set
    # the status.
    return http_code >= 400


def ok_status_check(HTTP_code):
    return HTTP_code == 200


def created_status_check(http_code):
    return http_code == 201


def updated_status_check(http_code):
    return http_code == 202


events_monitored = [
    {
        'name': 'failed_logins',
        'handler_check': login_check,
        'method': 'POST',
        'status_check': failure_status_check,
    },
    {
        'name': 'successful_logins',
        'handler_check': login_check,
        'method': 'POST',
        'status_check': ok_status_check
    },
    {
        'name': 'started_submissions',
        'handler_check': submission_check,
        'method': 'POST',
        'status_check': created_status_check
    },
    {
        'name': 'completed_submissions',
        'handler_check': submission_check,
        'method': 'PUT',
        'status_check': updated_status_check
    },
    {
        'name': 'failed_submissions',
        'handler_check': submission_check,
        'method': 'PUT',
        'status_check': failure_status_check
    },
    {
        'name': 'comments',
        'handler_check': comment_check,
        'method': 'POST',
        'status_check': created_status_check
    },
    {
        'name': 'messages',
        'handler_check': message_check,
        'method': 'POST',
        'status_check': created_status_check
    },
    {
        'name': 'files',
        'handler_check': file_upload_check,
        'method': 'POST',
        'status_check': ok_status_check
    }
]


class Event(object):
    """
    Every event that is kept in memory, is a temporary object.
    Once a while, they disappear. The statistics just take
    account of the expiration of the events collected, once a while.

    - Anomaly check is based on those elements.
    - Real-time analysis is based on these, too.
    """
    def __init__(self, event_obj, request_time):
        self.event_type = event_obj['name']
        self.creation_date = datetime_now()
        self.request_time = round(request_time.total_seconds(), 1)

    def serialize(self):
        return {
            'event': self.event_type,
            'creation_date': datetime_to_ISO8601(self.creation_date)[:-8],
            'duration': self.request_time
        }


def track_handler(handler):
    tid = handler.request.tid

    for event in events_monitored:
        if event['handler_check'](handler.request.uri) and \
           event['method'] == handler.request.method and \
           event['status_check'](handler.request.code):
            e = Event(event, handler.request.execution_time)
            State.tenant_state[tid].RecentEventQ.append(e)
            State.tenant_state[tid].EventQ.append(e)
            break
