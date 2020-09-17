# -*- coding: utf-8
# Implement a proof of work token to prevent resources exhaustion
import os
from datetime import timedelta

from globaleaks.rest import errors
from globaleaks.utils.crypto import sha256, generateRandomKey
from globaleaks.utils.tempdict import TempDict
from globaleaks.utils.utility import datetime_now


class Token(object):
    ttl = 1800

    def __init__(self, tokenlist, tid):
        self.tokenlist = tokenlist
        self.tid = tid
        self.id = generateRandomKey()
        self.creation_date = datetime_now()
        self.uploaded_files = []
        self.solved = False

    def update(self, answer):
        resolved = "%s%d" % (self.id, answer)
        x = sha256(resolved.encode())
        self.solved = x.endswith(b'00')

        if not self.solved:
            self.tokenlist.pop(self.id)

        return self.solved

    def associate_file(self, fileinfo):
        self.uploaded_files.append(fileinfo)

    def serialize(self):
        return {
            'id': self.id,
            'creation_date': self.creation_date,
            'ttl': self.ttl
        }


class TokenList(TempDict):
    def __init__(self, state, file_path):
        self.timeout = Token.ttl
        self.state = state
        self.file_path = file_path
        TempDict.__init__(self, self.timeout)

    def set_file_path(self, file_path):
        self.file_path = file_path

    def expireCallback(self, item):
        for f in item.uploaded_files:
            try:
                path = os.path.abspath(os.path.join(self.file_path, f['filename']))
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass

    def new(self, tid):
        token = Token(self, tid)
        self[token.id] = token
        return token

    def get(self, key):
        ret = TempDict.get(self, key)
        if ret is None:
            raise errors.InternalServerError("TokenFailure: Invalid token")

        return ret

    def use(self, key):
        token = TokenList.pop(self, key, None)
        if token is None:
            raise errors.InternalServerError("TokenFailure: Invalid token")

        if not token.solved:
            raise errors.InternalServerError("TokenFailure: Token is not solved")

        end = token.creation_date + timedelta(seconds=token.ttl)
        if datetime_now() > end:
            raise errors.InternalServerError("TokenFailure: Token is expired")

        return token
