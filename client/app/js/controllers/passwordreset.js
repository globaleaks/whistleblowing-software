GL.controller("PasswordResetCtrl", ["$scope", "$location", "$http",
  function($scope, $location, $http) {

  $scope.request = {
    "username": ""
  };

  $scope.submit = function() {
    $http.post("api/user/reset/password", $scope.request).then(function() {
      $location.path("/login/passwordreset/requested");
    });
  };
}]).
controller("PasswordResetCompleteCtrl", ["$scope", "$location", "$http",
  function($scope, $location, $http) {

  $scope.state = "start";

  $scope.request = {
    "reset_token": $location.search().token || "",
    "recovery_key": $location.search().recovery || "",
    "auth_code": ""
  };

  $scope.submit = function() {
    $http.put("api/user/reset/password", $scope.request).then(function(response) {
      if(response.data.status === "success") {
        $location.url("/login?token=" + response.data.token);
      } else {
        if (response.data.status === "require_recovery_key") {
          $scope.request.recovery_key = "";
        }

        $scope.request.auth_code = "";
	$scope.state = response.data.status;
      }
    });
  };

  if($scope.state === "start") {
    $scope.submit();
  }
}]);
