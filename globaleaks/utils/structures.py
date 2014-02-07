# -*- coding: UTF-8
#   structures
#   **********
#
# This file contains the complex structures stored in Storm table
# in order to checks integrity between exclusive options, provide defaults,
# supports extensions (without changing DB format)

from globaleaks.utils.utility import log
from globaleaks.settings import GLSetting

class Fields:

    accepted_form_type = [ "text", "radio", "select", "multiple",
                           "checkboxes",  "textarea", "number",
                           "url", "phone", "email" ]

    def debug_status(self, developer_reminder):
        # change this when you need verbose field debug
        if False:
            log.debug("%s lang [%s] and fields #%d" % (
                developer_reminder,
                self._localization.keys(), len(self._fields.keys()) ))

    def __init__(self, localization=None, fields=None):

        self._localization = localization if localization else {}
        self._fields = fields if fields else {}
        self.debug_status('__init__')

    def context_import(self, context_storm_object):

        assert hasattr(context_storm_object, '__storm_table__'), \
            "context_import expect only a Storm object"
        assert hasattr(context_storm_object, 'localized_fields'), \
            "missing localized fields"
        assert hasattr(context_storm_object, 'unique_fields'), \
            "missing unique fields"

        self.debug_status('context_import')
        context_storm_object.localized_fields = self._localization
        context_storm_object.unique_fields = self._fields

    def update_fields(self, language, admin_data):
        """
        update_fields imply create_fields

        @param language:
        @param admin_data:

        This function shall be used in two cases:
        1) a new field has been added with the language
        2) a new language has been provided

        admin_data expect this kind of data -LOCALIZED-
        [
          {
             u'name': u'Short title',
             u'presentation_order': 1,
             u'hint': u'Describe your Tip with a short title',
             u'required': True,
             u'value': u'',
             u'key': u'b410bb94-00a7-4b9f-9499-f4fea086e4cc',
             u'preview': True,
             u'type': u'text'
          },
          {
             u'name': u'Full description',
             ...
          }
        ]
        """
        from globaleaks.rest.errors import InvalidInputFormat
        from uuid import uuid4

        self.debug_status('before update')

        # this variable collect the updated fields from the
        # admin var, in order to keep track of the real existing keys
        existing_keys = []

        for admin_order, field_desc in enumerate(admin_data):

            check_type = field_desc['type']
            if not check_type in Fields.accepted_form_type:
                raise InvalidInputFormat("Fields validation deny '%s' in %s" %
                                                (check_type, field_desc['name']) )

            if field_desc.has_key(u'key') and \
                            len(field_desc.get(u'key')) == len(unicode(uuid4())):
                key = field_desc.get(u'key')
                # print "key recognized and retrieved %s" % key
            else:
                # print "creating new key for %s" % field_desc
                key = unicode(uuid4())

            existing_keys.append(key)

            self._fields[key] = dict(field_desc)

            if not self._localization.has_key(language):
                self._localization[language] = dict()

            self._localization[language][key] = dict()

            # init localization track
            self._localization[language][key].update({'name' : field_desc['name']})
            self._localization[language][key].update({'hint' : field_desc['hint']})

            del self._fields[key]['name']
            del self._fields[key]['hint']
            del self._fields[key]['key']

        # This variable keep track of the key that has not been updated,
        # and then need to be removed.
        removed_keys = []
        for k, v in self._fields.iteritems():
            if k not in existing_keys:
                removed_keys.append(k)

        # loop over the internal dict and remove the not updated keys
        for key in removed_keys:

            for lang in self._localization:
                try:
                    del self._localization[lang][key]
                except KeyError as keyerr:
                    log.err("Handled inconsistency (field delete) lang (%s) %s" % (lang, keyerr))

            try:
                del self._fields[key]
            except KeyError as keyerr:
                log.err("Handled inconsistency (field delete): %s" % keyerr)


        self.debug_status('after update')

    def validate_fields(self, wb_fields, strict_validation):
        """
        @param wb_fields: the received wb_fields
        @param configured_fields: the Context defined wb_fields
        @return: update the object of raise an Exception if a required field
            is missing, or if received field do not match the expected shape

        strict_validation = required the presence of 'required' wb_fields.
        Is not enforced if Submission would not be finalized yet.
        """
        from globaleaks.rest.errors import SubmissionFailFields

        required_keys = list()
        optional_keys = list()

        self.debug_status('fields validation')
        try:
            for k, v in self._fields.iteritems():

                if v['required'] == True:
                    required_keys.append(k)
                else:
                    optional_keys.append(k)

        except Exception as excep:
            log.err("Internal error in processing required keys: %s" % excep)
            raise excep

        for key, value in wb_fields.iteritems():

            if not key in required_keys and not key in optional_keys:
                log.err("Submission contain an unexpected field %s" % key)
                raise SubmissionFailFields("Submitted field '%s' not expected in context" % key)

        if not strict_validation:
            return

        #log.debug("fields strict validation: %s (optional %s)" % (required_keys, optional_keys))

        for required in required_keys:

            if wb_fields.has_key(required) and len(wb_fields[required]) > 0:
            # the keys are always provided by GLClient! also if the content is empty.
            # then is not difficult check a test len(text) > $blah, but other checks are...
                continue

            log.err("Submission has a required field (%s) missing" % required)
            raise SubmissionFailFields("Missing field '%s': Required" % required)

    def dump_fields(self, language):

        default_language = GLSetting.memory_copy.default_language
        ordered_field_list = {}
        presentation_fallback = 0

        for k, v in self._fields.iteritems():

            v['key'] = k

            if self._localization.has_key(language) and self._localization[language].has_key(k):
                v['name'] = self._localization[language][k]['name']
                v['hint'] = self._localization[language][k]['hint']
            elif self._localization.has_key(default_language) and self._localization[default_language].has_key(k):
                v['name'] = u"*_Translate '%s' [%s]" % (language, self._localization[default_language][k]['name'])
                v['hint'] = u"*_Translate '%s' [%s]" % (language, self._localization[default_language][k]['hint'])
            else:
                v['name'] = u"Missing translation for lang '%s' " % language
                v['hint'] = u"Missing translation for lang '%s' " % language

            order = v['presentation_order']
            if ordered_field_list.has_key(order):
                # this shall happen only in malformed Admin Clients != from GLC
                log.err("Conflict: two fields have the same presentation order!")
                # and the old one would be lost :P
            ordered_field_list.update({ order : v })

        # convert from the keyed Dict to an ordered list
        fields_list = []
        try:
            for field_ndx in ordered_field_list.keys():
                fields_list.append(ordered_field_list[field_ndx])
        except Exception as excep:
            log.err("Unexpected problem in listing ordered fields: %s" % excep)
            for _unused, field in ordered_field_list.iteritems():
                fields_list.append(field)

        return fields_list

    def get_preview_keys(self, language):

        default_language = GLSetting.memory_copy.default_language
        key_label_dict = {}

        for k, field_desc in self._fields.iteritems():

            if field_desc['preview'] == True and field_desc['type'] == u'text':

                if self._localization.has_key(language) and self._localization[language].has_key(k):
                    key_label_dict[k] = self._localization[language][k]['name']
                elif self._localization.has_key(default_language) and self._localization[default_language].has_key(k):
                    key_label_dict[k] = u"in '%s' [%s]" % (language, self._localization[default_language][k]['name'])
                else:
                    key_label_dict[k] = u"Missing '%s' language" % language

        return key_label_dict

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
        self._localized_strings = {}

        for attr in self._localized_attrs:
            single_dict = getattr(storm_object, attr)

            if not isinstance(single_dict, dict):
                self._localized_strings[attr] = {}
                continue

            self._localized_strings[attr] = single_dict

    def acquire_request(self, language, request, storm_class=None):
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


