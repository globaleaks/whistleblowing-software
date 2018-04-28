# -*- coding: utf-8 -*-

class ObjectDict(dict):
    """Makes a dictionary behave like an object."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        if isinstance(value, str):
            value = value.encode('utf-8')

        self[name] = value
