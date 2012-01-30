import tornado.database

__all__ = ['Config']


def escape_query(func):
    """
    Decorator for accesses to database that require a layer of security.
    """
    def escape(key):
        if '--' in key or '\'' in key or '\"' in key:
            raise NotImplementedError
        else:
            return func(key)

class Config(object):
    db = database.Connection('localhost', 'gl.db')




