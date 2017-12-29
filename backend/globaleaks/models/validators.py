# -*- coding: utf-8
#
# validator
# *********
#
# Utilities to validate data recorded in the ORM
import re

from globaleaks import LANGUAGES_SUPPORTED_CODES
from globaleaks.rest import errors
from globaleaks.state import State


def natnum_v(self, attr, value):
    """
    Validates that the passed value is a natural number (in Z+)
    """
    if not isinstance(value, int) or value < 0:
        raise errors.InvalidModelInput("natnum_v: expected val to be in Z+ (%s:%d)" % (attr, value))
    return value


class range_v(object):
    def __call__(self, model_obj, attr, value):
        if not isinstance(value, int):
            raise errors.InvalidModelInput("range_v: expected int (%s)" % attr)
        if value < self.start or value > self.stop:
            m = "range_v(%d, %d): value outside of acceptable range (%d)" % (self.start, self.stop, value)
            raise errors.InvalidModelInput(m)

        return value

    def __init__(self, start, stop):
        self.start = start
        self.stop = stop


def shorttext_v(self, attr, value):
    if isinstance(value, str):
        value = unicode(value)

    if not isinstance(value, unicode):
        raise errors.InvalidModelInput("shorttext_v: expected unicode (%s:%s)" % (attr, value))

    if State.settings.enable_input_length_checks and len(value) > State.settings.maximum_namesize:
        raise errors.InvalidModelInput("shorttext_v: length need to be < of %d"
                                        % State.settings.maximum_namesize)

    return value


def longtext_v(self, attr, value):
    if not attr:
        return value

    if isinstance(value, str):
        value = unicode(value)

    if not isinstance(value, unicode):
        raise errors.InvalidModelInput("longtext_v: expected unicode (%s:%s)" %
                                       (attr, value))

    if State.settings.enable_input_length_checks and len(value) > State.settings.maximum_textsize:
        raise errors.InvalidModelInput("longtext_v: unicode text in %s " \
                                        "overcomes length " \
                                        "limit %d" % (attr, State.settings.maximum_textsize))

    return value


def dict_v(self, attr, value):
    if not value:
        return {}

    if not isinstance(value, dict):
        raise errors.InvalidModelInput("dict_v: expected dict (%s)" % attr)

    for key, subvalue in value.items():
        if isinstance(subvalue, str):
            subvalue = unicode(subvalue)

        if isinstance(subvalue, unicode):
            if State.settings.enable_input_length_checks and len(subvalue) > State.settings.maximum_textsize:
                raise errors.InvalidModelInput("dict_v: text for key %s in %s " \
                                                "overcomes length limit of %d" % (key, attr,
                                                                                  State.settings.maximum_textsize))

        if isinstance(subvalue, dict):
            dict_v(self, attr, subvalue)

    # If a language does not exist, it does not mean that a malicious input have been provided,
    # this condition in fact may happen when a language is removed from the package and
    # so the proper way to handle it so is simply to log the issue and discard the input.
    # https://github.com/globaleaks/GlobaLeaks/issues/879
    remove = [lang for lang in value if lang not in LANGUAGES_SUPPORTED_CODES]
    for k in remove:
        del value[k]

    return value


def shortlocal_v(self, attr, value):
    value = dict_v(self, attr, value)

    if not value:
        return value

    for _, text in value.items():
        shorttext_v(None, attr, text)

    return value


def longlocal_v(self, attr, value):
    value = dict_v(self, attr, value)

    if not value:
        return value

    for _, text in value.items():
        longtext_v(None, attr, text)

    return value


def shorturl_v(self, attr, value):
    if not re.match(r'^(/s/[a-z0-9_-]{1,30})$', value):
        raise errors.InvalidModelInput("invalid shorturl")

    return value


def longurl_v(self, attr, value):
    if not re.match(r'^(/[a-z0-9#=_&?/-]{1,255})$', value):
        raise errors.InvalidModelInput("invalid longurl")

    return value
