/* eslint no-unused-vars: ["error", { "varsIgnorePattern": "GLClient" }] */

function extendExceptionHandler($delegate, $injector, $window, stacktraceService) {
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

        var errorMessage = exception.toString();
        stacktraceService.fromError(exception).then(function(result) {
          var errorData = angular.toJson({
            errorUrl: $window.location.href,
            errorMessage: errorMessage,
            stackTrace: result,
            agent: navigator.userAgent
          });

          var $http = $injector.get('$http');

          $http.post('exception', errorData);
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
    'flow',
    'pascalprecht.translate',
    'zxcvbn',
    'GLServices',
    'GLDirectives',
    'GLFilters'
  ]).
  config(['$compileProvider', '$httpProvider', '$routeProvider', '$rootScopeProvider', '$translateProvider', '$uibTooltipProvider',
    function($compileProvider, $httpProvider, $routeProvider, $rootScopeProvider, $translateProvider, $uibTooltipProvider) {
    $compileProvider.debugInfoEnabled(false);

    $httpProvider.interceptors.push('globaleaksRequestInterceptor');

    $routeProvider.
      when('/wizard', {
        templateUrl: 'views/wizard/main.html',
        controller: 'WizardCtrl',
        header_title: 'Platform wizard',
        header_subtitle: 'Step-by-step setup'
      }).
      when('/submission', {
        templateUrl: 'views/submission/main.html',
        controller: 'SubmissionCtrl',
        header_title: '',
        header_subtitle: ''
      }).
      when('/receipt', {
        templateUrl: 'views/receipt.html',
        controller: 'ReceiptController',
        header_title: '',
        header_subtitle: ''
      }).
      when('/status/:tip_id', {
        templateUrl: 'views/receiver/tip.html',
        controller: 'TipCtrl',
        header_title: '',
        header_subtitle: ''
      }).
      when('/status', {
        templateUrl: 'views/whistleblower/tip.html',
        controller: 'TipCtrl',
        header_title: '',
        header_subtitle: ''
      }).
      when('/forcedpasswordchange', {
        templateUrl: 'views/forced_password_change.html',
        controller: 'ForcedPasswordChangeCtrl',
        header_title: 'Change your password',
        header_subtitle: ''
      }).
      when('/receiver/preferences', {
        templateUrl: 'views/receiver/preferences.html',
        controller: 'PreferencesCtrl',
        header_title: 'Recipient interface',
        header_subtitle: 'Preferences'
      }).
      when('/receiver/tips', {
        templateUrl: 'views/receiver/tips.html',
        controller: 'ReceiverTipsCtrl',
        header_title: 'Recipient interface',
        header_subtitle: 'List of submissions'
      }).
      when('/admin/landing', {
        templateUrl: 'views/admin/landing.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'Landing page'
      }).
      when('/admin/content', {
        templateUrl: 'views/admin/content.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'General settings'
      }).
      when('/admin/contexts', {
        templateUrl: 'views/admin/contexts.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'Context configuration'
      }).
      when('/admin/questionnaires', {
        templateUrl: 'views/admin/questionnaires.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'Questionnaire configuration'
      }).
      when('/admin/users', {
        templateUrl: 'views/admin/users.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'User management'
      }).
      when('/admin/receivers', {
        templateUrl: 'views/admin/receivers.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'Recipient configuration'
      }).
      when('/admin/mail', {
        templateUrl: 'views/admin/mail.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'Notification settings'
      }).
      when('/admin/url_shortener', {
        templateUrl: 'views/admin/url_shortener.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'URL shortener'
      }).
      when('/admin/advanced_settings', {
        templateUrl: 'views/admin/advanced.html',
        controller: 'AdminCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'Advanced settings'
      }).
      when('/user/preferences', {
        templateUrl: 'views/user/preferences.html',
        controller: 'PreferencesCtrl',
        header_title: 'User preferences',
        header_subtitle: ''
      }).
      when('/admin/overview/users', {
        templateUrl: 'views/admin/users_overview.html',
        controller: 'OverviewCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'User overview'
      }).
      when('/admin/overview/tips', {
        templateUrl: 'views/admin/tips_overview.html',
        controller: 'OverviewCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'Submission overview'
      }).
      when('/admin/overview/files', {
        templateUrl: 'views/admin/files_overview.html',
        controller: 'OverviewCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'File overview'
      }).
      when('/admin/anomalies', {
        templateUrl: 'views/admin/anomalies.html',
        controller: 'AnomaliesCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'Anomalies'
      }).
      when('/admin/stats', {
        templateUrl: 'views/admin/stats.html',
        controller: 'StatisticsCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'System stats'
      }).
      when('/admin/activities', {
        templateUrl: 'views/admin/activities.html',
        controller: 'ActivitiesCtrl',
        header_title: 'Administration interface',
        header_subtitle: 'Recent activities'
      }).
      when('/admin', {
        templateUrl: 'views/login.html',
        controller: 'LoginCtrl',
        header_title: 'Login',
        header_subtitle: ''
      }).
      when('/custodian', {
        templateUrl: 'views/login.html',
        controller: 'LoginCtrl',
        header_title: 'Login',
        header_subtitle: ''
      }).
      when('/custodian/identityaccessrequests', {
        templateUrl: 'views/custodian/identity_access_requests.html',
        header_title: 'Custodian of the identities',
        header_subtitle: 'List of access requests to whistleblowers\' identities'
      }).
      when('/login', {
        templateUrl: 'views/login.html',
        controller: 'LoginCtrl',
        header_title: 'Login',
        header_subtitle: ''
      }).
      when('/autologin', {
        templateUrl: 'views/autologin.html',
        controller: 'AutoLoginCtrl',
        header_title: 'Login',
        header_subtitle: ''
      }).
      when('/', {
        templateUrl: 'views/home.html',
        controller: 'HomeCtrl',
        header_title: '',
        header_subtitle: ''
      }).
      otherwise({
        redirectTo: '/'
      });

      // Raise the default digest loop limit to 30 because of the template recursion used by fields:
      // https://github.com/angular/angular.js/issues/6440
      $rootScopeProvider.digestTtl(30);

      $translateProvider.useStaticFilesLoader({
        prefix: 'l10n/',
        suffix: '.json'
      });

      $translateProvider.useSanitizeValueStrategy('escape');

      $uibTooltipProvider.options({appendToBody: true});
}]).
  config(['flowFactoryProvider', function (flowFactoryProvider) {
    flowFactoryProvider.factory = fustyFlowFactory;
    flowFactoryProvider.defaults = {
        chunkSize: 1024 * 1024,
        forceChunkSize: true,
        testChunks: false,
        simultaneousUploads: 1,
        generateUniqueIdentifier: function () {
          return Math.random() * 1000000 + 1000000;
        }
    };
}]).
  factory("stacktraceService", function() {
    return({
      fromError: StackTrace.fromError
    });
}).
  factory('globaleaksRequestInterceptor', ['$rootScope', function($rootScope) {
    return {
     'request': function(config) {
       angular.extend(config.headers, $rootScope.get_auth_headers());
       return config;
     }
   };
}]).
  config(exceptionConfig);
