# -*- encoding: utf-8 -*-
#
# In here we shall keep track of all variables and objects that should be
# instantiated only once and be common to pieces of GLBackend code.

__version__ = '2.23.5'
DATABASE_VERSION = 2

# Add here by hand the languages supported!
# copy paste format from 'grunt makeTranslations'
LANGUAGES_SUPPORTED = [
                    { "code": "ar", "name": "Arabic" },
                    { "code": "en", "name": "English"},
                    { "code": "nl", "name": "Dutch"},
                    { "code": "de", "name": "German"},
                    { "code": "el", "name": "Greek"},
                    { "code": "hu_HU", "name": "Hungarian (Hungary)"},
                    { "code": "it", "name": "Italian"},
                    { "code": "pl", "name": "Polish"},
                    { "code": "tr", "name": "Turkish"},
                ]

LANGUAGES_SUPPORTED_CODES = [ "ar", "en", "nl", "de",
                              "el", "hu_HU", "it",
                              "pl", "tr" ]
