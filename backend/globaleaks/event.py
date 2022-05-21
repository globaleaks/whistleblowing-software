# -*- coding: utf-8

from globaleaks.state import State
from globaleaks.utils.utility import datetime_now


def successful_login_check(handler):
    return handler.request.uri == b'/api/authentication' and \
           handler.request.method == b'POST' and \
           handler.request.code == 201


def failed_login_check(handler):
    return handler.request.uri == b'/api/authentication' and \
           handler.request.method == b'POST' and \
           handler.request.code == 401


def completed_submission_check(handler):
    return handler.request.uri.startswith(b'/api/submission') and \
           len(handler.request.uri) == 80 and \
           handler.request.method == b'PUT' and \
           handler.request.code == 202


events_monitored = [
    {
        'name': 'failed_logins',
        'handler_check': failed_login_check
    },
    {
        'name': 'successful_logins',
        'handler_check': successful_login_check
    },
    {
        'name': 'completed_submissions',
        'handler_check': completed_submission_check
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
            'creation_date': self.creation_date,
            'duration': self.request_time
        }


def track_handler(handler):
    tid = handler.request.tid

    for event in events_monitored:
        if event['handler_check'](handler):
            e = Event(event, handler.request.execution_time)
            State.tenants[tid].RecentEventQ.append(e)
            State.tenants[tid].EventQ.append(e)
            break
