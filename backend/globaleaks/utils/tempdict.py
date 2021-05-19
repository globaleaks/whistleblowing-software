# -*- coding: utf-8 -*-
from twisted.internet import reactor

class TempDict(dict):
    reactor = reactor

    def __init__(self, timeout=300):
        self.timeout = timeout
        dict.__init__(self)

    def __getitem__(self, key):
        value = dict.__getitem__(self, key)

        if value and value.expireCall is not None:
            try:
                value.expireCall.reset(self.timeout)
            except:
                pass

        return value

    def __setitem__(self, key, value):
        value.expireCall = self.reactor.callLater(self.timeout, self.__delitem__, key)
        return dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        value = self.pop(key, None)

        if value:
            try:
                value.expireCall.cancel()  # pylint: disable=no-member
            except:
                pass

            if hasattr(value, 'expireCallback'):
                value.expireCallback()
