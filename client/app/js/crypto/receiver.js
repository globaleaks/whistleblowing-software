angular.module('GLBrowserCrypto')
.factory('glbcReceiver', ['$q', '$http', 'pgp', 'glbcKeyRing', 'glbcCipherLib', function($q, $http, pgp, glbcKeyRing, glbcCipherLib) {

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
     * @param {old_key_passphrase: String, new_key_passphrase: String} params
     * @return {Promise}
     **/
    updatePrivateKey: function(params) {
      glbcKeyRing.changeKeyPassphrase(params.old_passphrase, params.new_passphrase);
      return $http.post('/receiver/privkey', {
        'ccrypto_key_private': glbcKeyRing.exportPrivateKey(),
        'ccrypto_key_public': '',
        'auth_token_hash': params.auth_token_hash,
      });
    },

    postKeyPair: function(pair, auth_token_hash) {
      return $http.post('/receiver/privkey', {
        'ccrypto_key_private': pair.ccrypto_key_private.armor(),
        'ccrypto_key_public': pair.ccrypto_key_public.armor(),
        'auth_token_hash': auth_token_hash,
      });
    }
  };
}]);
