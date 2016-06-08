angular.module('GLBrowserCrypto')
.directive('glbcKeyChangeElem', ['$location', 'Authentication', 'glbcUserKeyGen', function($location, Authentication, glbcUserKeyGen) {

  return {
    restrict: 'A',
    templateUrl: 'views/partials/client_key_gen.html',
    controller: ['$scope', '$rootScope', function($scope, $rootScope) {
      glbcUserKeyGen.vars.promises.ready.then(function() {
        $location.path(Authentication.session.auth_landing_page);
        $rootScope.success.push("Key change succeeded!");
      }, function(failure) {
        console.log(failure);
        $location.path(Authentication.session.auth_landing_page);
        $rootScope.errors.push("Key change failed with " + failure);
      });
      $scope.msgs = glbcUserKeyGen.vars.msgQueue;
    }],

  };
}])
.factory('glbcUserKeyGen', ['$q', '$http', '$timeout', 'Authentication', 'glbcKeyLib', 'glbcKeyRing', function($q, $http, $timeout, Authentication, glbcKeyLib, glbcKeyRing) { 
  var vars = {};

  function showMsg(msg) {
    console.log(msg);
    vars.msgP = vars.msgP.then(function() {
      return $timeout(function() {
        vars.msgQueue.push(msg);
      }, 1000);
    });
  }

  
  return {
    vars: vars,

    // TODO document usage: setup -> noKeyGen -> AddPassPhrase; catch ready
    setup: function() {
      vars = {
        msgQueue: [],
        msgP: $q(function(resolve) {
          resolve();
        }),
        promises: {
          keyGen: $q.defer(),
          authDerived: $q.defer(),
          speedLimit: $q.defer(),
          ready: undefined,
        },
      };
      this.vars = vars;

      vars.promises.ready = $q.all([
        vars.promises.keyGen.promise,
        vars.promises.authDerived.promise,
        vars.promises.speedLimit.promise,
      ]).then(function(results) {
        showMsg('Encrypting private key with new passphrase. . .');
        glbcKeyRing.lockKeyRing(results[1].new_res.passphrase);
        return results;
      }).then(function(results) {
        showMsg('Saving private key on the platform. . . ');
        var authDeriv = results[1];
        return $http.post('/user/passprivkey', {
          'old_auth_token_hash': authDeriv.old_res.authentication,
          'new_auth_token_hash': authDeriv.new_res.authentication,
          'salt': authDeriv.salt,
          'ccrypto_key_public': glbcKeyRing.getPubKey('private').armor(),
          'ccrypto_key_private': glbcKeyRing.exportPrivKey(),
        });
      }).then(function() {
        showMsg('Success! Redirecting home. . .');
        return vars.msgP.then(function() {
          return $timeout(function(){}, 2500);
        });
      });

    },

    startKeyGen: function() {
      $timeout(function() {
        vars.promises.speedLimit.resolve(); 
      }, 7500);

      showMsg('Starting key generation. . . this may take a while. . .');
      glbcKeyRing.createNewCCryptoKey().then(function(r) {
        vars.promises.keyGen.resolve(r);
      });
    },

    noKeyGen: function() {
      $timeout(function() {
        vars.promises.speedLimit.resolve(); 
      }, 5000);
      vars.promises.keyGen.resolve();
    },

    addPassphrase: function(old_password, new_password) {
      showMsg('Starting passphrase derivation. . .');
      var old_salt = Authentication.user_salt;
      // TODO generate a real salt
      var salt = '========================';
      Authentication.user_salt = salt;
      showMsg('Adding salt. . . ');

      var p1 = glbcKeyLib.deriveUserPassword(new_password, salt);
      var p2 = glbcKeyLib.deriveUserPassword(old_password, old_salt);

      $q.all([p1, p2]).then(function(results) {
        showMsg('Derived both passphrases');
        vars.promises.authDerived.resolve({
          'new_res': results[0],
          'old_res': results[1],
          'salt': salt,
        });
      });
    },

    showMsg: showMsg,
  };
}]);
