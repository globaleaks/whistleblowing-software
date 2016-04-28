GLClient.controller('UserCtrl',
  ['$scope', '$rootScope', '$location', 'GLTranslate', 'WhistleblowerTip', 
  function($scope, $rootScope, $location, GLTranslate, WhistleblowerTip) {

  $scope.GLTranslate = GLTranslate;

  $scope.view_tip = function(keycode) {
    keycode = keycode.replace(/\D/g,'');
    new WhistleblowerTip(keycode, function() {
      $location.path('/status');
    });
  };
}]).
controller('ForcedPasswordChangeCtrl', ['$scope', '$rootScope', '$location',
  function($scope, $rootScope, $location) {

    $scope.pass_save = function () {
      // avoid changing any PGP setting
      $scope.preferences.pgp_key_remove = false;
      $scope.preferences.pgp_key_public = '';

      $scope.preferences.$update(function () {
        $location.path($scope.session.auth_landing_page);
      });
    };
}]);
