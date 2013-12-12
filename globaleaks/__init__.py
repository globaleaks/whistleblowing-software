# -*- encoding: utf-8 -*-
#
# In here we shall keep track of all variables and objects that should be
# instantiated only once and be common to pieces of GLBackend code.

import operator

__version__ = '2.40'
DATABASE_VERSION = 8

# Add here by hand the languages supported!
# copy paste format from 'grunt makeTranslations'
LANGUAGES_SUPPORTED = [
 { "code": "ar", "name": "Arabic" },
 { "code": "cs", "name": "Czech" },
 { "code": "nl", "name": "Dutch" },
 { "code": "fr", "name": "French" },
 { "code": "bg", "name": "Bulgarian" },
 { "code": "en", "name": "English" },
 { "code": "hu_HU", "name": "Hungarian (Hungary)" },
 { "code": "it", "name": "Italian" },
 { "code": "de", "name": "German" },
 { "code": "sr_RS", "name": "Serbian (Serbia)" },
 { "code": "ru", "name": "Russian" },
 { "code": "es", "name": "Spanish" },
 { "code": "pt_BR", "name": "Portuguese (Brazil)" },
 { "code": "vi", "name": "Vietnamese" },
 { "code": "sr_RS@latin", "name": "Serbian (Latin) (Serbia)" },
]

# Sorting the list of dict using the key 'code'
LANGUAGES_SUPPORTED.sort(key=operator.itemgetter('code'))

# Creating LANGUAGES_SUPPORTED_CODES form the ordered LANGUAGES_SUPPORTED
LANGUAGES_SUPPORTED_CODES = [i['code'] for i in LANGUAGES_SUPPORTED]
