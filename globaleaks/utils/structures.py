# -*- coding: UTF-8
#   structures
#   **********
#
# This file contains the complex structures stored in Storm table
# in order to checks integrity between exclusive options, provide defaults,
# supports extensions (without changing DB format)

from globaleaks import LANGUAGES_SUPPORTED_CODES
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

    def debug_status(self, developer_reminder):
        # change this when you need verbose field debug
        if True:
            log.debug("%s attrs [%s] and strings [%s]" % (
                developer_reminder,
                self._localized_attrs, self._localized_strings ))

    def __init__(self):
        self._localized_strings = {}
        self._localized_attrs = {}

    def acquire_storm_object(self, storm_object):
        assert hasattr(storm_object, '__storm_table__'), \
            "acquire_localized expect only a Storm object"
        assert hasattr(storm_object, 'localized_strings'), \
            "missing localized fields"

        self._localized_attrs = getattr(storm_object, 'localized_strings')

        for attr in self._localized_attrs:
            single_dict = getattr(storm_object, attr)

            if not isinstance(single_dict, dict):
                self._localized_strings[attr] = {}
                continue

            self._localized_strings[attr] = single_dict

    def acquire_request(self, language, request, storm_class="None"):
        assert storm_class or self._localized_attrs, \
            "Invalid usage of acquire_request: specify the class or acquire_storm_object"

        if storm_class:
            self._localized_attrs = getattr(storm_class, 'localized_strings')

        for attr in self._localized_attrs:
            # InvalidInputFormat would been already been raise, this
            # assertion can't happen when the code is running
            assert request.has_key(attr), \
                "attribute %s not present in the request" % attr

            if not self._localized_strings.has_key(attr):
                self._localized_strings[attr] = {}

            self._localized_strings[attr][language] = request[attr]

    def fill_storm_object(self, storm_object):
        assert self._localized_strings, \
            "fill_storm_object can be called having localized strings"

        for attr in self._localized_attrs:
            setattr(storm_object, attr, self._localized_strings[attr])

    def get_localized_attrs(self):
        assert self._localized_attrs, \
            "get_localized_attrs can be called only after acquire_storm_object"

        return self._localized_attrs

    def get_localized_dict(self, attrname):
        """
        @param attrname: a valid key in self._localized_attrs
        @return: the dict having languages as key
        """
        if self._localized_strings.has_key(attrname):
            return self._localized_strings[attrname]
        else:
            log.debug("Empty localized dict for attr %s" % attrname)
            return {}

    def dump_translated(self, attrname, language):
        assert self._localized_strings, \
            "dump_translated can be called having localized strings"

        default_language = GLSetting.memory_copy.default_language

        if not self._localized_strings.has_key(attrname):
            return "!! Missing value for '%s'" % attrname

        translated_dict = self._localized_strings[attrname]

        if translated_dict.has_key(language):
            return translated_dict[language]
        elif translated_dict.has_key(default_language):
            return "*_Translate in '%s' [%s]" % (language, translated_dict[default_language])
        else:
            return "# Missing translation for '%s' in '%s'" % \
                   (attrname, language)

def fill_localized_keys(dictionary, model, language):
    mo = Rosetta()
    mo.acquire_request(language, dictionary, model)

    for attr in mo.get_localized_attrs():
        dictionary[attr] = mo.get_localized_dict(attr)

    return dictionary

def get_localized_values(dictionary, obj, language):
    mo = Rosetta()
    mo.acquire_storm_object(obj)

    for attr in mo.get_localized_attrs():
        dictionary[attr] = mo.dump_translated(attr, language)

    return dictionary

