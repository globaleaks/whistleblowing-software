'use strict';

var GLClient = angular.module('GLClient', [
    'ngAria',
    'ngRoute',
    'ui.bootstrap',
    'flow',
    'monospaced.elastic',
    'pascalprecht.translate',
    'GLServices',
    'GLDirectives',
    'GLFilters'
  ]).
  config(['$compileProvider', '$routeProvider', '$translateProvider', '$tooltipProvider',
    function($compileProvider, $routeProvider, $translateProvider, $tooltipProvider) {

    $compileProvider.debugInfoEnabled(false);

    $routeProvider.
      when('/wizard', {
        templateUrl: 'views/wizard/main.html',
        controller: 'WizardCtrl',
        header_title: 'GlobaLeaks Wizard',
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
        header_title: 'Receiver Interface',
        header_subtitle: 'Tip Status Page'
      }).
      when('/status', {
        templateUrl: 'views/whistleblower/tip.html',
        controller: 'TipCtrl',
        header_title: 'Whistleblower Interface',
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
        header_title: 'Receiver Interface',
        header_subtitle: 'Preferences'
      }).
      when('/receiver/tips', {
        templateUrl: 'views/receiver/tips.html',
        controller: 'ReceiverTipsCtrl',
        header_title: 'Receiver Interface',
        header_subtitle: 'Your Tips'
      }).
      when('/admin/landing', {
        templateUrl: 'views/admin/landing.html',
        controller: 'AdminCtrl',
        header_title: 'Administration Interface',
        header_subtitle: 'Landing Page'
      }).
      when('/admin/content', {
        templateUrl: 'views/admin/content.html',
        controller: 'AdminCtrl',
        header_title: 'Administration Interface',
        header_subtitle: 'Content Settings'
      }).
      when('/admin/contexts', {
        templateUrl: 'views/admin/contexts.html',
        controller: 'AdminCtrl',
        header_title: 'Administration Interface',
        header_subtitle: 'Contexts Configuration'
      }).
      when('/admin/fields', {
        templateUrl: 'views/admin/field_templates.html',
        controller: 'AdminCtrl',
        header_title: 'Administration Interface',
        header_subtitle: 'Fields Configuration'
      }).
      when('/admin/users', {
        templateUrl: 'views/admin/users.html',
        controller: 'AdminCtrl',
        header_title: 'Administration Interface',
        header_subtitle: 'Users Configuration'
      }).
      when('/admin/receivers', {
        templateUrl: 'views/admin/receivers.html',
        controller: 'AdminCtrl',
        header_title: 'Administration Interface',
        header_subtitle: 'Receivers Configuration'
      }).
      when('/admin/mail', {
        templateUrl: 'views/admin/mail.html',
        controller: 'AdminCtrl',
        header_title: 'Administration Interface',
        header_subtitle: 'Email Configuration'
      }).
      when('/admin/advanced_settings', {
        templateUrl: 'views/admin/advanced.html',
        controller: 'AdminCtrl',
        header_title: 'Administration Interface',
        header_subtitle: 'Advanced Settings'
      }).
      when('/user/preferences', {
        templateUrl: 'views/user/preferences.html',
        controller: 'PreferencesCtrl',
        header_title: 'User Preferences',
        header_subtitle: ''
      }).
      when('/admin/overview/users', {
        templateUrl: 'views/admin/users_overview.html',
        controller: 'OverviewCtrl',
        header_title: 'Administration Interface',
        header_subtitle: 'Users Overview'
      }).
      when('/admin/overview/tips', {
        templateUrl: 'views/admin/tips_overview.html',
        controller: 'OverviewCtrl',
        header_title: 'Administration Interface',
        header_subtitle: 'Tips Overview'
      }).
      when('/admin/overview/files', {
        templateUrl: 'views/admin/files_overview.html',
        controller: 'OverviewCtrl',
        header_title: 'Administration Interface',
        header_subtitle: 'Files Overview'
      }).
      when('/admin/anomalies', {
        templateUrl: 'views/admin/anomalies.html',
        controller: 'AnomaliesCtrl',
        header_title: 'Administration Interface',
        header_subtitle: 'Anomalies'
      }).
      when('/admin/stats', {
        templateUrl: 'views/admin/stats.html',
        controller: 'StatisticsCtrl',
        header_title: 'Administration Interface',
        header_subtitle: 'System Stats'
      }).
      when('/admin/activities', {
        templateUrl: 'views/admin/activities.html',
        controller: 'ActivitiesCtrl',
        header_title: 'Administration Interface',
        header_subtitle: 'Recent Activities'
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
      when('/login', {
        templateUrl: 'views/login.html',
        controller: 'LoginCtrl',
        header_title: 'Login',
        header_subtitle: ''
      }).
      when('/start', {
        templateUrl: 'views/home.html',
        controller: 'HomeCtrl',
        header_title: '',
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

      $translateProvider.useStaticFilesLoader({
        prefix: 'l10n/',
        suffix: '.json'
      });

      $translateProvider.useSanitizeValueStrategy('escape');

      $tooltipProvider.options({appendToBody: true});
}]).
  config(['flowFactoryProvider', function (flowFactoryProvider) {
    flowFactoryProvider.defaults = {
        chunkSize: 1 * 1024 * 1024,
        forceChunkSize: true,
        testChunks: false,
        simultaneousUploads: 1,
        generateUniqueIdentifier: function (file) {
          return Math.random() * 1000000 + 1000000;
        }
    };
}]).
  factory("stacktraceService", function() {
    return({
      print: printStackTrace
    });
}).
  config(exceptionConfig).
  run(['$http', '$rootScope', '$location', function ($http, $rootScope, $location) {
     $rootScope.successes = [];
     $rootScope.errors = [];
     $rootScope.loginInProgress = false;

     var globaleaksRequestInterceptor = function(data, headers) {
        headers = angular.extend(headers(), $rootScope.get_auth_headers());
        return data;
    };

    $http.defaults.transformRequest.push(globaleaksRequestInterceptor);

    // register listener to watch route changes
    $rootScope.$on("$routeChangeStart", function(event, next, current) {
      var path = $location.path();
      var embedded = '/embedded/';

      if (path.substr(0, embedded.length) === embedded) {
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

    $rootScope.$on('$routeChangeSuccess', function (event, current, previous) {
        if (current.$$route) {
          $rootScope.successes = [];
          $rootScope.errors = [];
          $rootScope.header_title = current.$$route.header_title;
          $rootScope.header_subtitle = current.$$route.header_subtitle;
        }
    });

    $rootScope.anonymous = false;
    $rootScope.embedded = false;
}]);

exceptionConfig.$inject = ['$provide'];

function exceptionConfig($provide) {
    $provide.decorator('$exceptionHandler', extendExceptionHandler);
}

extendExceptionHandler.$inject = ['$delegate', '$injector', '$window', 'stacktraceService'];

function extendExceptionHandler($delegate, $injector, $window, stacktraceService) {
    return function(exception, cause) {

        var $rootScope = $injector.get('$rootScope');

        if ($rootScope.exceptions_count == undefined) {
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
        var stackTrace = stacktraceService.print({e: exception});

        var errorData = angular.toJson({
          errorUrl: $window.location.href,
          errorMessage: errorMessage,
          stackTrace: stackTrace,
          agent: navigator.userAgent
        });

        var $http = $injector.get('$http');

        $http.post('exception', errorData);
    };
}
