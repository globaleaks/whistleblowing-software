# -*- encoding: utf-8 -*-
#
# In here we shall keep track of all variables and objects that should be
# instantiated only once and be common to pieces of GLBackend code.

import operator

__version__ = '2.50.8'
DATABASE_VERSION = 9

# Add here by hand the languages supported!
# copy paste format from 'grunt makeTranslations'
LANGUAGES_SUPPORTED = [
 { "code": "en", "name": "English" },
 { "code": "bg", "name": "Bulgarian" },
 { "code": "ar", "name": "Arabic" },
 { "code": "cs", "name": "Czech" },
 { "code": "nl", "name": "Dutch" },
 { "code": "de", "name": "German" },
 { "code": "hu_HU", "name": "Hungarian (Hungary)" },
 { "code": "fr", "name": "French" },
 { "code": "pt_BR", "name": "Portuguese (Brazil)" },
 { "code": "sr_RS@latin", "name": "Serbian (Latin) (Serbia)" },
 { "code": "it", "name": "Italian" },
 { "code": "ru", "name": "Russian" },
 { "code": "sr_RS", "name": "Serbian (Serbia)" },
 { "code": "vi", "name": "Vietnamese" },
 { "code": "es", "name": "Spanish" },
]

# Sorting the list of dict using the key 'code'
LANGUAGES_SUPPORTED.sort(key=operator.itemgetter('code'))

# Creating LANGUAGES_SUPPORTED_CODES form the ordered LANGUAGES_SUPPORTED
LANGUAGES_SUPPORTED_CODES = [i['code'] for i in LANGUAGES_SUPPORTED]
