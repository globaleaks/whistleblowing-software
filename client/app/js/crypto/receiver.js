angular.module('GLBrowserCrypto')
.factory('glbcReceiver', ['$q', '$http', 'pgp', 'glbcKeyRing', 'glbcCipherLib', function($q, $http, pgp, glbcKeyRing, glbcCipherLib) {
  var passphrase = null;

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

    loadSessionKey: function(sess_cckey_prv_enc) {
      var options = {
        message: pgp.message.readArmored(sess_cckey_prv_enc),
        format: 'binary',
        privateKey: glbcKeyRing.getKey(),
      };

      var p = pgp.decrypt(options).then(function(res) {
        var packetlist = new pgp.packet.List();
        packetlist.read(res.data);

        var keyIndex = packetlist.indexOfTag(pgp.enums.packet.secretKey,
                                             pgp.enums.packet.userid,
                                             pgp.enums.packet.signature,
                                             pgp.enums.packet.secretSubkey,
                                             pgp.enums.packet.signature);

        // assert that the key is in the right format
        if (keyIndex.length !== 5) {
          throw "Passed pgp session key is in the wrong format";
        }

        for (var i = 0; i < keyIndex.length; i++) {
          if (keyIndex[i] !== i) {
            throw "Key elements are out of order"; // Throw because something funky is going on.
          }
        }

        tip_session_key = new pgp.key.Key(packetlist);
        glbcKeyRing.setSessionKey(tip_session_key);
      }).catch(function(e) {
        // TODO(handle-me) exceptions thrown in the then are dropped here.
        console.log(e);
        throw e;
      });

      return p;
    },

    clear: function() {
      passphrase = null;
      glbcKeyRing.clear();
    },

    /**
     * @param {Blob} inputBlob the raw encrypted file returned from an http request
     * @param {boolean} verify
     * @return {Promise<Blob>} the decrypted contents of the file.
     */
    decryptAndVerifyFile: function(inputBlob, verify) {
      var deferred = $q.defer();
      glbcCipherLib.createArrayFromBlob(inputBlob).then(function(ciphertext) {
        var options = {
          message: pgp.message.read(ciphertext),
          privateKey: glbcKeyRing.getSessionKey(),
          format: 'binary',
        };

        if (verify) {
          options['publicKeys'] = glbcKeyRing.getPubKey('whistleblower');
        }

        pgp.decrypt(options).then(function(plaintext) {
          var outputBlob = new Blob([plaintext.data], {type: 'application/octet-stream'});
          deferred.resolve(outputBlob);
        }, function(err) {
          deferred.reject(err);
        });
      });
      return deferred.promise;
    },
  };
}]);
