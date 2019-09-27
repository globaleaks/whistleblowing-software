GLClient
.controller("ForcedPasswordChangeCtrl", ["$scope", "$location",
  function($scope, $location) {
    $scope.save = function () {
      return $scope.preferences.$update(function () {
        $scope.session.password_change_needed = false;
        $location.path($scope.session.auth_landing_page);
      });
    };
}]);
