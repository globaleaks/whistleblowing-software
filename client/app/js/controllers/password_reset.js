GLClient.controller("PasswordResetCtrl", ["$scope", "$location", "$http",
  function($scope, $location, $http) {

  $scope.request = {
    "username_or_email": ""
  };

  $scope.submit = function() {
    $http.post("reset/password", $scope.request).then(function(response) {
      $location.path('/login/passwordreset/requested');
    });
  }
}]).
controller("PasswordResetCompleteCtrl", ["$scope", "$location", "$http",
  function($scope, $location, $http) {
  $scope.request = {
    "reset_token": $location.search().token,
    "recovery_key": ""
  };

  $http.put("reset/password", $scope.request).then(function(response) {
    if(response.data.status == 'success') {
      $location.url('/login?token=' + response.data.token);
    } else {
      $location.url('/login/passwordreset/failure/token');
    }
  });
}]).
controller("PasswordResetRecoveryCtrl", ["$scope", "$location", "$http",
  function($scope, $location, $http) {

  $scope.request = {
    "reset_token": $location.search().token,
    "recovery_key": $location.search().recovery
  };

  $scope.submit = function() {
    $http.put("reset/password", $scope.request).then(function(response) {
      if(response.data.status == 'success') {
        $location.url('/login?token=' + response.data.token);
      } if (response.data.status == 'invalid_recovery_key_provided') {
	$location.url('/login/passwordreset/failure/recovery');
      } else {
	$location.url('/login/passwordreset/failure/token');
      }
    });
  }
}]);
