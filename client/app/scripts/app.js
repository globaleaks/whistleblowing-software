'use strict';

var GLClient = angular.module('GLClient', [
    'ngRoute',
    'ui.bootstrap',
    'ui.sortable',
    'ang-drag-drop',
    'flow',
    'monospaced.elastic',
    'resourceServices',
    'submissionUI',
    'pascalprecht.translate',
    'e2e',
    'GLClientFilters'
  ]).
  config(['$routeProvider', '$translateProvider', '$tooltipProvider',
    function($routeProvider, $translateProvider, $tooltipProvider) {

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
        templateUrl: 'views/submission/receipt.html',
        controller: 'ReceiptController',
        header_title: '',
        header_subtitle: ''
      }).
      when('/status/:tip_id', {
        templateUrl: 'views/receiver/tip.html',
        controller: 'StatusCtrl',
        header_title: 'Receiver Interface',
        header_subtitle: 'Tip Status Page'
      }).
      when('/status', {
        templateUrl: 'views/whistleblower/tip.html',
        controller: 'StatusCtrl',
        header_title: 'Whistleblower Interface',
        header_subtitle: 'Tip Status Page'
      }).
      when('/receiver/firstlogin', {
        templateUrl: 'views/receiver/firstlogin.html',
        controller: 'ReceiverFirstLoginCtrl',
        header_title: 'Receiver First Login',
        header_subtitle: ''
      }).
      when('/receiver/preferences', {
        templateUrl: 'views/receiver/preferences.html',
        controller: 'ReceiverPreferencesCtrl',
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
        templateUrl: 'views/admin/fields.html',
        controller: 'AdminCtrl',
        header_title: 'Administration Interface',
        header_subtitle: 'Fields Configuration'
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
      when('/admin/password', {
        templateUrl: 'views/admin/password.html',
        controller: 'AdminCtrl',
        header_title: 'Administration Interface',
        header_subtitle: 'Password Configuration'
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
        templateUrl: 'views/admin.html',
        controller: 'LoginCtrl',
        header_title: 'Login',
        header_subtitle: ''
      }).
      when('/embedded/submission', {
        templateUrl: 'views/embedded/submission.html',
        controller: 'EmbeddedSubmissionCtrl',
        header_title: '',
        header_subtitle: ''
      }).
      when('/embedded/receipt', {
        templateUrl: 'views/embedded/receipt.html',
        controller: 'EmbeddedReceiptCtrl',
        header_title: '',
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

      $tooltipProvider.options({appendToBody: true});
}]).
  config(['flowFactoryProvider', function (flowFactoryProvider) {
    flowFactoryProvider.defaults = {
        chunkSize: 1 * 1024 * 1024,
        forceChunkSize: true,
        generateUniqueIdentifier: function (file) {
          return Math.random() * 1000000 + 1000000;
        }
    }
}]).
  run(['$http', '$rootScope', function ($http, $rootScope) {

     var globaleaksRequestInterceptor = function(data, headers) {

        headers = angular.extend(headers(), $rootScope.get_auth_headers());

        return data;
    };

    $http.defaults.transformRequest.push(globaleaksRequestInterceptor);

    function overrideReload(e) {
       if (((e.which || e.keyCode) == 116) || /* F5 */
           ((e.which || e.keyCode) == 82 && (e.ctrlKey || e.metaKey))) {  /* (ctrl or meta) + r */ 
           e.preventDefault();
           $rootScope.$broadcast("REFRESH");
       }
    }
      $(document).bind("keydown", overrideReload);

    $rootScope.$on('$routeChangeSuccess', function (event, current, previous) {
        if (current.$$route) {
          $rootScope.header_title = current.$$route.header_title;
          $rootScope.header_subtitle = current.$$route.header_subtitle;
          $rootScope.errors = [];
        }
    });

    document.cookie = 'cookiesenabled=true;';
    if (document.cookie == "") {
      $rootScope.cookiesEnabled = false;
    } else {
      $rootScope.cookiesEnabled = true;
      $.removeCookie('cookiesenabled');
    }

    $rootScope.anonymous = false;
    $rootScope.embedded = false;
}]);
