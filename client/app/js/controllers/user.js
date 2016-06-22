GLClient
.controller('ForcedPasswordChangeCtrl', ['$scope', '$location', '$uibModal', 'locationForce', 'Authentication', 'glbcUserKeyGen',
  function($scope, $location, $uibModal, locationForce, Authentication, glbcUserKeyGen) {
    $scope.showKeyChange = false;
    glbcUserKeyGen.setup();

    $scope.inp = {
      old_password: "",
      new_password: "",
    };

    $scope.pass_next = function () {
      glbcUserKeyGen.startProcessing();

      locationForce.clear();

      $scope.preferences.pgp_key_remove = false;

      glbcUserKeyGen.addPassphrase($scope.inp.old_password, $scope.inp.new_password);
      glbcUserKeyGen.vars.promises.ready.then(function() {
        $location.path(Authentication.session.auth_landing_page);
      });

      $scope.showKeyChange = true;
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
