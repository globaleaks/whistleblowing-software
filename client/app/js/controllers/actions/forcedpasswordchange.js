GLClient
.controller("ForcedPasswordChangeCtrl", ["$scope", "$location",
  function($scope, $location) {
    $scope.save = function () {
      return $scope.preferences.$update(function () {
        $scope.Authentication.session.password_change_needed = false;
        $location.path($scope.Authentication.session.homepage);
      });
    };
}]);
