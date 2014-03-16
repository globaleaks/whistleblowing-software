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

from globaleaks.settings import GLSetting
from globaleaks.rest import errors
from globaleaks import LANGUAGES_SUPPORTED_CODES

def shorttext_v(_self, _attr, value):
    """
    Validator for 'name' element, receiver, context, node, and few others
        are here checked
    """
    if isinstance(value, str):
        value = unicode(value)

    if not isinstance(value, unicode):
        raise errors.InvalidInputFormat("Name expected unicode (%s)" % value)

    if len(value) > GLSetting.memory_copy.maximum_namesize or len(value) == 0:
        raise errors.InvalidInputFormat("Name length need to be > 0 and " \
                                        "< of %d" % GLSetting.memory_copy.maximum_namesize)

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

    for lang, text in value.iteritems():
        if lang not in LANGUAGES_SUPPORTED_CODES:
            raise errors.InvalidInputFormat("(%s) Invalid language code in %s" % (lang, attr) )

        shorttext_v(None, None, text)

    return value


def longlocal_v(_self, attr, value):

    dict_v(None, attr, value)

    if not value:
        return value

    for lang, text in value.iteritems():
        if lang not in LANGUAGES_SUPPORTED_CODES:
            raise errors.InvalidInputFormat("(%s) Invalid language code in %s" % (lang, attr) )

        longtext_v(None, attr, text)

    return value


