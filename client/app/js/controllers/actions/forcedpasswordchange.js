GL.controller("ForcedPasswordChangeCtrl", ["$scope", "$location",
  function($scope, $location) {
    $scope.changePasswordArgs = {"current": ""};

    $scope.changePassword = function() {
      return $scope.Utils.runUserOperation("change_password", $scope.changePasswordArgs).then(
        function() {
          $scope.resources.preferences.password_change_needed = false;
          $location.path($scope.Authentication.session.homepage);
        },
        function() {
          $scope.changePasswordArgs = {};
        });
    };
}]);
