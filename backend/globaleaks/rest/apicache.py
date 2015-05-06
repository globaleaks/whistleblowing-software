from twisted.internet.defer import inlineCallbacks, returnValue

from globaleaks.utils.utility import log

class GLApiCache(object):
    memory_cache_dict = {}

    @classmethod
    @inlineCallbacks
    def get(cls, resource_name, language, function, *args, **kwargs):
        try:
            if resource_name in cls.memory_cache_dict \
                    and language in cls.memory_cache_dict[resource_name]:
                returnValue(cls.memory_cache_dict[resource_name][language])

            value = yield function(*args, **kwargs)
            if resource_name not in cls.memory_cache_dict:
                cls.memory_cache_dict[resource_name] = {}
            cls.memory_cache_dict[resource_name][language] = value
            returnValue(value)
        except KeyError:
            log.debug("KeyError exception while operating on the cache; probable race")
            returnValue(None)

    @classmethod
    def set(cls, resource_name, language, value):
        try:
            if resource_name not in GLApiCache.memory_cache_dict:
                cls.memory_cache_dict[resource_name] = {}

            cls.memory_cache_dict[resource_name][language] = value
        except KeyError:
            log.debug("KeyError exception while operating on the cache; probable race")
            returnValue(None)

    @classmethod
    def invalidate(cls, resource_name = None):
        """
        When a function has an update, all the language need to be
        invalidated, because the change is still effective
        """
        if resource_name is None:
            cls.memory_cache_dict = {}
        else:
            cls.memory_cache_dict.pop(resource_name, None)
