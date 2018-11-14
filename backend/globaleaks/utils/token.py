# -*- coding: utf-8
# Implement a proof of work token to prevent resources exhaustion
import os
from datetime import datetime, timedelta

from globaleaks.utils.crypto import sha256, generateRandomKey, GCE
from globaleaks.utils.tempdict import TempDict
from globaleaks.utils.utility import datetime_now, datetime_to_ISO8601


class Token(object):
    min_ttl = 1
    max_ttl = 3600

    def __init__(self, tokenlist, tid, type='submission'):
        self.tokenlist = tokenlist
        self.tid = tid
        self.id = generateRandomKey(42)
        self.type = type
        self.creation_date = datetime.utcnow()

        self.uploaded_files = []

        self.solved = False
        self.question = generateRandomKey(20)

    def timedelta_check(self):
        now = datetime_now()
        start = (self.creation_date + timedelta(seconds=self.min_ttl))
        if not start < now:
            raise Exception("TokenFalure: Too early to use this token")

        end = (self.creation_date + timedelta(self.max_ttl))
        if now > end:
            raise Exception("TokenFailure: Too late to use this token")

    def validate(self, answer):
        resolved = "%s%d" % (self.question, answer)
        x = sha256(resolved.encode())
        self.solved = x.endswith(b'00')

    def update(self, answer):
        self.validate(answer)

        if not self.solved:
            return False

        if self.type == 'submission' and GCE.ENCRYPTION_AVAILABLE:
            self.tip_key = GCE.generate_key()

        return True

    def use(self):
        try:
            self.timedelta_check()
        except Exception as e:
            # Unrecoverable failures so immediately delete the token.
            self.tokenlist.delete(self.id)
            raise

        if not self.solved:
            raise Exception("TokenFailure: Token is not solved")

    def associate_file(self, fileinfo):
        self.uploaded_files.append(fileinfo)

    def serialize(self):
        return {
            'id': self.id,
            'creation_date': datetime_to_ISO8601(self.creation_date),
            'type': self.type,
            'question': self.question,
            'solved': self.solved
        }


class TokenList(TempDict):
    def __init__(self, file_path, *args, **kwds):
        self.file_path = file_path
        TempDict.__init__(self, *args, **kwds)

    def set_file_path(self, file_path):
        self.file_path = file_path

    def get_timeout(self):
        return Token.min_ttl + \
               Token.max_ttl

    def expireCallback(self, item):
        for f in item.uploaded_files:
            try:
                path = os.path.abspath(os.path.join(self.file_path, f['filename']))
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                pass

    def get(self, key):
        ret = TempDict.get(self, key)
        if ret is None:
            raise Exception('TokenFailure: Invalid token')

        return ret

    def new(self, tid, type='submission'):
        token = Token(self, tid, type)
        self.set(token.id, token)
        return token
