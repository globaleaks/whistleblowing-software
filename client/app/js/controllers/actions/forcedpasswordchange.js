GL.controller("ForcedPasswordChangeCtrl", ["$scope", "$location",
  function($scope, $location) {
    $scope.changePasswordArgs = {};

    $scope.changePassword = function() {
      return $scope.Utils.runUserOperation("change_password", $scope.changePasswordArgs).then(
        function() {
          $scope.Authentication.session.require_password_change = false;
          $location.path($scope.Authentication.session.homepage);
        },
        function() {
          $scope.changePasswordArgs = {};
        });
    };
}]);
