# -*- coding: UTF-8
#
#   validator
#   *********
#
# Utility to validated data recorded in the ORM, these function are 
# called automatically by Storm ORM.
#
# they are five: short text validator,
#                long text validator,
#                short localized text validator,
#                long localized text validator,
#                dictionary validator

from globaleaks import LANGUAGES_SUPPORTED_CODES
from globaleaks.settings import GLSetting
from globaleaks.rest import errors
from globaleaks.utils.utility import log

def shorttext_v(_self, _attr, value):
    """
    Validator for 'name' element, receiver, context, node, and few others
        are here checked
    """
    if isinstance(value, str):
        value = unicode(value)

    if not isinstance(value, unicode):
        raise errors.InvalidInputFormat("Name expected unicode (%s)" % value)

    if len(value) > GLSetting.memory_copy.maximum_namesize:
        raise errors.InvalidInputFormat("Name length need to be < of %d"
                                        % GLSetting.memory_copy.maximum_namesize)

    return value

def longtext_v(_self, attr, value):
    """
    Validator for every generic text element stored in the DB,
    in future may check for markdown
    """
    if not attr:
        return value

    if isinstance(value, str):
        value = unicode(value)

    if not isinstance(value, unicode):
        raise errors.InvalidInputFormat("attr %s: Text expected unicode (%s)" % 
                         ( attr, value ) )

    if len(value) > GLSetting.memory_copy.maximum_textsize:
        raise errors.InvalidInputFormat("Text unicode in %s " \
					"overcome length " \
                                        "limit %d" % (attr, GLSetting.memory_copy.maximum_textsize))

    return value

def dict_v(_self, attr, value):
    """
    Validate dict content, every key, if unicode, have not to
    overcome the generic length limit.
    """
    if not value:
        return {}

    if not isinstance(value, dict):
        raise errors.InvalidInputFormat("(%s) dict expected" % attr)

    for key, subvalue in value.iteritems():
        if isinstance(subvalue, str):
            subvalue = unicode(subvalue)

        if isinstance(subvalue, unicode):
            if len(subvalue) > GLSetting.memory_copy.maximum_textsize:
                raise errors.InvalidInputFormat("In dict %s the key %s" \
                                                "overcome length limit of %d" % (attr, key,
                                                GLSetting.memory_copy.maximum_textsize))

        if isinstance(subvalue, dict):
            dict_v(_self, attr, subvalue)

    return value


def shortlocal_v(_self, attr, value):
    """
    Validate a dict containing a localized content (a dictionary having as a key
        one of the supported languages)
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
        log.debug("(%s) Invalid language code in %s, ignoring it" % (lang, attr))

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
        log.debug("(%s) Invalid language code in %s, ignoring it" % (lang, attr))

    for lang, text in value.iteritems():
        longtext_v(None, attr, text)

    return value


