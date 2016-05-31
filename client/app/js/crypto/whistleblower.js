angular.module('GLBrowserCrypto')
.factory('glbcWhistleblower', ['$q', 'pgp', 'glbcCipherLib', 'glbcKeyLib', 'glbcKeyRing', function($q, pgp, glbcCipherLib, glbcKeyLib, glbcKeyRing) {

  var variables = {
    keyDerived: false,
    passphrase: null,
  };

  return {
    variables: variables,

    storePassphrase: function(passphrase) {
      if (variables.passphrase !== null) {
        throw new Error('Overwriting a WBs passphrase');
      }
      variables.passphrase = passphrase;
    },

    initializeKey: function(armoredPrivateKey) {
      glbcKeyRing.initialize(armoredPrivateKey, 'whistleblower');
      if (variables.passphrase === null) {
        throw new Error('WB key passphrase is null');
      }
      return glbcKeyRing.unlockKeyRing(variables.passphrase);
    },

    /**
     * @param {string} keycode
     * @param {string} salt
     * @param {Submission} submission
     * @return {Promise}
     **/
    deriveKey: function(keycode, salt, submission) {
      return glbcKeyLib.deriveUserPassword(keycode, salt, 14).then(function(result) {
        submission.receipt_hash = result.authentication;
        glbcKeyLib.generateCCryptoKey(result.passphrase).then(function(keys) {
          var armored_priv_key = keys.ccrypto_key_private.armor();
          var success = glbcKeyRing.initialize(armored_priv_key, 'whistleblower');
          if (!success) {
            throw new Error('Key Derivation failed!');
          }
          // TODO remove unlock
          glbcKeyRing.unlockKeyRing(result.passphrase);

          submission.ccrypto_key_private = armored_priv_key;
          submission.ccrypto_key_public = keys.ccrypto_key_public.armor();

          variables.keyDerived = true;
        });
      });
    },

    /** 
    * encrypts the passed file with the keys of the receivers and returns a 
    * new encrypted file with '.pgp' added as the extension.
    * @param {File} file 
    * @param {Array<Object>} receivers 
    * @return {Promise<File>}
    */
    handleFileEncryption: function(file, receivers) {
      var deferred = $q.defer();

      glbcCipherLib.createArrayFromBlob(file).then(function(fileArr) {
        // Get the public keys for each receiver
        // TODO TODO TODO Remove temp public key
        var pubKeyStrs = receivers.map(function(rec) { return rec.ccrypto_key_public; });
        // TODO TODO TODO
        var pubKeys;
        try {
          pubKeys = glbcCipherLib.loadPublicKeys(pubKeyStrs);
        } catch(err) {
          deferred.reject(err);
          return;
        }
        
        var options = {
          data: fileArr,
          publicKeys: pubKeys,
          privateKey: glbcKeyRing.getKey(),
          format: 'binary',
          armor: false,
        };
        return pgp.encrypt(options);
      }).then(function(result) {

        var cipherTextArr = result.message.packets.write();

        // Note application/octet-stream must be explicitly set or the new File
        // will append leading and trailing bytes to the upload.
        var cipherBlob = new Blob([cipherTextArr.buffer], {type:'application/octet-stream'});
        var encFile = new File([cipherBlob], file.name+'.pgp');
        deferred.resolve(encFile);
      });
      return deferred.promise;
    },


    /**
     * @param {String} jsonAnswers a stringified JSON object containing the msg.
     * @param {Array<String>} receiverIds 
     * @return {Promise<String>} the armored pgp message
     */
    encryptAndSignAnswers: function(jsonAnswers, receiverIds) {

      var pubKeys = receiverIds.map(function(id) {
        return glbcKeyRing.getPubKey(id); 
      });
      pubKeys.push(glbcKeyRing.getPubKey('whistleblower'));

      var options = {
        data: jsonAnswers,
        privateKey: glbcKeyRing.getKey(),
        publicKeys: pubKeys,
        format: 'utf8',
        armor: true,
      };

      // TODO unlock keyring
      return pgp.encrypt(options).then(function(cipherMsg) {
        return cipherMsg.data;
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
