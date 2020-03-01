# -*- coding: utf-8
# Implement a proof of work token to prevent resources exhaustion
import os
from datetime import timedelta

from globaleaks.utils.crypto import sha256, generateRandomKey, GCE
from globaleaks.utils.tempdict import TempDict
from globaleaks.utils.utility import datetime_now, datetime_to_ISO8601


class Token(object):
    min_ttl = 1
    max_ttl = 1800

    def __init__(self, tokenlist, tid):
        self.tokenlist = tokenlist
        self.tid = tid
        self.id = generateRandomKey(42)
        self.question = generateRandomKey(20)
        self.creation_date = datetime_now()
        self.uploaded_files = []
        self.solved = False

    def update(self, answer):
        resolved = "%s%d" % (self.question, answer)
        x = sha256(resolved.encode())
        self.solved = x.endswith(b'00')

        if not self.solved:
            self.tokenlist.pop(self.id)

        if self.solved and self.tokenlist.state.tenant_cache[self.tid].encryption:
            self.tip_key = GCE.generate_key()

        return self.solved

    def associate_file(self, fileinfo):
        self.uploaded_files.append(fileinfo)

    def serialize(self):
        return {
            'id': self.id,
            'creation_date': datetime_to_ISO8601(self.creation_date),
            'question': self.question,
            'min_ttl': self.min_ttl,
            'max_ttl': self.max_ttl
        }


class TokenList(TempDict):
    def __init__(self, state, file_path, *args, **kwds):
        self.state = state
        self.file_path = file_path
        TempDict.__init__(self, *args, **kwds)

    def set_file_path(self, file_path):
        self.file_path = file_path

    def get_timeout(self):
        return Token.max_ttl

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
        self.set(token.id, token)
        return token

    def get(self, key):
        ret = TempDict.get(self, key)
        if ret is None:
            raise Exception("TokenFailure: Invalid token")

        return ret

    def use(self, key):
        token = TokenList.pop(self, key, None)
        if token is None:
            raise Exception("TokenFailure: Invalid token")

        if not token.solved:
            raise Exception("TokenFailure: Token is not solved")

        now = datetime_now()
        start = token.creation_date + timedelta(seconds=token.min_ttl)
        if now < start:
            raise Exception("TokenFalure: Too early to use this token")

        end = token.creation_date + timedelta(seconds=token.max_ttl)
        if now > end:
            raise Exception("TokenFailure: Too late to use this token")

        return token
