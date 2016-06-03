GLClient
.controller('ForcedPasswordChangeCtrl', ['$scope', '$location', 'locationForce', 'glbcUser', 'glbcReceiver', 'glbcKeyRing',
  function($scope, $location, locationForce, glbcUser, glbcReceiver, glbcKeyRing) {
    $scope.key_gen = false;
    $scope.key_gen_msgs = [];

    $scope.pass_save = function () {
      locationForce.clear();

      $scope.preferences.pgp_key_remove = false;

      var old_pw = $scope.preferences.old_password;
      var old_salt = $scope.preferences.salt;
      var new_pw = $scope.preferences.password;
      var uname = $scope.preferences.name;

      glbcUser.changePassword(uname, new_pw, old_pw, old_salt).then(function(res) {
        var p;

        if ($scope.preferences.ccrypto_key_public === '') {
          $scope.key_gen = true;
          p = glbcKeyRing.createNewCCryptoKey(res.new_passphrase).then(
            function() {
              $scope.key_gen_msgs.push('Posting new key pair to server. . .');
              return glbcUser.submitNewKeyPair(res.auth_token_hash);
            },
            function(err) { return err; },
            function(msg) { 
              $scope.key_gen_msgs.push(msg);
            }
          );
        } else {
          p = glbcReceiver.updatePrivateKey(res);
        }

        return p.then(function() {
          $scope.key_gen_msgs.push('Key gen finished! Redirecting!');
          $location.path($scope.session.auth_landing_page);
        });
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
