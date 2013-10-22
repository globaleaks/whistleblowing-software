'use strict';

GLClient.controller('LoginCtrl', ['$scope', '$location',
                    '$routeParams', 'Authentication', 
		    'cookiesEnabled', 'notificationRedirect',
  function($scope, $location, $routeParams, Authentication, 
	cookiesEnabled, notificationRedirect) {
    var src = $routeParams['src'];

    $scope.loginUsername = "";
    $scope.loginPassword = "";
    $scope.loginRole = "receiver";

    if (src && src.indexOf("/admin") != -1) {
      $scope.loginUsername = "admin";
      $scope.loginRole = "admin";
    };

    $scope.cookiesEnabled = cookiesEnabled;
    $scope.notificationRedirect = notificationRedirect;

    $scope.login = Authentication.login;

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
