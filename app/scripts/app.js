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
      when('/admin/basic', {
        templateUrl: 'views/admin/basic.html',
        controller: 'AdminCtrl',
      }).
      when('/admin/advanced', {
        templateUrl: 'views/admin/advanced.html',
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

