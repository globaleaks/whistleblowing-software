# -*- encoding: utf-8 -*-
#
# In here we shall keep track of all variables and objects that should be
# instantiated only once and be common to pieces of GLBackend code.

__version__ = '2.27.23'
DATABASE_VERSION = 6

# Add here by hand the languages supported!
# copy paste format from 'grunt makeTranslations'
LANGUAGES_SUPPORTED = [
                    { "code": "cs", "name": "Czech" },
                    { "code": "de", "name": "German" },
                    { "code": "en", "name": "English"},
                    { "code": "es", "name": "Spanish" },
                    { "code": "fr", "name": "French"},
                    { "code": "hu_HU", "name": "Hungarian (Hungary)"},
                    { "code": "it", "name": "Italian"},
                    { "code": "nl", "name": "Dutch"},
                    { "code": "pt_BR", "name": "Portuguese (Brazil)"},
                    { "code": "ru", "name": "Russian" },
                    { "code": "sr_RS", "name": "Serbian (Serbia)" },
                    { "code": "sr_RS@latin", "name": "Serbian (Latin) (Serbia)" },
                    { "code": "vi", "name": "Vietnamese"},
                ]

LANGUAGES_SUPPORTED_CODES = [i['code'] for i in LANGUAGES_SUPPORTED]
