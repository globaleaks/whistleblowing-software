# -*- coding: UTF-8
#
# validator
# *********
#
# Utilities to validate data recorded in the ORM

from globaleaks import LANGUAGES_SUPPORTED_CODES
from globaleaks.settings import GLSettings
from globaleaks.rest import errors
from globaleaks.utils.utility import log


def shorttext_v(_self, attr, value):
    """
    """
    if isinstance(value, str):
        value = unicode(value)

    if not isinstance(value, unicode):
        raise errors.InvalidModelInput("shorttext_v: expected unicode (%s:%s)" % (attr, value))

    if len(value) > GLSettings.memory_copy.maximum_namesize:
        raise errors.InvalidModelInput("shorttext_v: length need to be < of %d"
                                        % GLSettings.memory_copy.maximum_namesize)

    return value


def longtext_v(_self, attr, value):
    """
    """
    if not attr:
        return value

    if isinstance(value, str):
        value = unicode(value)

    if not isinstance(value, unicode):
        raise errors.InvalidModelInput("longtext_v: expected unicode (%s:%s)" %
                                       (attr, value))

    if len(value) > GLSettings.memory_copy.maximum_textsize:
        raise errors.InvalidModelInput("longtext_v: unicode text in %s " \
                                        "overcomes length " \
                                        "limit %d" % (attr, GLSettings.memory_copy.maximum_textsize))

    return value


def dict_v(_self, attr, value):
    """
    """
    if not value:
        return {}

    if not isinstance(value, dict):
        raise errors.InvalidModelInput("dict_v: expected dict (%s)" % attr)

    for key, subvalue in value.iteritems():
        if isinstance(subvalue, str):
            subvalue = unicode(subvalue)

        if isinstance(subvalue, unicode):
            if len(subvalue) > GLSettings.memory_copy.maximum_textsize:
                raise errors.InvalidModelInput("dict_v: text for key %s in %s " \
                                                "overcomes length limit of %d" % (key, attr,
                                                                                  GLSettings.memory_copy.maximum_textsize))

        if isinstance(subvalue, dict):
            dict_v(_self, attr, subvalue)

    return value


def shortlocal_v(_self, attr, value):
    """
    """
    dict_v(None, attr, value)

    if not value:
        return value

    # If a language does not exist, it does not mean that a malicious input have been provided,
    # this condition in fact may happen when a language is removed from the package and 
    # so the proper way to handle it so is simply to log the issue and discard the input.
    # https://github.com/globaleaks/GlobaLeaks/issues/879
    remove = [lang for lang in value if lang not in LANGUAGES_SUPPORTED_CODES]
    for k in remove:
        try:
            del value[unicode(k)]
        except KeyError:
            pass
        log.debug("shortlocal_v: (%s) Invalid language code in %s, skipped" %
                  (k, attr))

    for lang, text in value.iteritems():
        shorttext_v(None, None, text)

    return value


def longlocal_v(_self, attr, value):
    dict_v(None, attr, value)

    if not value:
        return value

    # If a language does not exist, it does not mean that a malicious input have been provided,
    # this condition in fact may happen when a language is removed from the package and
    # so the proper way to handle it so is simply to log the issue and discard the input.
    # https://github.com/globaleaks/GlobaLeaks/issues/879
    remove = [lang for lang in value if lang not in LANGUAGES_SUPPORTED_CODES]
    for k in remove:
        try:
            del value[unicode(k)]
        except KeyError:
            pass
        log.debug("longlocal_v: (%s) Invalid language code in %s, skipped" %
                  (k, attr))

    for lang, text in value.iteritems():
        longtext_v(None, attr, text)

    return value
