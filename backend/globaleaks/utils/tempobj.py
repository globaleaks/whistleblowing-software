#-*- coding: utf-8 -*-

from twisted.internet import reactor
from twisted.python import components

class TempObj(components.Componentized):
    """
    A temporary object.

    inspired by twisted.web.server.Session

    @ivar timeout: timeout of the object, in seconds.
    @ivar _reactor: An object providing L{IReactorTime} to use for scheduling
        expiration.
    """

    _reactor = reactor
    _expireCall = None

    def __init__(self, parent, id, timeout, reactor=None):
        """
        Initialize the temporary object with its expiring timeout.
        """
        components.Componentized.__init__(self)

        if reactor is not None:
            self._reactor = reactor

        self.parent = parent
        self.id = id

        self.parent[id] = self

        self.timeout = timeout

        self.expireCallbacks = []

        self._expireCall = self._reactor.callLater(
            self.timeout, self.expire)

        self.lastModified = self._reactor.seconds()

    def getTime(self):
        return self._expireCall.getTime()

    def expire(self):
        """
        Expire of the object.
        """

        try:
            del self.parent[self.id]
        except KeyError:
            pass

        for c in self.expireCallbacks:
            c()

        self.expireCallbacks = []
        if self._expireCall:
            if self._expireCall.active():
              self._expireCall.cancel()

            # Break reference cycle.
            self._expireCall = None


    def touch(self):
        """
        Notify object modification (keepalive).
        """
        self.lastModified = self._reactor.seconds()
        if self._expireCall is not None:
            self._expireCall.reset(self.timeout)


    def notifyOnExpire(self, callback):
        """
        Call this callback when the session expires or logs out.
        """
        self.expireCallbacks.append(callback)
