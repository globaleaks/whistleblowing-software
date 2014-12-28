from __future__ import unicode_literals

import datetime

from storm.properties import Property
# datetime objects are going to be extended
from storm.locals import DateTime as _DateTime
from storm.variables import DateTimeVariable as _DateTimeVariable
# Storm's metaclass is going to be extended.
from storm.properties import PropertyPublisherMeta

from globaleaks.utils.validator import shorttext_v, shortlocal_v
from globaleaks.utils.validator import dict_v

__all__ = ['MetaModel']


class MetaModel(PropertyPublisherMeta):
    """
    Globaleaks Models metaclass.
    - Take care to select public attributes (i.e. columns of the databases
      represented as class public attributes) as this apparently is not available
      in Storm;
    - Provide a default naming for database table.
    """
    def __init__(cls, name, bases, attrs):
        # guess public attributes, as they define the object.
        public_attrs = set([key for key, val in attrs.iteritems()
        # it is not private
                            if not key.startswith('_')
        # this is going to be dealt at metaclass level shortly. aha.
                            if key not in ('int_keys', 'bool_keys', 'unicode_keys', 'localized_strings')
        # it is not a public method, but a column
                            if isinstance(val, Property)
        ])
        for base in bases:
            public_attrs |= getattr(base, '_public_attrs', set()
)
        if not hasattr(cls, '__storm_table__'):
            cls.__storm_table__ = cls.__name__.lower()
        # if storm_table is none, this means the model is abstract and no table
        # shall be created for it.
        elif cls.__storm_table__ is None:
            del cls.__storm_table__

        # populate class attributes with the inferred new inormations.
        cls._public_attrs = public_attrs

        return super(MetaModel, cls).__init__(name, bases, attrs)

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
