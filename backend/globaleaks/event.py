# -*- coding: utf-8

from globaleaks.state import State
from globaleaks.utils.utility import datetime_now, datetime_to_ISO8601


def failure_status_check(http_code):
    return http_code >= 400


def success_status_check(HTTP_code):
    return HTTP_code == 200


def created_status_check(http_code):
    return http_code == 201


def updated_status_check(http_code):
    return http_code == 202


def login_check(uri):
    return uri == b'/authentication'


def submission_check(uri):
    return uri.startswith(b'/submission') and (len(uri) == 11 or len(uri) == 54)


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
        'status_check': success_status_check
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
