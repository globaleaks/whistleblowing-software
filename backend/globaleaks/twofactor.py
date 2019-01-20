# -*- coding: utf-8 -*-
from globaleaks.utils.crypto import generate2FA
from globaleaks.utils.tempdict import TempDict

class TwoFactorToken(object):
    def __init__(self, user_id):
        self.id = user_id
        self.token = generate2FA()
        self.expireCall = None


class TwoFactorTokensFactory(TempDict):
    """Extends TempDict to provide session management functions ontop of temp session keys"""
    def revoke(self, user_id):
        try:
            del self[user_id]
        except:
            pass

    def new(self, user_id):
        token = TwoFactorToken(user_id)
        self.revoke(user_id)
        self.set(token.id, token)
        return token


TwoFactorTokens = TwoFactorTokensFactory(timeout=5 * 60) # 5 minutes
