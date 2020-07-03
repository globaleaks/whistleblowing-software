# -*- coding: utf-8 -*-

from globaleaks.settings import Settings
from globaleaks.utils.crypto import generateRandomKey
from globaleaks.utils.tempdict import TempDict


class Session(object):
    def __init__(self, tid, user_id, user_tid, user_role, pcn, two_factor, cc, ek, ms=False):
        self.id = generateRandomKey()
        self.tid = tid
        self.user_id = user_id
        self.user_tid = user_tid
        self.user_role = user_role
        self.pcn = pcn
        self.two_factor = two_factor
        self.cc = cc
        self.ek = ek
        self.ms = ms
        self.expireCall = None

    def getTime(self):
        return self.expireCall.getTime() if self.expireCall else 0

    def serialize(self):
        return {
            'session_id': self.id,
            'role': self.user_role,
            'encryption': self.cc != '',
            'user_id': self.user_id,
            'user_tid': self.user_tid,
            'session_expiration': self.getTime(),
            'password_change_needed': self.pcn,
            'two_factor': self.two_factor,
            'management_session': self.ms
        }


class SessionsFactory(TempDict):
    """Extends TempDict to provide session management functions ontop of temp session keys"""

    def revoke(self, tid, user_id):
        for k, v in list(self.items()):
            if v.tid == tid and v.user_id == user_id:
                del self[k]

    def new(self, tid, user_id, user_tid, user_role, pcn, two_factor, cc, ek, ms=False):
        self.revoke(tid, user_id)
        session = Session(tid, user_id, user_tid, user_role, pcn, two_factor, cc, ek, ms)
        self.set(session.id, session)
        return session

    def regenerate(self, session_id):
        session = self.pop(session_id)
        session.id = generateRandomKey()
        self.set(session.id, session)
        return session


Sessions = SessionsFactory(timeout=Settings.authentication_lifetime)
