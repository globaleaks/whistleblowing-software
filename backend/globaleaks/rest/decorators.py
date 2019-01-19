# -*- coding: utf-8
import json

from twisted.internet import defer

from globaleaks.rest import errors
from globaleaks.rest.cache import Cache
from globaleaks.state import State


def decorator_authentication(f, roles):
     def wrapper(self, *args, **kwargs):
         if self.state.tenant_cache[self.request.tid].basic_auth and not self.bypass_basic_auth:
             self.basic_auth()

         if '*' in roles or \
             'unauthenticated' in roles or \
             (self.current_user and self.current_user.user_role in roles):
             return f(self, *args, **kwargs)

         raise errors.NotAuthenticated

     return wrapper


def decorator_cache_get(f):
    def wrapper(self, *args, **kwargs):
        c = Cache.get(self.request.tid, self.request.path, self.request.language)
        if c is None:
            d = defer.maybeDeferred(f, self, *args, **kwargs)

            def callback(data):
                if isinstance(data, (dict, list)):
                    self.request.setHeader(b'content-type', b'application/json')
                    data = json.dumps(data)

                self.request.setHeader(b'Content-encoding', b'gzip')

                c = self.request.responseHeaders.getRawHeaders(b'Content-type', [b'application/json'])[0]
                return Cache.set(self.request.tid, self.request.path, self.request.language, c, data)[1]

            d.addCallback(callback)

            return d

        else:
            self.request.setHeader(b'Content-encoding', b'gzip')
            self.request.setHeader(b'Content-type', c[0])

        return c[1]

    return wrapper


def decorator_cache_invalidate(f):
    def wrapper(self, *args, **kwargs):
        if self.invalidate_cache:
            Cache.invalidate(self.request.tid)

        return f(self, *args, **kwargs)

    return wrapper


def decorator_refresh_connection_handpoints(f):
     def wrapper(self, *args, **kwargs):
         d = defer.maybeDeferred(f, self, *args, **kwargs)
         def callback(data):
             self.state.refresh_connection_handpoints()
             return data

         return d.addCallback(callback)

     return wrapper


def decorate_method(h, method):
    value = getattr(h, 'check_roles')
    if isinstance(value, str):
        value = {value}

    f = getattr(h, method)

    if State.settings.enable_api_cache:
        if method == 'get':
            if h.cache_resource:
                f = decorator_cache_get(f)
        else:
            if h.invalidate_cache:
                f = decorator_cache_invalidate(f)

            if h.refresh_connection_handpoints:
                f = decorator_refresh_connection_handpoints(f)

    f = decorator_authentication(f, value)

    setattr(h, method, f)
