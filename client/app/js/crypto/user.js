angular.module('GLBrowserCrypto')
.directive('glbcKeyChangeElem', ['$location', 'Authentication', 'glbcUserKeyGen', function($location, Authentication, glbcUserKeyGen) {
  return {
    restrict: 'A',
    templateUrl: 'views/partials/client_key_gen.html',
    controller: ['$rootScope', '$scope', function($rootScope, $scope) {
      $scope.showSpin = true;
      glbcUserKeyGen.vars.promises.ready.then(function() {
        $scope.showSpin = false;
      }, function(err) {
        $scope.showSpin = true;
        $rootScope.errors.push(err.data);
      });
      $scope.msgs = glbcUserKeyGen.vars.msgQueue;
    }],
  };
}])
// This factory is a state machine it must be instructed to proceed through the
// following steps: setup -> startProcessing -> addPassphrase
// When the Key and Auth tokens have been derived the vars.promises.ready will
// resolve.
.factory('glbcUserKeyGen', ['$q', '$http', '$timeout', 'Authentication', 'glbcUtil', 'glbcKeyLib', 'glbcKeyRing', function($q, $http, $timeout, Authentication, glbcUtil, glbcKeyLib, glbcKeyRing) {
  var vars = {msgQueue: []};

  function showMsg(msg) {
    vars.msgP = vars.msgP.then(function() {
      return $timeout(function() {
        vars.msgQueue.push(msg);
      }, 1000);
    });
  }

  return {
    vars: vars,

    setup: function() {
      vars = {
        msgQueue: vars.msgQueue,
        msgP: $q(function(resolve) {
          resolve();
        }),
        keyGen: false,
        promises: {
          keyGen: $q.defer(),
          authDerived: $q.defer(),
          speedLimit: $q.defer(),
          ready: undefined,
        },
        user_salt: undefined,
      };
      // Reset msg array without dropping ref
      while(vars.msgQueue.length > 0) { vars.msgQueue.pop(); }
      this.vars = vars;

      vars.promises.ready = $q.all([
        vars.promises.keyGen.promise,
        vars.promises.authDerived.promise,
        vars.promises.speedLimit.promise,
      ]).then(function(results) {
        glbcKeyRing.lockKeyRing(results[1].new_res.passphrase);

        var authDeriv = results[1];
        var body = {
          'old_auth_token_hash': authDeriv.old_res.authentication,
          'new_auth_token_hash': authDeriv.new_res.authentication,
          'salt': authDeriv.salt,
          'ccrypto_key_public': '',
          'ccrypto_key_private': glbcKeyRing.exportPrivKey(),
        };

        if (vars.keyGen) {
          showMsg('Saving the encryption keys on the platform');
          body.ccrypto_key_public = glbcKeyRing.getPubKey('private').armor();
        } else {
          showMsg('Updating the encryption key on the platform');
        }

        // TODO NOTE keyRing is only locked for the export
        glbcKeyRing.unlockKeyRing(results[1].new_res.passphrase);

        return $http.post('/user/passprivkey', body);
      }).then(function() {
        Authentication.user_salt = vars.user_salt;
        showMsg('Success!');
        return vars.msgP.then(function() {
          return $timeout(function(){}, 2500);
        });
      }, function(err) {
        showMsg('Failed');
        // Add a timeout to show failures before rejecting promise
        return vars.msgP.then(function() {
          return $timeout(function(){
            return $q.reject(err);
          }, 2500);
        });
      });
    },

    startProcessing: function() {
      if (glbcKeyRing.isInitialized()) {
        this.noKeyGen();
      } else {
        this.startKeyGen();
      }
    },

    startKeyGen: function() {
      vars.keyGen = true;
      $timeout(function() {
        vars.promises.speedLimit.resolve();
      }, 10000);

      showMsg('Generating encryption keys');
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
      var old_salt = Authentication.user_salt;
      vars.user_salt = glbcUtil.generateRandomSalt();

      var p1 = glbcKeyLib.deriveUserPassword(new_password, vars.user_salt);
      var p2 = glbcKeyLib.deriveUserPassword(old_password, old_salt);

      $q.all([p1, p2]).then(function(results) {
        vars.promises.authDerived.resolve({
          'new_res': results[0],
          'old_res': results[1],
          'salt': vars.user_salt,
        });
      });
    },

    showMsg: showMsg,
  };
}]);
