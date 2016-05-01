angular.module('tmh.dynamicLocalePreload', ['tmh.dynamicLocale'])
    .config(['tmhDynamicLocaleProvider', function(tmhDynamicLocaleProvider) {
  tmhDynamicLocaleProvider.localeLocationPattern('{{base64Locales[locale]}}');
  tmhDynamicLocaleProvider.addLocalePatternValue('base64Locales',
    {
     "ar": 'components/angular-i18n/angular-locale_ar.js',
     "bs": 'components/angular-i18n/angular-locale_bs.js',
     "de": 'components/angular-i18n/angular-locale_de.js',
     "el": 'components/angular-i18n/angular-locale_el.js',
     "en": 'components/angular-i18n/angular-locale_en.js',
     "es": 'components/angular-i18n/angular-locale_es.js',
     "fa": 'components/angular-i18n/angular-locale_fa.js',
     "fr": 'components/angular-i18n/angular-locale_fr.js',
     "he": 'components/angular-i18n/angular-locale_he.js',
     "hr-hr": 'components/angular-i18n/angular-locale_hr-hr.js',
     "hr-hu": 'components/angular-i18n/angular-locale_hr-hu.js',
     "it": 'components/angular-i18n/angular-locale_it.js',
     "ja": 'components/angular-i18n/angular-locale_ja.js',
     "ka": 'components/angular-i18n/angular-locale_ka.js',
     "ko": 'components/angular-i18n/angular-locale_ko.js',
     "nb-no": 'components/angular-i18n/angular-locale_nb_no.js',
     "nl": 'components/angular-i18n/angular-locale_nl.js',
     "pt-br": 'components/angular-i18n/angular-locale_pt-br.js',
     "pt-pt": 'components/angular-i18n/angular-locale_pt-pt.js',
     "ro": 'components/angular-i18n/angular-locale_ro.js',
     "ru": 'components/angular-i18n/angular-locale_ru.js',
     "sq": 'components/angular-i18n/angular-locale_sq.js',
     "sv": 'components/angular-i18n/angular-locale_sv.js',
     "ta": 'components/angular-i18n/angular-locale_ta.js',
     "th": 'components/angular-i18n/angular-locale_th.js',
     "tr": 'components/angular-i18n/angular-locale_tr.js',
     "uk": 'components/angular-i18n/angular-locale_uk.js',
     "vi": 'components/angular-i18n/angular-locale_vi.js',
     "zn-cn": 'components/angular-i18n/angular-locale_zh-cn.js',
     "zh-tw": 'components/angular-i18n/angular-locale_zh-tw.js'
    }
  );
}]);
