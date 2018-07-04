/* eslint no-unused-vars: ["error", { "varsIgnorePattern": "^GLClient|\$locale$" }] */

var _flowFactoryProvider;

function extendExceptionHandler($delegate, $injector, stacktraceService) {
    var uuid4RE = /([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})/g;
    var uuid4Empt = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx";
    // Note this RE is different from our usual email validator
    var emailRE = /(([\w+-.]){0,100}[\w]{1,100}@([\w+-.]){0,100}.[\w]{1,100})/g;
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
            errorUrl: $injector.get('$location').path(),
            errorMessage: exception.toString(),
            stackTrace: result,
            agent: navigator.userAgent
          });

          $injector.get('$http').post('exception', scrub(errorData));
        });
    };
}

extendExceptionHandler.$inject = ['$delegate', '$injector', 'stacktraceService'];

function exceptionConfig($provide) {
    $provide.decorator('$exceptionHandler', extendExceptionHandler);
}

exceptionConfig.$inject = ['$provide'];

var GLClient = angular.module('GLClient', [
    'angular.filter',
    'ngAria',
    'ngRoute',
    'ui.bootstrap',
    'ui.select',
    'tmh.dynamicLocale',
    'flow',
    'pascalprecht.translate',
    'zxcvbn',
    'ngSanitize',
    'ngFileSaver',
    'GLServices',
    'GLDirectives',
    'GLFilters',
    'GLBrowserCrypto'
  ]).
  config(['$compileProvider',
          '$httpProvider',
          '$locationProvider',
          '$provide',
          '$qProvider',
          '$routeProvider',
          '$rootScopeProvider',
          '$translateProvider',
          '$uibTooltipProvider',
          'tmhDynamicLocaleProvider',
    function($compileProvider, $httpProvider, $locationProvider, $provide, $qProvider, $routeProvider, $rootScopeProvider, $translateProvider, $uibTooltipProvider, tmhDynamicLocaleProvider) {
    $compileProvider.debugInfoEnabled(false);
    $compileProvider.aHrefSanitizationWhitelist(/^\s*(https?|local|data):/);

    $qProvider.errorOnUnhandledRejections(false);

    $httpProvider.interceptors.push('globaleaksRequestInterceptor');

    $locationProvider.hashPrefix("");

    $provide.decorator('$templateRequest', ['$delegate', function($delegate) {
      // This decorator is required in order to inject the 'true' for setting ignoreRequestError
      // in relation to https://docs.angularjs.org/error/$compile/tpload
      var fn = $delegate;

      $delegate = function(tpl) {
        for (var key in fn) {
          $delegate[key] = fn[key];
        }

        return fn.apply(this, [tpl, true]);
      };

      return $delegate;
    }]);

    function requireAuth(role) {
      return ['Access', function(Access) { return Access.isAuthenticated(role); }];
    }

    function noAuth() {
      return ['Access', function(Access) { return Access.isUnauth(); }];
    }

    function allKinds() {
      return ['Access', function(Access) { return Access.OK; }];
    }

    function fetchResources(role, lst) {
      return ['$q', 'Access', 'AdminContextResource', 'AdminQuestionnaireResource', 'AdminStepResource', 'AdminFieldResource', 'AdminFieldTemplateResource', 'AdminUserResource', 'AdminReceiverResource', 'AdminNodeResource', 'AdminNotificationResource', 'AdminShorturlResource', 'AdminTenantResource', 'FieldAttrs', 'ActivitiesCollection', 'AnomaliesCollection', 'TipOverview', 'FileOverview', 'JobsOverview', 'ManifestResource', 'AdminSubmissionStatusResource', function($q, Access, AdminContextResource, AdminQuestionnaireResource, AdminStepResource, AdminFieldResource, AdminFieldTemplateResource, AdminUserResource, AdminReceiverResource, AdminNodeResource, AdminNotificationResource, AdminShorturlResource, AdminTenantResource, FieldAttrs, ActivitiesCollection, AnomaliesCollection, TipOverview, FileOverview, JobsOverview, ManifestResource, AdminSubmissionStatusResource) {
        var resourcesPromises = {
          node: function() { return AdminNodeResource.get().$promise },
          manifest: function() { return ManifestResource.get().$promise; },
          contexts: function() { return AdminContextResource.query().$promise },
          field_attrs: function() { return FieldAttrs.get().$promise },
          fieldtemplates: function() { return AdminFieldTemplateResource.query().$promise },
          users: function() { return AdminUserResource.query().$promise },
          receivers: function() { return AdminReceiverResource.query().$promise },
          notification: function() { return AdminNotificationResource.get().$promise },
          shorturls: function() { return AdminShorturlResource.query().$promise },
          tenants: function() { return AdminTenantResource.query().$promise },
          activities: function() { return ActivitiesCollection.query().$promise },
          anomalies: function() { return AnomaliesCollection.query().$promise },
          tip_overview: function() { return TipOverview.query().$promise },
          file_overview: function() { return FileOverview.query().$promise },
          jobs_overview: function() { return JobsOverview.query().$promise },
          questionnaires: function() { return AdminQuestionnaireResource.query().$promise },
          submission_statuses: function() { return AdminSubmissionStatusResource.query().$promise },
        }

        return Access.isAuthenticated(role).then(function() {
          var promises = {};

          for (var i = 0; i < lst.length; i++) {
             var name = lst[i]
             promises[name] = resourcesPromises[name]();
          }

          return $q.all(promises);
        });
      }]
    }

    $routeProvider.
      when('/wizard', {
        templateUrl: 'views/wizard/main.html',
        controller: 'WizardCtrl',
        header_title: 'Platform wizard',
        header_subtitle: '',
        resolve: {
          access: allKinds(),
        }
      }).
      when('/signup', {
        templateUrl: 'views/signup/main.html',
        controller: 'SignupCtrl',
        header_title: 'Create your whistleblowing platform',
        header_subtitle: '',
        resolve: {
          access: allKinds(),
        }
      }).
      when('/activation', {
        templateUrl: 'views/signup/activation.html',
        controller: 'SignupActivationCtrl',
        header_title: 'Create your whistleblowing platform',
        header_subtitle: '',
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
      when('/receiver/tips', {
        templateUrl: 'views/receiver/tips.html',
        controller: 'ReceiverTipsCtrl',
        header_title: 'Recipient interface',
        header_subtitle: 'List of submissions',
        resolve: {
          access: requireAuth('receiver'),
        }
      }).
      when('/admin/home', {
        templateUrl: 'views/admin/home.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: '',
        resolve: {
          resources: fetchResources('acl', ['manifest', 'node']),
        }
      }).
      when('/admin/content', {
        templateUrl: 'views/admin/content.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'General settings',
        resolve: {
          resources: fetchResources('acl', ['node']),
        }
      }).
      when('/admin/contexts', {
        templateUrl: 'views/admin/contexts.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'Contexts',
        resolve: {
          resources: fetchResources('admin', ['contexts', 'node', 'questionnaires', 'receivers']),
        }
      }).
      when('/admin/questionnaires', {
        templateUrl: 'views/admin/questionnaires.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'Questionnaires',
        resolve: {
          resources: fetchResources('admin', ['fieldtemplates', 'field_attrs', 'node', 'questionnaires']),
        }
      }).
      when('/admin/users', {
        templateUrl: 'views/admin/users/userlist.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'Users',
        resolve: {
          resources: fetchResources('admin', ['node', 'users', 'tenants']),
        }
      }).
      when('/admin/receivers', {
        templateUrl: 'views/admin/receivers.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'Recipients',
        resolve: {
          resources: fetchResources('admin', ['contexts', 'node', 'receivers']),
        }
      }).
      when('/admin/mail', {
        templateUrl: 'views/admin/mail.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'Notification settings',
        resolve: {
          resources: fetchResources('admin', ['node', 'notification']),
        }
      }).
      when('/admin/network', {
        templateUrl: 'views/admin/network.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'Network settings',
        resolve: {
          resources: fetchResources('admin', ['node']),
        }
      }).
      when('/admin/advanced_settings', {
        templateUrl: 'views/admin/advanced.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'Advanced settings',
        resolve: {
          resources: fetchResources('admin', ['node', 'shorturls']),
        }
      }).
      when('/admin/overview', {
        templateUrl: 'views/admin/overview.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'System overview',
        resolve: {
          resources: fetchResources('admin', ['node', 'activities', 'anomalies', 'file_overview', 'jobs_overview', 'tip_overview', 'users']),
        }
      }).
      when('/admin/tenants', {
        templateUrl: 'views/admin/tenants.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'Sites management',
        resolve: {
          resources: fetchResources('admin', ['node', 'tenants']),
        }
      }).
      when('/admin/case_management', {
        templateUrl: 'views/admin/case_management.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'Case management',
        resolve: {
          resources: fetchResources('admin', ['node', 'submission_statuses']),
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
      when('/preferences', {
        templateUrl: 'views/preferences.html',
        controller: 'PreferencesCtrl',
        header_title: 'Preferences',
        header_subtitle: '',
        resolve: {
          access: requireAuth('*'),
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
      when('/login/passwordreset', {
        templateUrl: 'views/passwordreset/main.html',
        controller: 'PasswordResetCtrl',
        header_title: 'Request password reset',
        header_subtitle: '',
        resolve: {
          access: noAuth()
        }
      }).
      when('/login/passwordreset/requested', {
        templateUrl: 'views/passwordreset/requested.html',
        header_title: 'Request password reset',
        header_subtitle: '',
        resolve: {
          access: noAuth()
        }
      }).
      when('/login/passwordreset/failure', {
        templateUrl: 'views/passwordreset/failure.html',
        header_title: 'Request password reset',
        header_subtitle: '',
        resolve: {
          access: noAuth()
        }
      }).
      when('/email/validation/success', {
        templateUrl: 'views/email_validation_success.html',
        controller: 'EmailValidationCtrl',
        header_title: '',
        header_subtitle: '',
        resolve: {
          access: noAuth(),
        }
      }).
      when('/email/validation/failure', {
        templateUrl: 'views/email_validation_failure.html',
        controller: 'EmailValidationCtrl',
        header_title: '',
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

      $uibTooltipProvider.options({appendToBody: true, trigger: 'mouseenter'});

      // Raise the default digest loop limit to 30 because of the template recursion used by fields:
      // https://github.com/angular/angular.js/issues/6440
      $rootScopeProvider.digestTtl(30);

      // Configure translation and language providers.
      $translateProvider.useStaticFilesLoader({
        prefix: 'l10n/',
        suffix: ''
      });

      $translateProvider.useInterpolation('noopInterpolation');
      $translateProvider.useSanitizeValueStrategy('escape');

      tmhDynamicLocaleProvider.localeLocationPattern('{{base64Locales[locale]}}');
      tmhDynamicLocaleProvider.addLocalePatternValue('base64Locales',
        {
         "ar": 'js/locale/angular-locale_ar.js',
         "az": 'js/locale/angular-locale_az.js',
         "bg": 'js/locale/angular-locale_ca.js',
         "bs": 'js/locale/angular-locale_bs.js',
         "ca": 'js/locale/angular-locale_ca.js',
         "ca@valencia": 'js/locale/angular-locale_ca-es-valencia.js',
         "cs": 'js/locale/angular-locale_cs.js',
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
         "pl": 'js/locale/angular-locale_pl.js',
         "pt-br": 'js/locale/angular-locale_pt-br.js',
         "pt-pt": 'js/locale/angular-locale_pt-pt.js',
         "ro": 'js/locale/angular-locale_ro.js',
         "ru": 'js/locale/angular-locale_ru.js',
         "sl-si": 'js/locale/angular-locale_sl.js',
         "sq": 'js/locale/angular-locale_sq.js',
         "sv": 'js/locale/angular-locale_sv.js',
         "ta": 'js/locale/angular-locale_ta.js',
         "th": 'js/locale/angular-locale_th.js',
         "tr": 'js/locale/angular-locale_tr.js',
         "uk": 'js/locale/angular-locale_uk.js',
         "ur": 'js/locale/angular-locale_ur.js',
         "vi": 'js/locale/angular-locale_vi.js',
         "zn-cn": 'js/locale/angular-locale_zh-cn.js',
         "zh-tw": 'js/locale/angular-locale_zh-tw.js'
        }
      );

}]).
  config(['flowFactoryProvider', function (flowFactoryProvider) {
    // Trick to move the flowFactoryProvider config inside run block.
    _flowFactoryProvider = flowFactoryProvider;
}]).
  run(['$rootScope', '$http', '$route', '$routeParams', '$location',  '$filter', '$translate', '$uibModal', '$timeout', '$templateCache', 'Authentication', 'PublicResource', 'Utils', 'fieldUtilities', 'GLTranslate', 'Access', 'Test',
      function($rootScope, $http, $route, $routeParams, $location, $filter, $translate, $uibModal, $timeout, $templateCache, Authentication, PublicResource, Utils, fieldUtilities, GLTranslate, Access, Test) {
    $rootScope.Authentication = Authentication;
    $rootScope.GLTranslate = GLTranslate;
    $rootScope.Utils = Utils;

    $rootScope.started = false;
    $rootScope.showLoadingPanel = false;
    $rootScope.successes = [];
    $rootScope.errors = [];
    $rootScope.embedded = $location.search().embedded === 'true';

    _flowFactoryProvider.defaults = {
        chunkSize: 1000 * 1024,
        forceChunkSize: true,
        testChunks: false,
        simultaneousUploads: 1,
        generateUniqueIdentifier: function () {
          return Math.random() * 1000000 + 1000000;
        },
        headers: function() {
          return $rootScope.Authentication.get_headers();
        }
    };

    $rootScope.closeAlert = function (list, index) {
      list.splice(index, 1);
    };

    $rootScope.open_confidentiality_modal = function () {
      $uibModal.open({
        controller: 'ModalCtrl',
        templateUrl: 'views/partials/security_awareness_confidentiality.html',
        size: 'lg',
        scope: $rootScope,
        backdrop: 'static',
        keyboard: false
      });
    };

    $rootScope.open_disclaimer_modal = function () {
      $uibModal.open({
        templateUrl: 'views/partials/disclaimer.html',
        controller: 'DisclaimerModalCtrl',
        size: 'lg',
        scope: $rootScope,
        backdrop: 'static',
        keyboard: false
      });
    };

    $rootScope.evaluateConfidentialityModalOpening = function () {
      if (!Test && // NOTE used by protractor
          !$rootScope.connection.tor &&
          !$rootScope.connection.https &&
          !$rootScope.confidentiality_warning_opened &&
          ['localhost', '127.0.0.1'].indexOf($location.host()) === -1) {

        $rootScope.confidentiality_warning_opened = true;
        $rootScope.open_confidentiality_modal();
        return true;
      }

      return false;
    }

    $rootScope.evaluateDisclaimerModalOpening = function () {
      if ($rootScope.node.enable_disclaimer && !$rootScope.disclaimer_opened) {
        $rootScope.disclaimer_opened = true;
        $rootScope.open_disclaimer_modal();
        return true;
      }

      return false;
    }

    $rootScope.init = function () {
      return PublicResource.get(function(result, getResponseHeaders) {
        if (result.node.homepage) {
          $templateCache.put('custom_homepage.html', Utils.b64DecodeUnicode(result.node.homepage));
        }

        $rootScope.answer = {value: null};

        $rootScope.node = result.node;

        $rootScope.contexts = result.contexts;
        $rootScope.contexts_by_id = $rootScope.Utils.array_to_map(result.contexts);

        $rootScope.receivers = result.receivers;
        $rootScope.receivers_by_id = $rootScope.Utils.array_to_map(result.receivers);

        $rootScope.questionnaires = result.questionnaires;
        $rootScope.questionnaires_by_id = $rootScope.Utils.array_to_map(result.questionnaires);

        $rootScope.submission_statuses = result.submission_statuses;

        angular.forEach($rootScope.contexts_by_id, function(element, key) {
          $rootScope.contexts_by_id[key].questionnaire = $rootScope.questionnaires_by_id[$rootScope.contexts_by_id[key].questionnaire_id];
        });

        if (result.node.favicon) {
          document.getElementById('favicon').setAttribute("href", "data:image/x-icon;base64," + result.node.favicon);
        }

        $rootScope.connection = {
          'https': $location.protocol() === 'https',
          'tor': false
        }

        // Tor detection and enforcing of usage of HS if users are using Tor
        if ($location.host().match(/^[a-z0-9]{16}\.onion$/)) {
          // A better check on this situation would be
          // to fetch https://check.torproject.org/api/ip
          $rootScope.connection.tor = true;
        } else if ($rootScope.connection.https) {
          var headers = getResponseHeaders();
          if (headers['x-check-tor'] !== undefined && headers['x-check-tor'] === 'true') {
            $rootScope.connection.tor = true;
            if ($rootScope.node.onionservice && !Utils.iframeCheck()) {
              // the check on the iframe is in order to avoid redirects
              // when the application is included inside iframes in order to not
              // mix HTTPS resources with HTTP resources.
              $location.path('http://' + $rootScope.node.onionservice + '/#' + $location.url());
            }
          }
        }

        GLTranslate.addNodeFacts($rootScope.node.default_language, $rootScope.node.languages_enabled);

        Utils.route_check();

        $rootScope.languages_enabled = {};
        $rootScope.languages_enabled_selector = [];
        $rootScope.languages_supported = {};
        angular.forEach($rootScope.node.languages_supported, function (lang) {
          $rootScope.languages_supported[lang.code] = lang;
          if ($rootScope.node.languages_enabled.indexOf(lang.code) !== -1) {
            $rootScope.languages_enabled[lang.code] = lang;
            $rootScope.languages_enabled_selector.push(lang);
          }
        });

        $rootScope.languages_enabled_selector = $filter('orderBy')($rootScope.languages_enabled_selector, 'code');

        Utils.set_title();

        if ($rootScope.node.enable_experimental_features) {
          $rootScope.isFieldTriggered = fieldUtilities.isFieldTriggered;
        } else {
          $rootScope.isFieldTriggered = $rootScope.dumb_function;
        }

        $rootScope.evaluateConfidentialityModalOpening();

        $rootScope.started = true;
      }).$promise;
    };

    //////////////////////////////////////////////////////////////////

    $rootScope.$watch(function() {
        return $http.pendingRequests.length;
    }, function(val) {
        $rootScope.showLoadingPanel = val > 0;
    });

    $rootScope.$watch('GLTranslate.indirect.appLanguage', function(new_val, old_val) {
      GLTranslate.setLang();
      if(old_val !== new_val) {
        $rootScope.reload();
      }
    });

    $rootScope.$on("$routeChangeStart", function() {
      if ($rootScope.node) {
        Utils.route_check();
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

    $rootScope.$on('$routeChangeSuccess', function (event, current) {
      if (current.$$route) {
        $rootScope.successes = [];
        $rootScope.errors = [];
        $rootScope.header_title = current.$$route.header_title;
        $rootScope.header_subtitle = current.$$route.header_subtitle;

        if ($rootScope.node) {
          Utils.set_title();
        }
      }
    });

    $rootScope.$on('$routeChangeError', function(event, current, previous, rejection) {
      if (rejection === Access.FORBIDDEN) {
        $rootScope.Authentication.loginRedirect(false);
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

       angular.extend(config.headers, $rootScope.Authentication.get_headers());

       return config;
     },
     'responseError': function(response) {
       /*
          When the response has failed write the rootScope
          errors array the error message.
       */

       var $rootScope = $injector.get('$rootScope');
       var $http = $injector.get('$http');
       var $q = $injector.get('$q');
       var $location = $injector.get('$location');

       if (response.status === 405) {
         var errorData = angular.toJson({
             errorUrl: $location.path(),
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

         /* 10: Not Authenticated */
         if (error.code === 10) {
           $rootScope.Authentication.loginRedirect(false);
         }

         $rootScope.errors.push(error);
       }

       return $q.reject(response);
     }
   };
}]).
factory('noopInterpolation', ['$interpolate', '$translateSanitization', function ($interpolate, $translateSanitization) {
  // simple noop interpolation service

  var $locale,
      $identifier = 'noop';

  return {
    setLocale: function(locale) {
      $locale = locale;
    },
    getInterpolationIdentifier : function () {
      return $identifier;
    },
    useSanitizeValueStrategy: function (value) {
      $translateSanitization.useStrategy(value);
      return this;
    },
    interpolate: function (value/*, interpolationParams, context, sanitizeStrategy, translationId*/) {
      return value;
    }
  };
}]).
  config(exceptionConfig);
