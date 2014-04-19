# -*- encoding: utf-8 -*-
#
# In here we shall keep track of all variables and objects that should be
# instantiated only once and be common to pieces of GLBackend code.

import operator

__version__ = '2.54.16'
DATABASE_VERSION = 12

# Add here by hand the languages supported!
# copy paste format from 'grunt makeTranslations'
LANGUAGES_SUPPORTED = [
 { "code": "bg", "name": "Bulgarian" },
 { "code": "en_US", "name": "English (United States)" },
 { "code": "hr_HR", "name": "Croatian (Croatia)" },
 { "code": "cs", "name": "Czech" },
 { "code": "de", "name": "German" },
 { "code": "hu_HU", "name": "Hungarian (Hungary)" },
 { "code": "ar", "name": "Arabic" },
 { "code": "en", "name": "English" },
 { "code": "pt_PT", "name": "Portuguese (Portugal)" },
 { "code": "sk", "name": "Slovak" },
 { "code": "sr_RS", "name": "Serbian (Serbia)" },
 { "code": "nb_NO", "name": "Norwegian Bokmål (Norway)" },
 { "code": "pt_BR", "name": "Portuguese (Brazil)" },
 { "code": "es", "name": "Spanish" },
 { "code": "ru", "name": "Russian" },
 { "code": "sr_RS@latin", "name": "Serbian (Latin) (Serbia)" },
 { "code": "it", "name": "Italian" },
 { "code": "vi", "name": "Vietnamese" },
 { "code": "fr", "name": "French" },
 { "code": "sv", "name": "Swedish" },
 { "code": "nl", "name": "Dutch" },
]

# Sorting the list of dict using the key 'code'
LANGUAGES_SUPPORTED.sort(key=operator.itemgetter('code'))

# Creating LANGUAGES_SUPPORTED_CODES form the ordered LANGUAGES_SUPPORTED
LANGUAGES_SUPPORTED_CODES = [i['code'] for i in LANGUAGES_SUPPORTED]
