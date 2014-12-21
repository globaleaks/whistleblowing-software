# -*- coding: UTF-8
#   structures
#   **********
#
# This file contains the complex structures stored in Storm table
# in order to checks integrity between exclusive options, provide defaults,
# supports extensions (without changing DB format)

from globaleaks import LANGUAGES_SUPPORTED_CODES
from globaleaks.models import Model
from globaleaks.utils.utility import log
from globaleaks.settings import GLSetting

from globaleaks.rest.errors import InvalidInputFormat, SubmissionFailFields

from globaleaks.utils.utility import uuid4

# Localized strings utility management

class Rosetta:
    """
    This Class can manage all the localized strings inside
    one Storm object. AKA: manage three language on a single
    stone. Hell fucking yeah, History!
    """

    def __init__(self, attrs):
        self._localized_strings = {}
        self._localized_attrs = attrs

    def acquire_storm_object(self, obj):
        for attr in self._localized_attrs:
            self._localized_strings[attr] = getattr(obj, attr)

    def acquire_multilang_dict(self, obj):
        for attr in self._localized_attrs:
            self._localized_strings[attr] = obj[attr]

    def singlelang_to_multilang_dict(self, obj, language):
        ret = {}
        for attr in self._localized_attrs:
            ret[attr] = {}
            ret[attr][language] = obj[attr]
        return ret

    def dump_localized_attr(self, attr, language):
        default_language = GLSetting.memory_copy.default_language

        if attr not in self._localized_strings:
            return "!! Missing value for '%s'" % attr

        translated_dict = self._localized_strings[attr]

        if translated_dict.has_key(language):
            return translated_dict[language]
        elif translated_dict.has_key(default_language):
            return translated_dict[default_language]
        else:
            return ""

def fill_localized_keys(dictionary, attrs, language):
    mo = Rosetta(attrs)

    multilang_dict = mo.singlelang_to_multilang_dict(dictionary, language)

    for attr in attrs:
        dictionary[attr] = multilang_dict[attr]

    return dictionary

def get_localized_values(dictionary, obj, attrs, language):
    mo = Rosetta(attrs)

    if isinstance(obj, dict):
        mo.acquire_multilang_dict(obj)
    elif isinstance(obj, Model):
        mo.acquire_storm_object(obj)

    for attr in attrs:
        dictionary[attr] = mo.dump_localized_attr(attr, language)

    return dictionary

