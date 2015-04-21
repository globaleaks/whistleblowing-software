'use strict';

GLClient.controller('LoginCtrl', ['$scope', '$location', '$routeParams', 'Receivers',
  function($scope, $location, $routeParams, Receivers) {
    var src = $routeParams['src'];

    $scope.loginUsername = "";
    $scope.loginPassword = "";
    $scope.loginRole = "receiver";

    Receivers.query(function (receivers) {
      $scope.receivers = receivers;
    });

    if (location && location.hash && location.hash.indexOf("#/admin") != -1) {
      $scope.loginUsername = "admin";
      $scope.loginRole = "admin";
    }
    $scope.$watch("loginUsername", function(){
      if ($scope.loginUsername == "admin") {
        $scope.loginRole = "admin";
      } else if ($scope.loginUsername == "wb") {
        $scope.loginRole = "wb";
      } else {
        $scope.loginRole = "receiver";
      }
    });

}]);
