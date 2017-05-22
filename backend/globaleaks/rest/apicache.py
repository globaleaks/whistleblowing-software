# -*- encoding: utf-8 -*-

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
        """
        When a function has an update, all the languages need to be
        invalidated, because the change is still effective
        """
        if resource is None:
            cls.memory_cache_dict = {}
        else:
            cls.memory_cache_dict.pop(resource, None)
