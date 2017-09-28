angular.module('GLBrowserCrypto')
.directive('glbcKeyChangeElem', ['glbcUserKeyGen', function(glbcUserKeyGen) {
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
    scope: {
     glbcKeyChangeElemTitle: '@'
    },
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
      vars.msgQueue.push(msg);
      return $timeout(function() {}, 1000);
    });
    return vars.msgP;
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
        isWizard: false,
        promises: {
          keyGen: $q.defer(),
          authDerived: $q.defer(),
          speedLimit: $q.defer(),
          ready: undefined,
        },
      };

      // Reset msg array without dropping ref
      while(vars.msgQueue.length > 0) { vars.msgQueue.pop(); }

      this.vars = vars;

      var updateBody = {};

      vars.promises.ready = $q.all([
        vars.promises.keyGen.promise,
        vars.promises.authDerived.promise,
        vars.promises.speedLimit.promise,
      ]).then(function(results) {
        glbcKeyRing.lockKeyRing(results[1].new_res.passphrase);

        var authDeriv = results[1];

        updateBody = {
          'old_auth_token_hash': authDeriv.old_res.authentication,
          'new_auth_token_hash': authDeriv.new_res.authentication,
          'cckey_pub': '',
          'cckey_prv_penc': glbcKeyRing.exportPrivKey(),
        };

        if (vars.keyGen) {
          showMsg('Saving the encryption key on the platform');
          updateBody.cckey_pub = glbcKeyRing.getPubKey('private').armor();
        } else {
          showMsg('Updating the encryption key on the platform');
        }

        // TODO NOTE keyRing is only locked for the export
        glbcKeyRing.unlockKeyRing(results[1].new_res.passphrase);

        if (vars.isWizard) {
          return $q.resolve();
        } else {
          return $http.post('/user/passprivkey', updateBody);
        }
      }).then(function() {
        return showMsg('Success!').then(function() {
          return $q.resolve(updateBody);
        });
      }, function(err) {
        return showMsg('Failed').then(function() {
          return $q.reject(err);
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

    wizardStartKeyGen: function() {
      vars.isWizard = true;
      this.startKeyGen();
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
      var p1 = glbcKeyLib.deriveUserPassword(new_password, Authentication.user_salt);
      var p2 = glbcKeyLib.deriveUserPassword(old_password, Authentication.user_salt);

      $q.all([p1, p2]).then(function(results) {
        vars.promises.authDerived.resolve({
          'new_res': results[0],
          'old_res': results[1],
        });
      });
    },

    showMsg: showMsg,
  };
}]);
