'use strict';

var translations = {
 GLOBALEAKS: "{{NodeName}} makes use of GlobaLeaks software specifically designed to protect the identity of the submitter and of the receiver in the exchange of leaked materials."
};

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
      when('/wizard/:lang?', {
        templateUrl: 'views/wizard/main.html',
        controller: 'WizardCtrl',
        header_title: 'GlobaLeaks Wizard',
        header_subtitle: 'Step-by-step setup'
      }).
      when('/submission/:lang?', {
        templateUrl: 'views/submission/main.html',
        controller: 'SubmissionCtrl',
        header_title: 'Blow the Whistle',
        header_subtitle: ''
      }).
      when('/status/:lang?', {
        templateUrl: 'views/whistleblower/tip.html',
        controller: 'StatusCtrl',
        header_title: 'Whistleblower Interface',
        header_subtitle: 'Tip Status Page'
      }).
      when('/receiver/preferences/:lang?', {
        templateUrl: 'views/receiver/preferences.html',
        controller: 'ReceiverPreferencesCtrl',
        header_title: 'Receiver Interface',
        header_subtitle: ''
      }).
      when('/receiver/tips/:lang?', {
        templateUrl: 'views/receiver/tips.html',
        controller: 'ReceiverTipsCtrl',
        header_title: 'Receiver Interface',
        header_subtitle: 'Your Tips'
      }).
      when('/admin/landing/:lang?', {
        templateUrl: 'views/admin/landing.html',
        controller: 'AdminCtrl',
        header_title: 'Administration Interface',
        header_subtitle: 'Landing Page'
      }).
      when('/admin/content/:lang?', {
        templateUrl: 'views/admin/content.html',
        controller: 'AdminCtrl',
        header_title: 'Administration Interface',
        header_subtitle: 'Content Settings'
      }).
      when('/admin/contexts/:lang?', {
        templateUrl: 'views/admin/contexts.html',
        controller: 'AdminCtrl',
        header_title: 'Administration Interface',
        header_subtitle: 'Contexts Configuration'
      }).
      when('/admin/receivers/:lang?', {
        templateUrl: 'views/admin/receivers.html',
        controller: 'AdminCtrl',
        header_title: 'Administration Interface',
        header_subtitle: 'Receivers Configuration'
      }).
      when('/admin/mail/:lang?', {
        templateUrl: 'views/admin/mail.html',
        controller: 'AdminCtrl',
        header_title: 'Administration Interface',
        header_subtitle: 'Mail Configuration'
      }).
      when('/admin/advanced_settings/:lang?', {
        templateUrl: 'views/admin/advanced.html',
        controller: 'AdminCtrl',
        header_title: 'Administration Interface',
        header_subtitle: 'Advanced Settings'
      }).
      when('/admin/password/:lang?', {
        templateUrl: 'views/admin/password.html',
        controller: 'AdminCtrl',
        header_title: 'Administration Interface',
        header_subtitle: 'Password Configuration'
      }).
      when('/admin/overview/users/:lang?', {
        templateUrl: 'views/admin/users_overview.html',
        controller: 'OverviewCtrl',
        header_title: 'Administration Interface',
        header_subtitle: 'Users Overview'
      }).
      when('/admin/overview/tips/:lang?', {
        templateUrl: 'views/admin/tips_overview.html',
        controller: 'OverviewCtrl',
        header_title: 'Administration Interface',
        header_subtitle: 'Tips Overview'
      }).
      when('/admin/overview/files/:lang?', {
        templateUrl: 'views/admin/files_overview.html',
        controller: 'OverviewCtrl',
        header_title: 'Administration Interface',
        header_subtitle: 'Files Overview'
      }).
      when('/admin/stats/:lang?', {
        templateUrl: 'views/admin/stats.html',
        controller: 'StatisticsCtrl',
        header_title: 'Administration Interface',
        header_subtitle: 'System Stats'
      }).
      when('/login/:lang?', {
        templateUrl: 'views/login.html',
        controller: 'LoginCtrl',
        header_title: 'Login',
        header_subtitle: ''
      }).
      when('/start/:lang?', {
        templateUrl: 'views/home.html',
        controller: 'HomeCtrl',
        header_title: '',
        header_subtitle: ''
      }).
      when('/:lang?', {
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

      $tooltipProvider.options( {appendToBody: true} );
}]).
  run(['$http', '$rootScope', '$route', 'Authentication', function ($http, $rootScope, $route, Authentication) {

     var globaleaksRequestInterceptor = function(data, headers) {

        headers = angular.extend(headers(), Authentication.headers());

        return data;
    };

    $http.defaults.transformRequest.push(globaleaksRequestInterceptor);

    var reload = function () {
      $route.reload();
    };

    function overrideReload(e) {
       if (((e.which || e.keyCode) == 116) || /* F5 */
           ((e.which || e.keyCode) == 82 && (e.ctrlKey || e.metaKey))) {  /* (ctrl or meta) + r */ 
           e.preventDefault();
           $rootScope.$broadcast("REFRESH");
           reload();
       }
    };

    $(document).bind("keydown", overrideReload);

    $rootScope.reload = reload;

    $rootScope.$on('$routeChangeSuccess', function (event, current, previous) {
        if (current.$$route) {
          $rootScope.header_title = current.$$route.header_title;
          $rootScope.header_subtitle = current.$$route.header_subtitle;
        }
    });

    document.cookie = 'cookiesenabled=true;';
    if (document.cookie == "") {
      $rootScope.cookiesEnabled = false;
    } else {
      $rootScope.cookiesEnabled = true;
      $.removeCookie('cookiesenabled');
    }

    $rootScope.$on('$routeChangeSuccess', function (event, current, previous) {
        if (current.$$route) {
          $rootScope.header_title = current.$$route.header_title;
          $rootScope.header_subtitle = current.$$route.header_subtitle;
        }
    });


    /* initialization of privacy detection variables */
    $rootScope.privacy = 'unknown';
    $rootScope.anonymous = false;

}]);
