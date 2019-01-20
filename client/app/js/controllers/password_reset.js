GLClient.controller("PasswordResetCtrl", ["$scope", "$location", "$http",
  function($scope, $location, $http) {
  $scope.data = {
    "username_or_email": ""
  };

  if (!$scope.node.enable_password_reset) {
    $location.path("/");
  }

  $scope.submit = function() {
    $http.post("reset/password", $scope.data);
    $location.path("/login/passwordreset/requested");
  };
}]);
