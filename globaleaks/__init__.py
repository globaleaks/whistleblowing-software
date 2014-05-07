# -*- encoding: utf-8 -*-
#
# In here we shall keep track of all variables and objects that should be
# instantiated only once and be common to pieces of GLBackend code.

import operator

__version__ = '2.60.4'
DATABASE_VERSION = 12

# Add here by hand the languages supported!
# copy paste format from 'grunt makeTranslations'
LANGUAGES_SUPPORTED = [
 { "code": "cs", "name": "Czech" },
 { "code": "ar", "name": "Arabic" },
 { "code": "en", "name": "English" },
 { "code": "bg", "name": "Bulgarian" },
 { "code": "nl", "name": "Dutch" },
 { "code": "hr_HR", "name": "Croatian (Croatia)" },
 { "code": "fr", "name": "French" },
 { "code": "it", "name": "Italian" },
 { "code": "de", "name": "German" },
 { "code": "nb_NO", "name": "Norwegian Bokmål (Norway)" },
 { "code": "pl", "name": "Polish" },
 { "code": "hu_HU", "name": "Hungarian (Hungary)" },
 { "code": "pt_BR", "name": "Portuguese (Brazil)" },
 { "code": "ru", "name": "Russian" },
 { "code": "sr_RS", "name": "Serbian (Serbia)" },
 { "code": "sr_RS@latin", "name": "Serbian (Latin) (Serbia)" },
 { "code": "sk", "name": "Slovak" },
 { "code": "vi", "name": "Vietnamese" },
 { "code": "sv", "name": "Swedish" },
 { "code": "es", "name": "Spanish" },
 { "code": "pt_PT", "name": "Portuguese (Portugal)" },
]

# Sorting the list of dict using the key 'code'
LANGUAGES_SUPPORTED.sort(key=operator.itemgetter('code'))

# Creating LANGUAGES_SUPPORTED_CODES form the ordered LANGUAGES_SUPPORTED
LANGUAGES_SUPPORTED_CODES = [i['code'] for i in LANGUAGES_SUPPORTED]
