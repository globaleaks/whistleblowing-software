# -*- encoding: utf-8 -*-
#
# In here we shall keep track of all variables and objects that should be
# instantiated only once and be common to pieces of GLBackend code.

import operator

__version__ = '2.40.0'
DATABASE_VERSION = 8

# Add here by hand the languages supported!
# copy paste format from 'grunt makeTranslations'
LANGUAGES_SUPPORTED = [
 { "code": "cs", "name": "Czech" },
 { "code": "bg", "name": "Bulgarian" },
 { "code": "ar", "name": "Arabic" },
 { "code": "en", "name": "English" },
 { "code": "fr", "name": "French" },
 { "code": "hu_HU", "name": "Hungarian (Hungary)" },
 { "code": "it", "name": "Italian" },
 { "code": "nl", "name": "Dutch" },
 { "code": "pt_BR", "name": "Portuguese (Brazil)" },
 { "code": "ru", "name": "Russian" },
 { "code": "sr_RS@latin", "name": "Serbian (Latin) (Serbia)" },
 { "code": "sr_RS", "name": "Serbian (Serbia)" },
 { "code": "es", "name": "Spanish" },
 { "code": "vi", "name": "Vietnamese" },
]

# Sorting the list of dict using the key 'code'
LANGUAGES_SUPPORTED.sort(key=operator.itemgetter('code'))

# Creating LANGUAGES_SUPPORTED_CODES form the ordered LANGUAGES_SUPPORTED
LANGUAGES_SUPPORTED_CODES = [i['code'] for i in LANGUAGES_SUPPORTED]
