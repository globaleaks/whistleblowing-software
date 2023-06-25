# -*- coding: utf-8 -*-
from globaleaks.settings import Settings
from globaleaks.utils.crypto import generateRandomKey
from globaleaks.utils.tempdict import TempDict
from globaleaks.utils.utility import datetime_now, uuid4


class Session(object):
    def __init__(self, tid, user_id, user_tid, user_role, cc='', ek=''):
        self.id = generateRandomKey()
        self.tid = tid
        self.user_id = user_id
        self.user_tid = user_tid
        self.user_role = user_role
        self.properties = {}
        self.permissions = {}
        self.cc = cc
        self.ek = ek
        self.ratelimit_time = datetime_now()
        self.ratelimit_count = 0
        self.files = []
        self.expireCall = None

    def getTime(self):
        return self.expireCall.getTime() if self.expireCall else 0

    def has_permission(self, permission):
        return self.permissions.get(permission, False)

    def serialize(self):
        return {
            'id': self.id,
            'role': self.user_role,
            'encryption': self.cc == '',
            'user_id': self.user_id,
            'session_expiration': self.getTime(),
            'properties': self.properties,
            'permissions': self.permissions
        }


class SessionsFactory(TempDict):
    """Extends TempDict to provide session management functions ontop of temp session keys"""

    def revoke(self, tid, user_id):
        for k, v in list(self.items()):
            if v.tid == tid and v.user_id == user_id:
                del self[k]

    def new(self, tid, user_id, user_tid, user_role, cc='', ek=''):
        self.revoke(tid, user_id)
        session = Session(tid, user_id, user_tid, user_role, cc, ek)
        self[session.id] = session
        return session

    def regenerate(self, session_id):
        session = self.pop(session_id)
        session.id = generateRandomKey()
        self[session.id] = session
        return session


Sessions = SessionsFactory(timeout=Settings.authentication_lifetime)


def initialize_submission_session(tid):
    return Sessions.new(tid, uuid4(), tid, 'whistleblower')
