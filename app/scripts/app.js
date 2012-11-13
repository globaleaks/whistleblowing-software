'use strict';

var GLClient = angular.module('GLClient', ['nodeRequests', 
    'submissionRequests', 'submissionUI']).
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
      when('receiver/:token/preferences', {
        templateUrl: 'views/receiver/preferences.html',
        controller: 'MainCtrl'
      }).
      when('receiver/:token/list', {
        templateUrl: 'views/receiver/list.html',
        controller: 'MainCtrl'
      }).
      when('/about', {
        templateUrl: 'views/about.html',
        controller: 'MainCtrl',
      }).
      otherwise({
        redirectTo: '/'
      })
}]);

