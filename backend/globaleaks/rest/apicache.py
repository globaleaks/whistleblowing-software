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
    def invalidate(cls, resource=None):
        if resource is None:
            cls.memory_cache_dict = {}
        else:
            cls.memory_cache_dict.pop(resource, None)


def decorator_cache_get(f):
    def wrapper(self, *args, **kwargs):
        c = GLApiCache.get(self.request.path, 'en')
        if c is None:
            c = f(self, *args, **kwargs)
            if isinstance(c, defer.Deferred):
                def callback(data):
                    GLApiCache.set(self.request.path, 'en', data)

                    return data

                c.addCallback(callback)

        return c

    return wrapper


def decorator_cache_invalidate(f):
    def wrapper(self, *args, **kwargs):
        GLApiCache.invalidate(self.request.path)
        return f(self, *args, **kwargs)

    return wrapper
