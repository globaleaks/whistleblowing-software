"""
    GLBackend
    *********

    :copyright: (c) 2012 by GlobaLeaks
    :license: see LICENSE for more details
"""
__all__ = [ 'core', 'rest', 'modules', 'utils']


class DummyHandler:
    handler = None
    def __getattr__(self, name, *arg, **kw):
        def dummy_func(*arg, **kw):
            return {'arg': arg, 'kw': kw}
        return dummy_func
