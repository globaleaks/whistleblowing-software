GLClient.controller('LoginCtrl', ['$scope', '$location', function($scope, $location) {
  $scope.loginUsername = "";
  $scope.loginPassword = "";

  if ($location.path() === '/admin') {
    $scope.loginRole = "admin";
  } else {
    $scope.loginRole = "receiver";
  }
}]);
