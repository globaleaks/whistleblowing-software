'use strict';

var GLClient = angular.module('GLClient', ['GLClient.templates', 'resourceServices',
    'submissionUI', 'GLClientFilters']).
  config(['$routeProvider', function($routeProvider) {
    $routeProvider.
      when('/', {
        templateUrl: 'templates/default/views/home.html',
        controller: 'HomeCtrl'
      }).

      when('/about', {
        templateUrl: 'templates/default/views/about.html',
        controller: 'PageCtrl',
      }).


      when('/submission', {
        templateUrl: 'templates/default/views/submission/main.html',
        controller: 'SubmissionCtrl',
      }).


      when('/status/:tip_id', {
        templateUrl: 'templates/default/views/status.html',
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

      when('/admin/advanced', {
        templateUrl: 'views/admin/advanced.html',
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
}]);
