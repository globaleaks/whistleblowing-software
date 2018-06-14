# -*- coding: utf-8 -*-
#
# In here we shall keep track of all variables and objects that should be
# instantiated only once and be common to pieces of GLBackend code.
import operator

__author__ = u'Random GlobaLeaks Developers'
__email__ = u'info@globaleaks.org'
__copyright__ = u'2011-2018 - Hermes Center for Transparency and Digital Human Rights - GlobaLeaks Project'
__email__ = u'info@globaleaks.org'
__version__ = u'3.1.9'
__license__ = u'AGPL-3.0'

DATABASE_VERSION = 41
FIRST_DATABASE_VERSION_SUPPORTED = 24

# Add new languages as they are supported here! To do this retrieve the name of
# the language and its code from transifex. Then use the following command to
# generate the 'native' unicode string:
#
# python -c "code='ar'; import babel; print 'native: %s' % repr(babel.Locale.parse(code).get_display_name(code));"
#
# NOTE that the cmd requires Babel is installed via pip and `code` is defined.
LANGUAGES_SUPPORTED = [
  {'code': 'ar', 'name': 'Arabic', 'native': u'\u0627\u0644\u0639\u0631\u0628\u064a\u0629'},
  {'code': 'az', 'name': 'Azerbaijani', 'native': u'az\u0259rbaycanca'},
  {'code': 'bg', 'name': 'Bulgarian', 'native': u'\u0431\u044a\u043b\u0433\u0430\u0440\u0441\u043a\u0438'},
  {'code': 'bs', 'name': 'Bosnian', 'native': u'Bosanski'},
  {'code': 'ca', 'name': 'Catalan', 'native': u'Catal\xe0'},
  {'code': 'ca@valencia', 'name': 'Valencian', 'native': u'Valenci\xe0'},
  {'code': 'cs', 'name': 'Czech', 'native': u'\u010de\u0161tina'},
  {'code': 'da', 'name': 'Danish', 'native': u'\u0627\u0644\u0639\u0631\u0628\u064a\u0629'},
  {'code': 'de', 'name': 'German', 'native': u'Deutsch'},
  {'code': 'el', 'name': 'Greek',  'native': u'\u0395\u03bb\u03bb\u03b7\u03bd\u03b9\u03ba\u03ac'},
  {'code': 'en', 'name': 'English', 'native': u'English'},
  {'code': 'es', 'name': 'Spanish', 'native': u'Espa\xf1ol'},
  {'code': 'fa', 'name': 'Persian', 'native': u'\u0641\u0627\u0631\u0633\u06cc' },
  {'code': 'fi', 'name': 'Finnish', 'native': u'Finnish'},
  {'code': 'fr', 'name': 'French', 'native': u'Fran\xe7ais'},
  {'code': 'he', 'name': 'Hebrew', 'native': u'\u05e2\u05d1\u05e8\u05d9\u05ea'},
  {'code': 'hr_HR', 'name': 'Croatian', 'native': u'Hrvatski'},
  {'code': 'hu_HU', 'name': 'Hungarian', 'native': u'Magyar'},
  {'code': 'it', 'name': 'Italian', 'native': u'Italiano'},
  {'code': 'ja', 'name': 'Japanese', 'native': u'\u65e5\u672c\u8a9e'},
  {'code': 'ka', 'name': 'Georgian', 'native': u'\u10e5\u10d0\u10e0\u10d7\u10e3\u10da\u10d8'},
  {'code': 'ko', 'name': 'Korean', 'native': u'\ud55c\uad6d\uc5b4'},
  {'code': 'nb_NO', 'name': 'Norwegian', 'native': u'Norsk bokm\xe5l'},
  {'code': 'nl', 'name': 'Dutch', 'native': u'Nederlands'},
  {'code': 'pl', 'name': 'Polish', 'native': u'polski'},
  {'code': 'pt_BR', 'name': 'Portuguese (Brazil)', 'native': u'Portugu\xeas (Brasil)'},
  {'code': 'pt_PT', 'name': 'Portuguese (Portugal)', 'native': u'Portugu\xeas (Portugal)'},
  {'code': 'ro', 'name': 'Romanian', 'native': u'Rom\xe2n\u0103'},
  {'code': 'ru', 'name': 'Russian', 'native': u'\u0440\u0443\u0441\u0441\u043a\u0438\u0439'},
  {'code': 'sl_SI', 'name': 'Slovenian', 'native': u'sloven\u0161\u010dina'},
  {'code': 'sq', 'name': 'Albanian', 'native': u'Shqip'},
  {'code': 'sv', 'name': 'Swedish', 'native': u'Svenska'},
  {'code': 'ta', 'name': 'Tamil', 'native': u'\u0ba4\u0bae\u0bbf\u0bb4\u0bcd'},
  {'code': 'th', 'name': 'Thai', 'native': u'\u0e44\u0e17\u0e22'},
  {'code': 'tr', 'name': 'Turkish', 'native': u'T\xfcrk\xe7e'},
  {'code': 'uk', 'name': 'Ukrainian', 'native': u'\u0443\u043a\u0440\u0430\u0457\u043d\u0441\u044c\u043a\u0430'},
  {'code': 'ur', 'name': 'Urdu', 'native': u'\u0627\u0631\u062f\u0648'},
  {'code': 'vi', 'name': 'Vietnamese', 'native': u'Ti\u1ebfng Vi\u1ec7t'},
  {'code': 'zh_CN', 'name': 'Chinese (China)', 'native': u'\u4e2d\u6587 (\u7b80\u4f53, \u4e2d\u56fd)'},
  {'code': 'zh_TW', 'name': 'Chinese (Taiwan)', 'native': u'\u4e2d\u6587 (\u7e41\u9ad4, \u53f0\u7063)'}
]

# Sorting the list of dict using the key 'code'
LANGUAGES_SUPPORTED.sort(key=operator.itemgetter('code'))

# Creating LANGUAGES_SUPPORTED_CODES form the ordered LANGUAGES_SUPPORTED
LANGUAGES_SUPPORTED_CODES = {i['code'] for i in LANGUAGES_SUPPORTED}

# Versioning for exported questionnaire's
QUESTIONNAIRE_EXPORT_VERSION = u'0.0.1'
