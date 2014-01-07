'use strict';

var GLClient = angular.module('GLClient', [
    'ngRoute',
    'ui.bootstrap',
    'ui.sortable',
    'resourceServices',
    'submissionUI',
    'GLClientFilters',
    'blueimp.fileupload',
    'pascalprecht.translate'
  ]).
  config(['$routeProvider', '$translateProvider', '$tooltipProvider', function($routeProvider, $translateProvider, $tooltipProvider) {

    $routeProvider.
      when('/', {
        templateUrl: 'views/home.html',
        controller: 'HomeCtrl'
      }).
      when('/submission', {
        templateUrl: 'views/submission/main.html',
        controller: 'SubmissionCtrl',
      }).
      when('/status', {
        templateUrl: 'views/whistleblower/tip.html',
        controller: 'StatusCtrl',
      }).
      when('/status/:tip_id', {
        templateUrl: 'views/receiver/tip.html',
        controller: 'StatusCtrl',
      }).
      when('/receiver/preferences', {
        templateUrl: 'views/receiver/preferences.html',
        controller: 'ReceiverPreferencesCtrl'
      }).
      when('/receiver/tips', {
        templateUrl: 'views/receiver/tips.html',
        controller: 'ReceiverTipsCtrl'
      }).
      when('/admin/content', {
        templateUrl: 'views/admin/content.html',
        controller: 'AdminCtrl',
      }).
      when('/admin/contexts', {
        templateUrl: 'views/admin/contexts.html',
        controller: 'AdminCtrl',
      }).
      when('/admin/receivers', {
        templateUrl: 'views/admin/receivers.html',
        controller: 'AdminCtrl',
      }).
      when('/admin/mail', {
        templateUrl: 'views/admin/mail.html',
        controller: 'AdminCtrl',
      }).
      when('/admin/advanced_settings', {
        templateUrl: 'views/admin/advanced.html',
        controller: 'AdminCtrl',
      }).

      when('/admin/password', {
        templateUrl: 'views/admin/password.html',
        controller: 'AdminCtrl',
      }).

      when('/admin/overview/users', {
        templateUrl: 'views/admin/users_overview.html',
        controller: 'OverviewCtrl',
      }).
      when('/admin/overview/tips', {
        templateUrl: 'views/admin/tips_overview.html',
        controller: 'OverviewCtrl',
      }).
      when('/admin/overview/files', {
        templateUrl: 'views/admin/files_overview.html',
        controller: 'OverviewCtrl',
      }).
      when('/login', {
        templateUrl: 'views/login.html',
        controller: 'LoginCtrl',
      }).
      otherwise({
        redirectTo: '/'
      })

      $translateProvider.useStaticFilesLoader({
        prefix: 'l10n/',
        suffix: '.json'
      });

      $translateProvider.uses('en');

      $tooltipProvider.options( {appendToBody: true} );
}]).
  run(['$http', '$rootScope', '$route', 'Authentication', function ($http, $rootScope, $route, Authentication) {

     var globaleaksRequestInterceptor = function(data, headers) {

        var extra_headers = {};

        if (Authentication.id) {
          extra_headers['X-Session'] = Authentication.id;
        };

        if ($.cookie('XSRF-TOKEN')) {
          extra_headers['X-XSRF-TOKEN'] = $.cookie('XSRF-TOKEN');
        }

        if ($rootScope.language) {
          extra_headers['GL-Language'] = $rootScope.language;
        };

        headers = angular.extend(headers(), extra_headers);

        return data;
    };

    $http.defaults.transformRequest.push(globaleaksRequestInterceptor);

    var reload = function() {
        $route.reload();
    }

    function overloadReload(e) {
       if (((e.which || e.keyCode) == 116) || /* F5       */
           ((e.which || e.keyCode) == 82 && (e.ctrlKey || e.metaKey))) {  /* (ctrl or meta) + r */ 
           e.preventDefault();
           reload();
       }
    };

    $(document).bind("keydown", overloadReload);

    $rootScope.reload = reload;

}]);
