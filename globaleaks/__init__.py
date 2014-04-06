# -*- encoding: utf-8 -*-
#
# In here we shall keep track of all variables and objects that should be
# instantiated only once and be common to pieces of GLBackend code.

import operator

__version__ = '2.54.16'
DATABASE_VERSION = 11

# Add here by hand the languages supported!
# copy paste format from 'grunt makeTranslations'
LANGUAGES_SUPPORTED = [
 { "code": "bg", "name": "Bulgarian" },
 { "code": "hr_HR", "name": "Croatian (Croatia)" },
 { "code": "ar", "name": "Arabic" },
 { "code": "en_US", "name": "English (United States)" },
 { "code": "en", "name": "English" },
 { "code": "cs", "name": "Czech" },
 { "code": "fr", "name": "French" },
 { "code": "de", "name": "German" },
 { "code": "nl", "name": "Dutch" },
 { "code": "pt_BR", "name": "Portuguese (Brazil)" },
 { "code": "hu_HU", "name": "Hungarian (Hungary)" },
 { "code": "pt_PT", "name": "Portuguese (Portugal)" },
 { "code": "ru", "name": "Russian" },
 { "code": "sv", "name": "Swedish" },
 { "code": "sk", "name": "Slovak" },
 { "code": "sr_RS", "name": "Serbian (Serbia)" },
 { "code": "vi", "name": "Vietnamese" },
 { "code": "it", "name": "Italian" },
 { "code": "es", "name": "Spanish" },
 { "code": "sr_RS@latin", "name": "Serbian (Latin) (Serbia)" },
]

# Sorting the list of dict using the key 'code'
LANGUAGES_SUPPORTED.sort(key=operator.itemgetter('code'))

# Creating LANGUAGES_SUPPORTED_CODES form the ordered LANGUAGES_SUPPORTED
LANGUAGES_SUPPORTED_CODES = [i['code'] for i in LANGUAGES_SUPPORTED]
