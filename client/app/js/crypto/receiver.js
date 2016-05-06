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

  };
}]);
