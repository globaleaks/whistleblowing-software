# -*- coding: utf-8
# Implement a job that reset the system cache when State.reset_cache is set to True
from twisted.internet.defer import inlineCallbacks

from globaleaks.db import refresh_tenant_cache
from globaleaks.jobs.job import LoopingJob
from globaleaks.rest.cache import Cache
from globaleaks.state import State

__all__ = ['CacheReset']


class CacheReset(LoopingJob):
    interval = 5
    monitor_interval = 10

    @inlineCallbacks
    def operation(self):
        """
        This scheduler is responsible for resetting software cache
        """
        if State.reset_cache:
            Cache.invalidate(1)
            yield refresh_tenant_cache(1)
            State.reset_cache = False
