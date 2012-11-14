'use strict';

var GLClient = angular.module('GLClient', ['nodeServices',
    'submissionServices', 'helpServices', 'submissionUI',
    'adminServices', 'GLClientFilters']).
  config(['$routeProvider', function($routeProvider) {
    $routeProvider.
      when('/', {
        templateUrl: 'views/home.html',
        controller: 'MainCtrl'
      }).
      when('/about', {
        templateUrl: 'views/about.html',
        controller: 'MainCtrl',
      }).
      when('/submission', {
        templateUrl: 'views/submission.html',
        controller: 'SubmissionCtrl',
      }).
      when('/status/:token', {
        templateUrl: 'views/status.html',
        controller: 'MainCtrl',
      }).
      when('/receiver/:token', {
        templateUrl: 'views/receiver/main.html',
        controller: 'MainCtrl',
      }).
      when('/receiver/:token/preferences', {
        templateUrl: 'views/receiver/preferences.html',
        controller: 'MainCtrl'
      }).
      when('/receiver/:token/list', {
        templateUrl: 'views/receiver/list.html',
        controller: 'MainCtrl'
      }).
      when('/admin/basic', {
        templateUrl: 'views/admin/basic.html',
        controller: 'AdminCtrl',
      }).
      when('/admin/advanced', {
        templateUrl: 'views/admin/basic.html',
        controller: 'AdminCtrl',
      }).
      when('/admin/wizard', {
        templateUrl: 'views/admin/wizard.html',
        controller: 'AdminCtrl',
      }).
      otherwise({
        redirectTo: '/'
      })
}]);

