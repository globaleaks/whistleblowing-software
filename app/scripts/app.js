'use strict';

var GLClient = angular.module('GLClient', ['resourceServices', 
    'submissionUI', 'localeServices', 'GLClientFilters']).
  config(['$routeProvider', function($routeProvider) {
    $routeProvider.
      when('/', {
        templateUrl: 'views/home.html',
        controller: 'PageCtrl'
      }).
      when('/about', {
        templateUrl: 'views/about.html',
        controller: 'PageCtrl',
      }).
      when('/submission', {
        templateUrl: 'views/submission.html',
        controller: 'SubmissionCtrl',
      }).
      when('/status/:token', {
        templateUrl: 'views/status.html',
        controller: 'PageCtrl',
      }).
      when('/receiver/:token', {
        templateUrl: 'views/receiver/main.html',
        controller: 'PageCtrl',
      }).
      when('/receiver/:token/preferences', {
        templateUrl: 'views/receiver/preferences.html',
        controller: 'PageCtrl'
      }).
      when('/receiver/:token/list', {
        templateUrl: 'views/receiver/list.html',
        controller: 'PageCtrl'
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

