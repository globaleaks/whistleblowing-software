# -*- coding: utf-8 -*-

from globaleaks.settings import Settings
from globaleaks.utils.crypto import generateRandomKey
from globaleaks.utils.tempdict import TempDict

class Session(object):
    def __init__(self, tid, user_id, user_role, pcn, cc):
        self.id = generateRandomKey(42)
        self.tid = tid
        self.user_id = user_id
        self.user_role = user_role
        self.pcn = pcn
        self.cc = cc
        self.expireCall = None

    def getTime(self):
        return self.expireCall.getTime() if self.expireCall else 0

    def serialize(self):
        return {
            'session_id': self.id,
            'role': self.user_role,
            'user_id': self.user_id,
            'session_expiration': self.getTime(),
            'password_change_needed': self.pcn
        }


class SessionsFactory(TempDict):
    """Extends TempDict to provide session management functions ontop of temp session keys"""
    def revoke(self, user_id):
        for k, v in list(self.items()):
            if v.user_id == user_id:
                del self[k]

    def new(self, tid, user_id, user_role, pcn, cc):
        session = Session(tid, user_id, user_role, pcn, cc)
        self.revoke(user_id)
        self.set(session.id, session)
        return session

    def regenerate(self, session_id):
        session = self.pop(session_id)
        session.id = generateRandomKey(42)
        self.set(session.id, session)
        return session


Sessions = SessionsFactory(timeout=Settings.authentication_lifetime)
