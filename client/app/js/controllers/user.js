GLClient.controller('UserCtrl',
  ['$scope', '$location', 'Authentication', 'GLTranslate',
  function($scope, $location, Authentication, GLTranslate, Utils) {

  $scope.GLTranslate = GLTranslate;
  $scope.Authentication = Authentication;
  $scope.Utils = Utils;
}]).
controller('ForcedPasswordChangeCtrl', ['$scope', '$location', 'locationForce',
  function($scope, $location, locationForce) {

    $scope.pass_save = function () {
      locationForce.clear();

      // avoid changing any PGP setting
      $scope.preferences.pgp_key_remove = false;
      $scope.preferences.pgp_key_public = '';

      $scope.preferences.$update(function () {
        $location.path($scope.session.auth_landing_page);
      });
    };
}])
.factory('locationForce', ['$location', '$rootScope', function($location,  $rootScope) {

  var forcedLocation = null;
  var deregister = function() {};

  return {
    set: function(path) {
      forcedLocation = path;

      deregister = $rootScope.$on("$locationChangeStart", function(event, next) {
        next = next.substring($location.absUrl().length - $location.url().length);
        if (forcedLocation !== null && next !== forcedLocation) {
          event.preventDefault();
        }
      }); 

      $location.path(path);
    },
    
    clear: function() {
      forcedLocation = null;
      deregister();
    },

  };
}]);
