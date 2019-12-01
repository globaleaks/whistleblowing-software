# -*- coding: utf-8 -*-
from collections import OrderedDict

from twisted.internet import reactor as _reactor


# needed in order to allow UT override
reactor = _reactor


class TempDict(OrderedDict):
    expireCallback = None

    def __init__(self, timeout=None):
        self.timeout = timeout
        OrderedDict.__init__(self)

    def get_timeout(self):
        """The override of this method allows dynamic limits imlementations"""
        return self.timeout

    def set(self, key, item):
        timeout = self.get_timeout()
        item.expireCall = reactor.callLater(timeout, self._expire, key)
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
            # pylint: disable=not-callable
            self.expireCallback(self[key])

        del self[key]
