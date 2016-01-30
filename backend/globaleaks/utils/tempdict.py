# -*- coding: utf-8 -*-

from collections import OrderedDict

from twisted.internet import reactor


# needed in order to allow UT override
test_reactor = None


class TempDict(OrderedDict):
    reactor = None
    expireCallback = None

    def __init__(self, timeout=None, size_limit=None):
        self.timeout = timeout
        self.size_limit = size_limit
        OrderedDict.__init__(self)

        self.reactor = reactor if test_reactor is None else test_reactor

        self._check_size_limit()

    def get_timeout(self):
        """The override of this method allows dynamic limits imlementations"""
        return self.timeout

    def get_size_limit(self):
        """The override of this method allows dynamic limits imlementations"""
        return self.size_limit

    def set(self, key, value):
        timeout = self.get_timeout()
        if timeout is not None:
            value._expireCall = self.reactor.callLater(timeout, self._expire, key)
        else:
            value._expireCall = None

        self[key] = value

        self._check_size_limit()

    def get(self, key):
        if key in self:
            if self[key]._expireCall is not None:
                self[key]._expireCall.reset(self.get_timeout())

            return self[key]

        return None

    def delete(self, key):
        if key in self:
            try:
                self[key]._expireCall.stop()
            except:
                pass

            del self[key]

    def _check_size_limit(self):
        size_limit = self.get_size_limit()
        if size_limit is not None:
            while len(self) > size_limit:
                self.popitem(last=False)

    def _expire(self, key):
        if key in self:
            if self.expireCallback is not None:
                self.expireCallback(self[key])

            del self[key]
