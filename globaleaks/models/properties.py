from __future__ import unicode_literals

import datetime
import types

from storm.locals import Int, Pickle, Reference, ReferenceSet
from storm.locals import Unicode, Storm, JSON
from storm.properties import Property
# datetime objects are going to be extended
from storm.locals import DateTime as _DateTime
from storm.variables import DateTimeVariable as _DateTimeVariable
# Storm's metaclass is going to be extended.
from storm.properties import PropertyPublisherMeta

from globaleaks.settings import transact
from globaleaks.utils.utility import datetime_now, uuid4
from globaleaks.utils.validator import shorttext_v, longtext_v, shortlocal_v
from globaleaks.utils.validator import longlocal_v, dict_v

__all__ = ['MetaModel']


class MetaModel(PropertyPublisherMeta):
    def __init__(cls, name, bases, attrs):
        # guess public attributes, as they define the object.
        public_attrs = set([key for key, val in attrs.iteritems()
        # it is not private
                            if not key.startswith('_')
        # this is going to be dealt at metaclass level shortly. aha.
                            if not key in ('int_keys', 'bool_keys', 'unicode_keys', 'localized_strings')
        # it is not a public method, but a column
                            if isinstance(val, Property)
        ])
        for base in bases:
            public_attrs |= getattr(base, '_public_attrs', set())
        # # guess attributes types magically instead of specifying them.
        # if not hasattr(cls, 'int_keys'):
        #     cls.int_keys = [key for key in public_attrs
        #                     if isinstance(attrs[key], Int)]
        # if not hasattr(cls, 'bool_keys'):
        #     bool_keys = [key for key in public_attrs
        #                  if isinstance(attrs[key], Bool)])
        # if not hasattr(cls, 'localized_strings'):
        #     localized_strings = set([key for key in public_attrs
        #                              if isinstance(attrs[key], L10NUnicode])
        #     cls.localized_strings = list(localized_strings)
        # if not hasattr(cls, 'unicode_keys'):
        #     unicode_keys = set([key for key in public_attrs
        #                         if isinstance(attrs[key], Unicode)])
        #     cls.unicode_keys = list(unicode_keys - localized_strings)
        # if not provided, set storm_table's name to the class name.
        if not hasattr(cls, '__storm_table__'):
            cls.__storm_table__ = cls.__name__.lower()
        # if storm_table is none, this means the model is abstract and no table
        # shall be created for it.
        elif cls.__storm_table__ is None:
            del cls.__storm_table__
        # populate class attributes with the inferred new inormations.
        cls._public_attrs = public_attrs
        return super(MetaModel, cls).__init__(name, bases, attrs)

# L10NUnicode = type('L10NUnicode', (Unicode, ), {})


class DateTimeVariable(_DateTimeVariable):
    """
    Extend storm variable for datetime objects to parse string-formatted dates.
    """
    def parse_set(self, value, from_db):
        if not from_db and isinstance(value, (str, unicode)):
            value = datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
        return super(DateTimeVariable, self).parse_set(value, from_db)

class DateTime(_DateTime):
    """
    Re-define storm's property datetime to use our parser.
    """
    variable_class = DateTimeVariable
