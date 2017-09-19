# -*- coding: utf-8 -*-
import datetime
from storm.locals import DateTime as _DateTime
from storm.properties import Property
from storm.properties import PropertyPublisherMeta
from storm.variables import DateTimeVariable as _DateTimeVariable

__all__ = ['MetaModel']


class MetaModel(PropertyPublisherMeta):
    """
    Metaclass that initialize properties necessary to storm and models
    """
    def __init__(self, name, bases, attrs):
        if not hasattr(self, '__storm_table__'):
            self.__storm_table__ = self.__name__.lower()
        elif self.__storm_table__ is None:
            del self.__storm_table__

        properties = set([key for key, val in attrs.items() if isinstance(val, Property)])

        for base in bases:
            properties |= getattr(base, 'properties', set())

        self.properties = properties

        super(MetaModel, self).__init__(name, bases, attrs)


def iso_strp_time(s):
    return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f")


def iso_strf_time(d):
    return d.strftime("%Y-%m-%d %H:%M:%S.%f")


class DateTimeVariable(_DateTimeVariable):
    """
    Extend storm variable for datetime objects to parse string-formatted dates.
    """
    def parse_set(self, value, from_db):
        if not from_db and isinstance(value, (str, unicode)):
            value = iso_strp_time(value)
        return super(DateTimeVariable, self).parse_set(value, from_db)


class DateTime(_DateTime):
    """
    Re-define storm's property datetime to use our parser.
    """
    variable_class = DateTimeVariable
