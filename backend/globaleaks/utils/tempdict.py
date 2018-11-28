# -*- coding: utf-8 -*-
import six
from collections import OrderedDict

from twisted.internet import reactor as _reactor


# needed in order to allow UT override
reactor = _reactor

class TempDict(OrderedDict):
    expireCallback = None

    def __init__(self, timeout=None, size_limit=None):
        self.timeout = timeout
        self.size_limit = size_limit
        OrderedDict.__init__(self)

        self._check_size_limit()

    def get_timeout(self):
        """The override of this method allows dynamic limits imlementations"""
        return self.timeout

    def get_size_limit(self):
        """The override of this method allows dynamic limits imlementations"""
        return self.size_limit

    def set(self, key, item):
        self._check_size_limit()
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
        item.expireCall.cancel() # pylint: disable=no-member
        self._expire(key)


    def _check_size_limit(self):
        size_limit = self.get_size_limit()
        if size_limit is None:
            return

        while len(self) >= size_limit:
            # retrieves the oldest key in the OD
            k = next(six.iterkeys(self))
            self.delete(k)

    def _expire(self, key):
        if key not in self:
            return

        if self.expireCallback is not None:
            # pylint: disable=not-callable
            self.expireCallback(self[key])

        del self[key]
