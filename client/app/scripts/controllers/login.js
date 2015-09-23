GLClient.controller('LoginCtrl', ['$scope', '$location', function($scope, $location) {
  $scope.loginUsername = "";
  $scope.loginPassword = "";

  if ($location.path() === '/login' && $scope.node.simplified_login) {
    $scope.simplifiedLogin = true;
  } else {
    $scope.simplifiedLogin = false;
  }
}]);
