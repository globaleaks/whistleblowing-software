# -*- coding: utf-8
# Implement a proof of work token to prevent resources exhaustion
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

    def serialize(self):
        return {
            'id': self.id,
            'creation_date': self.creation_date,
            'complexity': 4
        }


class TokenList(TempDict):
    def new(self, tid, session=None):
        token = Token(self, tid)

        if session is not None:
            token.session = session

        self[token.id] = token

        return token

    def get(self, key):
        ret = TempDict.get(self, key)
        if ret is None:
            raise errors.InternalServerError("TokenFailure: Invalid token")

        return ret

    def validate(self, token_answer):
        try:
            key, answer = token_answer.split(b":")
            token = self.pop(key.decode())

            if datetime_now() > token.creation_date + timedelta(seconds=self.timeout):
                raise errors.InternalServerError("TokenFailure: Token is expired")

            if not sha256(key + answer).endswith(b'0000'):
                raise errors.InternalServerError("TokenFailure: Token is not solved")
        except errors.InternalServerError:
            raise
        except:
            raise errors.InternalServerError("TokenFailure: Invalid token")

        return token
