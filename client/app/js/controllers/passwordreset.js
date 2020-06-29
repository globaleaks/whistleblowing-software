GLClient.controller("PasswordResetCtrl", ["$scope", "$location", "$http",
  function($scope, $location, $http) {

  $scope.request = {
    "username_or_email": ""
  };

  $scope.submit = function() {
    $http.post("api/reset/password", $scope.request).then(function() {
      $location.path("/login/passwordreset/requested");
    });
  };
}]).
controller("PasswordResetCompleteCtrl", ["$scope", "$location", "$http",
  function($scope, $location, $http) {

  $scope.request = {
    "reset_token": $location.search().token,
    "recovery_key": $location.search().recovery || "",
    "auth_code": ""
  };

  $scope.submit = function() {
    $http.put("api/reset/password", $scope.request).then(function(response) {
      $scope.request.recovery_key = "";
      $scope.request.auth_code = "";
      if(response.data.status === "success") {
        $location.url("/login?token=" + response.data.token);
      } else if (response.data.status === "require_recovery_key") {
	$location.path("/password/reset/recovery");
      } else if (response.data.status === "require_two_factor_authentication") {
	$location.path("/password/reset/2fa");
      } else {
	$location.url("/login/passwordreset/failure/token");
      }
    });
  };

  if($location.path() === "/password/reset") {
    $scope.submit();
  }
}]);
