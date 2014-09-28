# -*- encoding: utf-8 -*-
#
# In here we shall keep track of all variables and objects that should be
# instantiated only once and be common to pieces of GLBackend code.

import operator

__version__ = '2.60.17'
DATABASE_VERSION = 14

# Add here by hand the languages supported!
# copy paste format from 'grunt updateTranslations'
LANGUAGES_SUPPORTED = [
 { "code": "ar", "name": "Arabic" },
 { "code": "bg", "name": "Bulgarian" },
 { "code": "ca", "name": "Catalan" },
 { "code": "cs", "name": "Czech" },
 { "code": "de", "name": "German" },
 { "code": "el", "name": "Greek" },
 { "code": "en", "name": "English" },
 { "code": "es", "name": "Spanish" },
 { "code": "fr", "name": "French" },
 { "code": "hr_HR", "name": "Croatian (Croatia)" },
 { "code": "hu_HU", "name": "Hungarian (Hungary)" },
 { "code": "it", "name": "Italian" },
 { "code": "lv", "name": "Latvian" },
 { "code": "nb_NO", "name": "Norwegian Bokmål (Norway)" },
 { "code": "nl", "name": "Dutch" },
 { "code": "pl", "name": "Polish" },
 { "code": "pt_BR", "name": "Portuguese (Brazil)" },
 { "code": "pt_PT", "name": "Portuguese (Portugal)" },
 { "code": "ru", "name": "Russian" },
 { "code": "sk", "name": "Slovak" },
 { "code": "sr_RS", "name": "Serbian (Serbia)" },
 { "code": "sr_RS@latin", "name": "Serbian (Latin) (Serbia)" },
 { "code": "sv", "name": "Swedish" },
 { "code": "th", "name": "Thai" },
 { "code": "tr", "name": "Turkish" },
 { "code": "vi", "name": "Vietnamese" },
 { "code": "zh_CN", "name": "Chinese (China)" },
]

# Sorting the list of dict using the key 'code'
LANGUAGES_SUPPORTED.sort(key=operator.itemgetter('code'))

# Creating LANGUAGES_SUPPORTED_CODES form the ordered LANGUAGES_SUPPORTED
LANGUAGES_SUPPORTED_CODES = [i['code'] for i in LANGUAGES_SUPPORTED]
