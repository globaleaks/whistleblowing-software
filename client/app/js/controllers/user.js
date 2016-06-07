GLClient
.controller('ForcedPasswordChangeCtrl', ['$scope', '$location', '$uibModal', 'locationForce', 'Authentication', 'glbcUserKeyGen',
  function($scope, $location, $uibModal, locationForce, Authentication, glbcUserKeyGen) {
    glbcUserKeyGen.startKeyGen();

    $scope.pass_save = function () {

      locationForce.clear();

      $scope.preferences.pgp_key_remove = false;

      var old_pw = $scope.preferences.old_password;
      var new_pw = $scope.preferences.password;
      var uname = $scope.preferences.name;

      glbcUserKeyGen.addPassphrase(uname, new_pw, old_pw);

      $uibModal.open({
        templateUrl: 'views/partials/client_key_gen.html',
        controller: ['$scope', 'glbcUserKeyGen', function($scope, glbcUserKeyGen) {
          console.log('enc modal ctrl', glbcUserKeyGen);
          $scope.close_on = false;
          glbcUserKeyGen.vars.promises.ready.then(function() {
            $scope.close_on = true;
            // TODO redirect here using lochandler
          });
          $scope.finishStep = function() {
            $scope.$close();
            $location.path(Authentication.session.auth_landing_page);
          };
          $scope.msgs = glbcUserKeyGen.vars.msgQueue;
        }],
        resolve: { glbcUserKeyGen: glbcUserKeyGen },
        size: 'md',
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
