# -*- coding: utf-8 -*-
from twisted.internet import defer


class ApiCache(object):
    memory_cache_dict = {}

    @classmethod
    def get(cls, tid, resource, language):
        if tid in cls.memory_cache_dict \
           and resource in cls.memory_cache_dict[tid] \
           and language in cls.memory_cache_dict[tid][resource]:
            return cls.memory_cache_dict[tid][resource][language]

    @classmethod
    def set(cls, tid, resource, language, value):
        if tid not in ApiCache.memory_cache_dict:
            cls.memory_cache_dict[tid] = {}

        if resource not in ApiCache.memory_cache_dict[tid]:
            cls.memory_cache_dict[tid][resource] = {}

        cls.memory_cache_dict[tid][resource][language] = value

        return value

    @classmethod
    def invalidate(cls):
        cls.memory_cache_dict.clear()


def decorator_cache_get(f):
    def decorator_cache_get_wrapper(self, *args, **kwargs):
        c = ApiCache.get(self.request.tid, self.request.path, self.request.language)
        if c is None:
            d = defer.maybeDeferred(f, self, *args, **kwargs)
            w = lambda x: ApiCache.set(self.request.tid, self.request.path, self.request.language, x)
            d.addCallback(w)
            return d

        return c

    return decorator_cache_get_wrapper


def decorator_cache_invalidate(f):
    def decorator_cache_invalidate_wrapper(self, *args, **kwargs):
        ApiCache.invalidate()
        return f(self, *args, **kwargs)

    return decorator_cache_invalidate_wrapper
