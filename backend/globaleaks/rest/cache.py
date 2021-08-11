# -*- coding: utf-8 -*-
class Cache(object):
    memory_cache_dict = {}

    @classmethod
    def get(cls, tid, resource, language):
        if tid in cls.memory_cache_dict \
           and resource in cls.memory_cache_dict[tid] \
           and language in cls.memory_cache_dict[tid][resource]:
            return cls.memory_cache_dict[tid][resource][language]

    @classmethod
    def set(cls, tid, resource, language, content_type, data):
        if tid not in Cache.memory_cache_dict:
            cls.memory_cache_dict[tid] = {}

        if resource not in Cache.memory_cache_dict[tid]:
            cls.memory_cache_dict[tid][resource] = {}

        entry = (content_type, data)

        cls.memory_cache_dict[tid][resource][language] = entry

        return entry

    @classmethod
    def invalidate(cls, tid=1):
        if tid == 1:
            cls.memory_cache_dict.clear()
        else:
            cls.memory_cache_dict.pop(tid, None)
