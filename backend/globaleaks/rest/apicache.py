# -*- encoding: utf-8 -*-
from twisted.internet import defer


class GLApiCache(object):
    memory_cache_dict = {}

    @classmethod
    def get(cls, resource, language):
        if resource in cls.memory_cache_dict \
                and language in cls.memory_cache_dict[resource]:
            return cls.memory_cache_dict[resource][language]

    @classmethod
    def set(cls, resource, language, value):
        if resource not in GLApiCache.memory_cache_dict:
            cls.memory_cache_dict[resource] = {}

        cls.memory_cache_dict[resource][language] = value

    @classmethod
    def invalidate(cls):
        cls.memory_cache_dict.clear()


def decorator_cache_get(f):
    def decorator_cache_get_wrapper(self, *args, **kwargs):
        c = GLApiCache.get(self.request.path, self.request.language)
        if c is None:
            c = f(self, *args, **kwargs)
            if isinstance(c, defer.Deferred):
                def callback(data):
                    GLApiCache.set(self.request.path, self.request.language, data)

                    return data

                c.addCallback(callback)
            else:
                GLApiCache.set(self.request.path, self.request.language, c)

        return c

    return decorator_cache_get_wrapper


def decorator_cache_invalidate(f):
    def decorator_cache_invalidate_wrapper(self, *args, **kwargs):
        GLApiCache.invalidate()
        return f(self, *args, **kwargs)

    return decorator_cache_invalidate_wrapper
