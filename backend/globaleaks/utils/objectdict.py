# -*- coding: utf-8 -*-


class ObjectDict(dict):
    """Makes a dictionary behave like an object."""
    def __getattr__(self, name):
        try:
            return self.__getitem__(name)
        except KeyError:
            return None

    def __setattr__(self, name, value):
        self[name] = value
