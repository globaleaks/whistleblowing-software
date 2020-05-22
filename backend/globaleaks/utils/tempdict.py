# -*- coding: utf-8 -*-
from collections import OrderedDict

from twisted.internet import reactor

class TempDict(OrderedDict):
    expireCallback = None
    reactor = reactor

    def __init__(self, timeout=None):
        self.timeout = timeout
        OrderedDict.__init__(self)

    def get_timeout(self):
        return self.timeout

    def set(self, key, item):
        timeout = self.get_timeout()
        item.expireCall = self.reactor.callLater(timeout, self._expire, key)
        self[key] = item

    def get(self, key):
        if key not in self:
            return

        if self[key].expireCall is not None:
            self[key].expireCall.reset(self.get_timeout())

        return self[key]

    def delete(self, key):
        if key not in self:
            return

        item = self.pop(key)
        item.expireCall.cancel()  # pylint: disable=no-member
        self._expire(key)

    def _expire(self, key):
        if key not in self:
            return

        if self.expireCallback is not None:
            self.expireCallback(self[key])  #pylint: disable=now-callable

        del self[key]
