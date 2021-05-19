# -*- coding: utf-8
# Implement a proof of work token to prevent resources exhaustion
import os
from datetime import timedelta

from globaleaks.rest import errors
from globaleaks.utils.crypto import sha256, generateRandomKey
from globaleaks.utils.tempdict import TempDict
from globaleaks.utils.utility import datetime_now


class Token(object):
    def __init__(self, tokenlist, tid):
        self.tokenlist = tokenlist
        self.tid = tid
        self.id = generateRandomKey()
        self.session = None
        self.creation_date = datetime_now()
        self.solved = False

    def update(self, answer):
        resolved = "%s%d" % (self.id, answer)
        x = sha256(resolved.encode())
        self.solved = x.endswith(b'00')

        if not self.solved:
            self.tokenlist.pop(self.id)

        return self.solved

    def serialize(self):
        return {
            'id': self.id,
            'creation_date': self.creation_date,
            'ttl': self.tokenlist.timeout
        }


class TokenList(TempDict):
    def new(self, tid, session=None):
        token = Token(self, tid)

        if session is not None:
            token.session = session
            token.solved = True

        self[token.id] = token

        return token

    def get(self, key):
        ret = TempDict.get(self, key)
        if ret is None:
            raise errors.InternalServerError("TokenFailure: Invalid token")

        return ret

    def validate(self, key):
        token = self.pop(key)
        if token is None:
            raise errors.InternalServerError("TokenFailure: Invalid token")

        if not token.solved:
            raise errors.InternalServerError("TokenFailure: Token is not solved")

        end = token.creation_date + timedelta(seconds=self.timeout)
        if datetime_now() > end:
            raise errors.InternalServerError("TokenFailure: Token is expired")

        return token
