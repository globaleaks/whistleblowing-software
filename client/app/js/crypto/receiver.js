angular.module('GLBrowserCrypto')
.factory('glbcReceiver', ['$q', '$http', 'pgp', 'glbcKeyRing', 'glbcCipherLib', function($q, $http, pgp, glbcKeyRing, glbcCipherLib) {
  passphrase = null;

  return {
    storePassphrase: function(pass) {
      passphrase = pass;
    },

    unlock: function() {
      return glbcKeyRing.unlockKeyRing(passphrase);
    },

    lock: function() {
      return glbcKeyRing.lockKeyRing(passphrase);
    },

    clear: function() {
      passphrase = null;
      glbcKeyRing.clear();
    },

    /**
     * @param {Blob} inputBlob the raw encrypted file returned from an http request
     * @return {Promise<Blob>} the decrypted contents of the file.
     */
    decryptAndVerifyFile: function(inputBlob, verify) {
      var deferred = $q.defer();
      glbcCipherLib.createArrayFromBlob(inputBlob).then(function(ciphertext) {
        var options = {
          message: pgp.message.read(ciphertext),
          privateKey: glbcKeyRing.getKey(),
          format: 'binary',
        };

        if (verify) {
          options['publicKeys'] = glbcKeyRing.getPubKey('whistleblower');
        }

        pgp.decrypt(options).then(function(plaintext) {
          var outputBlob = new Blob([plaintext.data], {type: 'application/octet-stream'});
          deferred.resolve(outputBlob);
        });
      });
      return deferred.promise;
    },
  };
}]);
