'use strict';

var GLClient = angular.module('GLClient', ['ui', 'resourceServices',
    'submissionUI', 'GLClientFilters']).
  config(['$routeProvider', function($routeProvider) {
    $routeProvider.
      when('/', {
        templateUrl: 'views/home.html',
        controller: 'HomeCtrl'
      }).

      when('/about', {
        templateUrl: 'views/about.html',
        controller: 'PageCtrl',
      }).


      when('/submission', {
        templateUrl: 'views/submission.html',
        controller: 'SubmissionCtrl',
      }).


      when('/status/:tip_id', {
        templateUrl: 'views/status.html',
        controller: 'StatusCtrl',
      }).


      when('/receiver/:token', {
        templateUrl: 'views/receiver/main.html',
        controller: 'ReceiverCtrl',
      }).
      when('/receiver/:token/preferences', {
        templateUrl: 'views/receiver/preferences.html',
        controller: 'ReceiverCtrl'
      }).
      when('/receiver/:token/list', {
        templateUrl: 'views/receiver/list.html',
        controller: 'ReceiverCtrl'
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


      when('/login', {
        templateUrl: 'views/login.html',
        controller: 'LoginCtrl',
      }).

      otherwise({
        redirectTo: '/'
      })
}]);

