angular.module('GLBrowserCrypto', []).
  factory('GLBrowserCrypto', ['$q', function($q) {
    /*
      The code below could be tested with:

      To following code is the PoC for:
        - authentication secrete derivation from user password
        - pgp passphrase derivation from user password
        - pgp key creation passphrase protected with the passphrase derived by
      GLBrowserCrypto.derivate_user_password("antani", "salt").then(function(result) {
        GLBrowserCrypto.generate_e2e_key(result.passphrase).then(function(result) {
          console.log(result);
        });
      });

      The following code is the PoC for the clientside keycode generation:
      var keycode = GLBrowserCrypto.generate_keycode();

      The keycode could be used in place of the "antani" above.
    */

    var scrypt = function(password,
                          salt,
                          logN,
                          encoding) {
      var defer = $q.defer();

      var worker = new Worker('/js/crypto/scrypt-async.worker.js');

      worker.onmessage = function(e) {
        defer.resolve(e.data);
        worker.terminate();
      };

      worker.postMessage({
        password: password,
        salt: salt,
        logN: logN,
        r: 8,
        dkLen: 256,
        encoding: encoding
      });

      return defer.promise;
    }

    var e2e_key_bits = 4096;

    var N = 13;
    var M = N + 1;

    return {
      scrypt: function(data, salt, logN) {
        var defer = $q.defer();

        scrypt(data, salt, logN, 'hex').then(function(stretched) {
          defer.resolve({
            value: data,
            stretched: stretched
          });
        });

        return defer.promise;
      },

      derivate_authentication: function(user_password, salt) {
        return this.scrypt(user_password, salt, M);
      },

      derivate_passphrase: function(user_password, salt) {
        return this.scrypt(user_password, salt, N);
      },

      derivate_user_password: function (user_password, salt) {
        var defer1 = $q.defer();
        var defer2 = $q.defer();
        var result = $q.defer();

        this.derivate_passphrase(user_password, salt).then(function(passphrase) {
          defer1.resolve(passphrase.stretched);
        });

        this.derivate_authentication(user_password, salt).then(function(authentication) {
          defer2.resolve(authentication.stretched);
        });

        $q.all([defer1.promise, defer2.promise]).then(function(values) {
          result.resolve({
            passphrase: values[0],
            authentication: values[1]
          });
        });

        return result.promise;
      },
      generate_e2e_key: function (passphrase) {
        var defer = $q.defer();

        var key_options = {
          userIds: [{ name:'Random User', email:'randomuser@globaleaks.org' }],
          passphrase: passphrase,
          numBits: e2e_key_bits
        }

        var key = openpgp.generateKey(key_options).then(function(keyPair) {
          defer.resolve({
            e2e_key_pub: keyPair.publicKeyArmored,
            e2e_key_prv: keyPair.privateKeyArmored
          });
        });

        return defer.promise;
      },
      generate_keycode: function() {
        var keycode = '';
        for (var i=0; i<16; i++) {
          keycode += openpgp.crypto.random.getSecureRandom(0, 9);
        }
        return keycode;
      }
    }
}]);
