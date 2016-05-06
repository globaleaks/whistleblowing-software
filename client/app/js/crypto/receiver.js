angular.module('GLBrowserCrypto')
.factory('glbcReceiver', ['$q', 'pgp', 'glbcKeyRing', 'glbcCipherLib', function($q, pgp, glbcKeyRing, glbcCipherLib) {

  return {
    
    /**
     * @param {Blob} inputBlob the raw encrypted file returned from an http request
     * @param {pgp.Key} wbPubKey the Whistleblower's public key
     * @return {Promise<Blob>} the decrypted contents of the file.
     */
    decryptAndVerifyFile: function(inputBlob, wbPubKey){
      var deferred = $q.defer();
      glbcCipherLib.createArrayFromBlob(inputBlob).then(function(ciphertext) {
        
        var options = {
          message: pgp.message.read(ciphertext),
          privateKey: glbcKeyRing.getKey(),
          publicKeys: wbPubKey,
          format: 'binary',
        };
        pgp.decrypt(options).then(function(plaintext) {
          var outputBlob = new Blob([plaintext.data], {type: 'application/octet-stream'});
          deferred.resolve(outputBlob);
        });
      });
      return deferred.promise;
    },

    /**
     * @param {pgp.Message} message
     * @param {pgp.Key} wbPubKey the Whistleblower's public key
     */
    decryptAndVerifyAnswers: function(message, wbPubKey) {
      // TODO glbcKeyRing.unlockKeyRing(passphrase);

      var options = {
        message: message,
        privateKey: glbcKeyRing.getKey(),
        publicKeys: wbPubKey,
        format: 'utf8',
      };
      // TODO glbcKeyRing.lockKeyRing(passphrase);
      return pgp.decrypt(options);
    },

    /**
     * @param {String} m the message to encrypt
     * @param {String} recPubKeyArmored the public key of the intended recipient.
     * @return {Promise<String>} a promise for an ASCII armored encrypted message.
     */
    encryptAndSignMessage: function(m, recPubKeyArmored) {
      var recPubKey = pgp.key.readArmored(recPubKeyArmored).keys[0];
      var pubKeys = [recPubKey].concat(glbcKeyRing.getKey().toPublic());
      var options = {
        data: m,
        format: 'utf8',
        privateKey: glbcKeyRing.getKey(),
        publicKeys: pubKeys,
        armored: true,
      };
      return pgp.encrypt(options).then(function(result) {
        return result.data;
      });
    },

    /*
     * @param {Array<String>} msgs a list of ASCII armored openpgp messages
     * @param {Array<pgp.Key>} pubKeys a corresponding list of public keys of the signer
     * @return {Promise<Array<String>>} the list of the decrypted msgs
     */
    decryptAndVerifyMessages: function(msgs, pubKeys) {
      var deferred = $q.defer();

      if (msgs.length !== pubKeys.length) {
        deferred.reject(new Error('mismatched msgs and pubkeys'));
      }

      var decPromises = [];
      for (var i = 0; i < msgs.length; i++) {
        var msg = pgp.message.readArmored(msgs[i]);
        var pubKey = pgp.key.readArmored(pubKeys[i]).keys[0];
        var options = {
          message: msg,
          privateKey: glbcKeyRing.getKey(),
          publicKeys: pubKey,
          format: 'utf8', 
        };
        var promise = pgp.decrypt(options).then(function(result) {
          return result.data; 
        });
        decPromises.push(promise);
      }
      
      return $q.all(decPromises);
    },

  };
}]);
