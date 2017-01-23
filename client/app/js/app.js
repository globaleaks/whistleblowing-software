/* eslint no-unused-vars: ["error", { "varsIgnorePattern": "GLClient" }] */

function extendExceptionHandler($delegate, $injector, $window, stacktraceService) {
    var uuid4RE = /([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})/g;
    var uuid4Empt = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx";
    // Note this RE is different from our usual email validator
    var emailRE = /(([\w+-\.]){0,100}[\w]{1,100}@([\w+-\.]){0,100}\.[\w]{1,100})/g;
    var emailEmpt = "~~~~~~@~~~~~~";

    function scrub(s) {
      var cleaner = s.replace(uuid4RE, uuid4Empt);
      cleaner = s.replace(emailRE, emailEmpt);
      return cleaner;
    }

    return function(exception, cause) {
        var $rootScope = $injector.get('$rootScope');

        if ($rootScope.exceptions_count === undefined) {
          $rootScope.exceptions_count = 0;
        }

        $rootScope.exceptions_count += 1;

        if ($rootScope.exceptions_count >= 3) {
          // Give each client the ability to forward only the first 3 exceptions
          // scattered; this is also important to avoid looping exceptions to
          // cause looping POST requests.
          return;
        }

        $delegate(exception, cause);

        stacktraceService.fromError(exception).then(function(result) {
          var errorData = angular.toJson({
            errorUrl: $window.location.href,
            errorMessage: exception.toString(),
            stackTrace: result,
            agent: navigator.userAgent
          });

          var $http = $injector.get('$http');

          $http.post('exception', scrub(errorData));
        });
    };
}

extendExceptionHandler.$inject = ['$delegate', '$injector', '$window', 'stacktraceService'];

function exceptionConfig($provide) {
    $provide.decorator('$exceptionHandler', extendExceptionHandler);
}

exceptionConfig.$inject = ['$provide'];

var GLClient = angular.module('GLClient', [
    'angular.filter',
    'ngAria',
    'ngRoute',
    'ui.bootstrap',
    'tmh.dynamicLocale',
    'flow',
    'pascalprecht.translate',
    'zxcvbn',
    'ngSanitize',
    'ngFileSaver',
    'ngFileReader',
    'GLServices',
    'GLDirectives',
    'GLFilters',
    'GLBrowserCrypto'
  ]).
  config(['$compileProvider',
          '$httpProvider',
          '$locationProvider',
          '$routeProvider',
          '$rootScopeProvider',
          '$translateProvider',
          '$uibTooltipProvider',
          'tmhDynamicLocaleProvider',
    function($compileProvider, $httpProvider, $locationProvider, $routeProvider, $rootScopeProvider, $translateProvider, $uibTooltipProvider, tmhDynamicLocaleProvider) {
    $compileProvider.debugInfoEnabled(false);
    $compileProvider.aHrefSanitizationWhitelist(/^\s*(https?|local|data):/);

    $httpProvider.interceptors.push('globaleaksRequestInterceptor');

    $locationProvider.hashPrefix("");

    function requireAuth(role) {
      return ['Access', function(Access) { return Access.isAuthenticated(role); }];
    }

    function noAuth() {
      return ['Access', function(Access) { return Access.isUnauth(); }];
    }

    function allKinds() {
      return ['Access', function(Access) { return Access.OK; }];
    }

    $routeProvider.
      when('/wizard', {
        templateUrl: 'views/wizard/main.html',
        controller: 'WizardCtrl',
        header_title: 'Platform wizard',
        header_subtitle: 'Step-by-step setup',
        resolve: {
          access: allKinds(),
        }
      }).
      when('/submission', {
        templateUrl: 'views/submission/main.html',
        controller: 'SubmissionCtrl',
        header_title: '',
        header_subtitle: '',
        resolve: {
          access: noAuth(),
        }
      }).
      when('/receipt', {
        templateUrl: 'views/receipt.html',
        controller: 'ReceiptController',
        header_title: '',
        header_subtitle: '',
        resolve: {
          access: noAuth(),
        }
      }).
      when('/status/:tip_id', {
        templateUrl: 'views/receiver/tip.html',
        controller: 'TipCtrl',
        header_title: '',
        header_subtitle: '',
        resolve: {
          access: requireAuth('receiver'),
        }
      }).
      when('/status', {
        templateUrl: 'views/whistleblower/tip.html',
        controller: 'TipCtrl',
        header_title: '',
        header_subtitle: '',
        resolve: {
          access: requireAuth('whistleblower'),
        }
      }).
      when('/forcedpasswordchange', {
        templateUrl: 'views/forced_password_change.html',
        controller: 'ForcedPasswordChangeCtrl',
        header_title: 'Change your password',
        header_subtitle: '',
        resolve: {
          access: requireAuth('*'),
        }
      }).
      when('/receiver/preferences', {
        templateUrl: 'views/receiver/preferences.html',
        controller: 'PreferencesCtrl',
        header_title: 'Recipient interface',
        header_subtitle: 'Preferences',
        resolve: {
          access: requireAuth('receiver'),
        }
      }).
      when('/receiver/tips', {
        templateUrl: 'views/receiver/tips.html',
        controller: 'ReceiverTipsCtrl',
        header_title: 'Recipient interface',
        header_subtitle: 'List of submissions',
        resolve: {
          access: requireAuth('receiver'),
        }
      }).
      when('/admin/landing', {
        templateUrl: 'views/admin/landing.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'Landing page',
        resolve: {
          access: requireAuth('admin'),
        }
      }).
      when('/admin/content', {
        templateUrl: 'views/admin/content.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'General settings',
        resolve: {
          access: requireAuth('admin'),
        }
      }).
      when('/admin/contexts', {
        templateUrl: 'views/admin/contexts.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'Context configuration',
        resolve: {
          access: requireAuth('admin'),
        }
      }).
      when('/admin/questionnaires', {
        templateUrl: 'views/admin/questionnaires.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'Questionnaire configuration',
        resolve: {
          access: requireAuth('admin'),
        }
      }).
      when('/admin/users', {
        templateUrl: 'views/admin/users.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'User management',
        resolve: {
          access: requireAuth('admin'),
        }
      }).
      when('/admin/receivers', {
        templateUrl: 'views/admin/receivers.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'Recipient configuration',
        resolve: {
          access: requireAuth('admin'),
        }
      }).
      when('/admin/mail', {
        templateUrl: 'views/admin/mail.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'Notification settings',
        resolve: {
          access: requireAuth('admin'),
        }
      }).
      when('/admin/url_shortener', {
        templateUrl: 'views/admin/url_shortener.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'URL shortener',
        resolve: {
          access: requireAuth('admin'),
        }
      }).
      when('/admin/advanced_settings', {
        templateUrl: 'views/admin/advanced.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'Advanced settings',
        resolve: {
          access: requireAuth('admin'),
        }
      }).
      when('/user/preferences', {
        templateUrl: 'views/user/preferences.html',
        controller: 'PreferencesCtrl',
        header_title: 'User preferences',
        header_subtitle: '',
        resolve: {
          access: requireAuth('*'),
        }
      }).
      when('/admin/overview', {
        templateUrl: 'views/admin/overview.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'System overview',
        resolve: {
          access: requireAuth('admin'),
        }
      }).
      when('/admin', {
        templateUrl: 'views/login.html',
        controller: 'LoginCtrl',
        header_title: 'Login',
        header_subtitle: '',
        resolve: {
          access: noAuth(),
        }
      }).
      when('/custodian', {
        templateUrl: 'views/login.html',
        controller: 'LoginCtrl',
        header_title: 'Login',
        header_subtitle: '',
        resolve: {
          access: noAuth(),
        }
      }).
      when('/custodian/identityaccessrequests', {
        templateUrl: 'views/custodian/identity_access_requests.html',
        header_title: 'Custodian of the identities',
        header_subtitle: "List of access requests to whistleblowers' identities",
        resolve: {
          access: requireAuth('custodian'),
        }
      }).
      when('/login', {
        templateUrl: 'views/login.html',
        controller: 'LoginCtrl',
        header_title: 'Login',
        header_subtitle: '',
        resolve: {
          access: noAuth(),
        }
      }).
      when('/autologin', {
        templateUrl: 'views/autologin.html',
        controller: 'AutoLoginCtrl',
        header_title: 'Login',
        header_subtitle: '',
        resolve: {
          access: noAuth(),
        }
      }).
      when('/', {
        templateUrl: 'views/home.html',
        controller: 'HomeCtrl',
        header_title: '',
        header_subtitle: '',
        resolve: {
          access: noAuth(),
        }
      }).
      otherwise({
        redirectTo: '/'
      });

      $uibTooltipProvider.options({appendToBody: true});

      // Raise the default digest loop limit to 30 because of the template recursion used by fields:
      // https://github.com/angular/angular.js/issues/6440
      $rootScopeProvider.digestTtl(30);

      // Configure translation and language providers.
      $translateProvider.useStaticFilesLoader({
        prefix: 'l10n/',
        suffix: ''
      });

      $translateProvider.useSanitizeValueStrategy('escape');

      tmhDynamicLocaleProvider.localeLocationPattern('{{base64Locales[locale]}}');
      tmhDynamicLocaleProvider.addLocalePatternValue('base64Locales',
        {
         "ar": 'js/locale/angular-locale_ar.js',
         "bs": 'js/locale/angular-locale_bs.js',
         "de": 'js/locale/angular-locale_de.js',
         "el": 'js/locale/angular-locale_el.js',
         "en": 'js/locale/angular-locale_en.js',
         "es": 'js/locale/angular-locale_es.js',
         "fa": 'js/locale/angular-locale_fa.js',
         "fr": 'js/locale/angular-locale_fr.js',
         "he": 'js/locale/angular-locale_he.js',
         "hr-hr": 'js/locale/angular-locale_hr-hr.js',
         "hr-hu": 'js/locale/angular-locale_hr-hu.js',
         "it": 'js/locale/angular-locale_it.js',
         "ja": 'js/locale/angular-locale_ja.js',
         "ka": 'js/locale/angular-locale_ka.js',
         "ko": 'js/locale/angular-locale_ko.js',
         "nb-no": 'js/locale/angular-locale_nb_no.js',
         "nl": 'js/locale/angular-locale_nl.js',
         "pt-br": 'js/locale/angular-locale_pt-br.js',
         "pt-pt": 'js/locale/angular-locale_pt-pt.js',
         "ro": 'js/locale/angular-locale_ro.js',
         "ru": 'js/locale/angular-locale_ru.js',
         "sq": 'js/locale/angular-locale_sq.js',
         "sv": 'js/locale/angular-locale_sv.js',
         "ta": 'js/locale/angular-locale_ta.js',
         "th": 'js/locale/angular-locale_th.js',
         "tr": 'js/locale/angular-locale_tr.js',
         "uk": 'js/locale/angular-locale_uk.js',
         "vi": 'js/locale/angular-locale_vi.js',
         "zn-cn": 'js/locale/angular-locale_zh-cn.js',
         "zh-tw": 'js/locale/angular-locale_zh-tw.js'
        }
      );
}]).
  config(['flowFactoryProvider', function (flowFactoryProvider) {
    flowFactoryProvider.defaults = {
        chunkSize: 1000 * 1024,
        forceChunkSize: true,
        testChunks: false,
        simultaneousUploads: 1,
        generateUniqueIdentifier: function () {
          return Math.random() * 1000000 + 1000000;
        }
    };
}]).
  run(['$q', '$rootScope', '$http', '$route', '$routeParams', '$location',  '$filter', '$translate', '$uibModal', '$timeout', '$templateCache', 'Authentication', 'PublicResource', 'Utils', 'fieldUtilities', 'GLTranslate',
      function($q, $rootScope, $http, $route, $routeParams, $location, $filter, $translate, $uibModal, $timeout, $templateCache, Authentication, PublicResource, Utils, fieldUtilities, GLTranslate) {

    $rootScope.Authentication = Authentication;
    $rootScope.GLTranslate = GLTranslate;
    $rootScope.Utils = Utils;

    $rootScope.started = false;
    $rootScope.showLoadingPanel = false;
    $rootScope.successes = [];
    $rootScope.errors = [];
    $rootScope.embedded = $location.search().embedded === 'true';

    $rootScope.closeAlert = function (list, index) {
      list.splice(index, 1);
    };

    var route_check = function () {
      if ($rootScope.node.wizard_done === false) {
        $location.path('/wizard');
      }

      if (($location.path() === '/') && ($rootScope.node.landing_page === 'submissionpage')) {
        $location.path('/submission');
      }

      if ($location.path() === '/submission' &&
          $rootScope.anonymous === false &&
          $rootScope.node.tor2web_whistleblower === false) {
        $location.path("/");
      }
    };

    var set_title = function () {
      var path = $location.path();
      var statuspage = '/status';
      if (path === '/') {
        $rootScope.ht = $rootScope.node.header_title_homepage;
      } else if (path === '/submission') {
        $rootScope.ht = $rootScope.node.header_title_submissionpage;
      } else if (path === '/receipt') {
        if (Authentication.keycode) {
          $rootScope.ht = $rootScope.node.header_title_receiptpage;
        } else {
          $rootScope.ht = $filter('translate')("Login");
        }
      } else if (path.substr(0, statuspage.length) === statuspage) {
        $rootScope.ht = $rootScope.node.header_title_tippage;
      } else {
        $rootScope.ht = $filter('translate')($rootScope.header_title);
      }
    };

    $rootScope.init = function () {
      var deferred = $q.defer();

      PublicResource.get(function(result, getResponseHeaders) {
        if (result.node.homepage) {
          $templateCache.put('custom_homepage.html', atob(result.node.homepage));
        }

        $rootScope.node = result.node;
        $rootScope.contexts = result.contexts;
        $rootScope.receivers = result.receivers;

        if (result.node.favicon) {
          document.getElementById('favicon').setAttribute("href", "data:image/x-icon;base64," + result.node.favicon);
        }

        // Tor detection and enforcing of usage of HS if users are using Tor
        if (window.location.hostname.match(/^[a-z0-9]{16}\.onion$/)) {
          // A better check on this situation would be
          // to fetch https://check.torproject.org/api/ip
          $rootScope.anonymous = true;
        } else {
          if (window.location.protocol === 'https:') {
            var headers = getResponseHeaders();
            if (headers['x-check-tor'] !== undefined && headers['x-check-tor'] === 'true') {
              $rootScope.anonymous = true;
              if ($rootScope.node.hidden_service && !Utils.iframeCheck()) {
                // the check on the iframe is in order to avoid redirects
                // when the application is included inside iframes in order to not
                // mix HTTPS resources with HTTP resources.
                window.location.href = $rootScope.node.hidden_service + '/#' + $location.url();
              }
            } else {
              $rootScope.anonymous = false;
            }
          } else {
            $rootScope.anonymous = false;
          }
        }

        GLTranslate.addNodeFacts($rootScope.node.default_language, $rootScope.node.languages_enabled);

        route_check();

        $rootScope.languages_supported = {};
        $rootScope.languages_enabled = {};
        $rootScope.languages_enabled_selector = [];
        angular.forEach($rootScope.node.languages_supported, function (lang) {
          var code = lang.code;
          var name = lang.native;
          $rootScope.languages_supported[code] = name;
          if ($rootScope.node.languages_enabled.indexOf(code) !== -1) {
            $rootScope.languages_enabled[code] = name;
            $rootScope.languages_enabled_selector.push({"name": name, "code": code});
          }
        });

        $rootScope.languages_enabled_selector = $filter('orderBy')($rootScope.languages_enabled_selector, 'code');

        $rootScope.languages_enabled_length = Object.keys($rootScope.node.languages_enabled).length;

        $rootScope.show_language_selector = ($rootScope.languages_enabled_length > 1);

        set_title();

        if ($rootScope.node.enable_experimental_features) {
          $rootScope.isStepTriggered = fieldUtilities.isStepTriggered;
          $rootScope.isFieldTriggered = fieldUtilities.isFieldTriggered;
        } else {
          $rootScope.isStepTriggered = $rootScope.dumb_function;
          $rootScope.isFieldTriggered = $rootScope.dumb_function;
        }

        $rootScope.started = true;
        deferred.resolve();
      });

      return deferred.promise;
    };

    //////////////////////////////////////////////////////////////////

    $rootScope.$watch('GLTranslate.indirect.appLanguage', function() {
      GLTranslate.setLang();
      $rootScope.reload();
    });

    $rootScope.$on("$routeChangeStart", function() {
      if ($rootScope.node) {
        route_check();
      }

      var path = $location.path();
      var embedded = '/embedded/';

      if ($location.path().substr(0, embedded.length) === embedded) {
        $rootScope.embedded = true;
        var search = $location.search();
        if (Object.keys(search).length === 0) {
          $location.path(path.replace("/embedded/", "/"));
          $location.search("embedded=true");
        } else {
          $location.url($location.url().replace("/embedded/", "/") + "&embedded=true");
        }
      }
    });

    $rootScope.$on('$routeChangeError', function(event, current, previous) {
      if (angular.isDefined(previous)) {
        $location.path(previous.$$route.originalPath);
      } else {
        $rootScope.Authentication.loginRedirect(false);
      }
    });

    $rootScope.$on('$routeChangeSuccess', function (event, current) {
      if (current.$$route) {
        $rootScope.successes = [];
        $rootScope.errors = [];
        $rootScope.header_title = current.$$route.header_title;
        $rootScope.header_subtitle = current.$$route.header_subtitle;

        if ($rootScope.node) {
          set_title();
        }
      }
    });

    $rootScope.$on("REFRESH", function() {
      $rootScope.reload();
    });

    $rootScope.$watch(function () {
      return Authentication.session;
    }, function () {
      $rootScope.session = Authentication.session;
    });

    $rootScope.keypress = function(e) {
       if (((e.which || e.keyCode) === 116) || /* F5 */
           ((e.which || e.keyCode) === 82 && (e.ctrlKey || e.metaKey))) {  /* (ctrl or meta) + r */
         e.preventDefault();
         $rootScope.$emit("REFRESH");
       }
    };

    $rootScope.init();

    $rootScope.reload = function(new_path) {
      $rootScope.started = false;
      $rootScope.successes = [];
      $rootScope.errors = [];
      $rootScope.init().then(function() {
        $route.reload();

        if (new_path) {
          $location.path(new_path).replace();
        }
      });
    };
}]).
  factory("stacktraceService", function() {
    return({
      fromError: StackTrace.fromError
    });
}).
  factory('globaleaksRequestInterceptor', ['$injector', function($injector) {
    return {
     'request': function(config) {
       var $rootScope = $injector.get('$rootScope');
       var Authentication = $injector.get('Authentication');

       $rootScope.showLoadingPanel = true;

       angular.extend(config.headers, Authentication.get_headers());

       return config;
     },
     'response': function(response) {
       var $http = $injector.get('$http');
       var $rootScope = $injector.get('$rootScope');

       if ($http.pendingRequests.length <= 1) {
          $rootScope.showLoadingPanel = false;
       }

       return response;
     },
     'responseError': function(response) {
       /*
          When the response has failed write the rootScope
          errors array the error message.
       */

       var $http = $injector.get('$http');
       var $rootScope = $injector.get('$rootScope');
       var $q = $injector.get('$q');
       var $window = $injector.get('$window');
       var Authentication = $injector.get('Authentication');

       if ($http.pendingRequests.length <= 1) {
          $rootScope.showLoadingPanel = false;
       }

       if (response.status === 405) {
         var errorData = angular.toJson({
             errorUrl: $window.location.href,
             errorMessage: response.statusText,
             stackTrace: [{
               'url': response.config.url,
               'method': response.config.method
             }],
             agent: navigator.userAgent
           });
          $http.post('exception', errorData);
       }

       if (response.data !== null) {
         var error = {
           'message': response.data.error_message,
           'code': response.data.error_code,
           'arguments': response.data.arguments
         };

         /* 30: Not Authenticated */
         if (error.code === 30) {
           Authentication.loginRedirect(false);
         }

         $rootScope.errors.push(error);
       }

       return $q.reject(response);
     }
   };
}]).
  config(exceptionConfig);
