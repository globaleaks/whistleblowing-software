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
controller('ForcedPasswordChangeCtrl', ['$scope', '$rootScope', '$location', 'locationForce',
  function($scope, $rootScope, $location, locationForce) {

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
