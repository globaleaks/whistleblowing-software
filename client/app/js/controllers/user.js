GLClient.controller('UserCtrl',
  ['$scope', '$location', 'Authentication', 'GLTranslate',
  function($scope, $location, Authentication, GLTranslate, Utils) {

  $scope.GLTranslate = GLTranslate;
  $scope.Authentication = Authentication;
  $scope.Utils = Utils
}]).
controller('ForcedPasswordChangeCtrl', ['$scope', '$location',
  function($scope, $location) {

    $scope.pass_save = function () {
      // avoid changing any PGP setting
      $scope.preferences.pgp_key_remove = false;
      $scope.preferences.pgp_key_public = '';

      $scope.preferences.$update(function () {
        $location.path($scope.session.auth_landing_page);
      });
    };
}]);
