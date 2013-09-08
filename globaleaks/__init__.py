# -*- encoding: utf-8 -*-
#
# In here we shall keep track of all variables and objects that should be
# instantiated only once and be common to pieces of GLBackend code.

__version__ = '2.25.1'
DATABASE_VERSION = 6

# Add here by hand the languages supported!
# copy paste format from 'grunt makeTranslations'
LANGUAGES_SUPPORTED = [
                    { "code": "en", "name": "English"},
                    { "code": "fr", "name": "French"},
                    { "code": "hu_HU", "name": "Hungarian (Hungary)"},
                    { "code": "it", "name": "Italian"},
                    { "code": "nl", "name": "Dutch"},
                    { "code": "pt_BR", "name": "Portuguese (Brazil)"},
                    { "code": "ru", "name": "Russian" },
                    { "code": "tr", "name": "Turkish"},
                    { "code": "vi", "name": "Vietnamese"},
                ]

LANGUAGES_SUPPORTED_CODES = [ "en", "fr", "hu_HU", "it", "nl",
                              "pt_BR", "ru", "tr", "vi" ]
