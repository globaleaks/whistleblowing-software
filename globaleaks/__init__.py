# -*- encoding: utf-8 -*-
#
# In here we shall keep track of all variables and objects that should be
# instantiated only once and be common to pieces of GLBackend code.

import operator

__version__ = '2.54.14'
DATABASE_VERSION = 11

# Add here by hand the languages supported!
# copy paste format from 'grunt makeTranslations'
LANGUAGES_SUPPORTED = [
 { "code": "bg", "name": "Bulgarian" },
 { "code": "ar", "name": "Arabic" },
 { "code": "de", "name": "German" },
 { "code": "en", "name": "English" },
 { "code": "cs", "name": "Czech" },
 { "code": "pt_BR", "name": "Portuguese (Brazil)" },
 { "code": "vi", "name": "Vietnamese" },
 { "code": "sr_RS@latin", "name": "Serbian (Latin) (Serbia)" },
 { "code": "es", "name": "Spanish" },
 { "code": "ru", "name": "Russian" },
 { "code": "sk", "name": "Slovak" },
 { "code": "fr", "name": "French" },
 { "code": "sr_RS", "name": "Serbian (Serbia)" },
 { "code": "hu_HU", "name": "Hungarian (Hungary)" },
 { "code": "it", "name": "Italian" },
 { "code": "nl", "name": "Dutch" },
 { "code": "en_US", "name": "English (United States)" },
]

# Sorting the list of dict using the key 'code'
LANGUAGES_SUPPORTED.sort(key=operator.itemgetter('code'))

# Creating LANGUAGES_SUPPORTED_CODES form the ordered LANGUAGES_SUPPORTED
LANGUAGES_SUPPORTED_CODES = [i['code'] for i in LANGUAGES_SUPPORTED]
