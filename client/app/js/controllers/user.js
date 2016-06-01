GLClient
.controller('ForcedPasswordChangeCtrl', ['$scope', '$location', 'locationForce', 'glbcUser', 'glbcReceiver',
  function($scope, $location, locationForce, glbcUser, glbcReceiver) {

    $scope.pass_save = function () {
      locationForce.clear();

      // avoid changing any PGP setting
      $scope.preferences.pgp_key_remove = false;

      var old_pw = $scope.preferences.old_password;
      var old_salt = $scope.preferences.salt;
      var new_pw = $scope.preferences.password;
      var uname = $scope.preferences.name;

      glbcUser.changePassword(uname, new_pw, old_pw, old_salt)
      .then(glbcReceiver.updatePrivateKey)
      .then(function() {
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
