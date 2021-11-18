GL.controller("ForcedPasswordChangeCtrl", ["$scope", "$location",
  function($scope, $location) {
    $scope.save = function () {
      return $scope.resources.preferences.$update(function () {
        $scope.Authentication.session.require_password_change = false;
        $location.path($scope.Authentication.session.homepage);
      });
    };
}]);
