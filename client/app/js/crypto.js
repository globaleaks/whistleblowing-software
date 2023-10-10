GL.factory("glbcUtil", function() {
  return {
    /**
     * @param {String} str
     * @return {Uint8Array} the int representing each 'character'
     **/
    str2Uint8Array: function(str) {
      var result = new Uint8Array(str.length);
      for (var i = 0; i < str.length; i++) {
        result[i] = str.charCodeAt(i);
      }
      return result;
    }
  };
})
.factory("glbcProofOfWork", ["$q", "glbcUtil", function($q, glbcUtil) {
  // proofOfWork return the answer to the proof of work
  // { [challenge string] -> [ answer index] }
  return {
    proofOfWork: function(data) {
      var deferred = $q.defer();

      function work(i) {
        var webCrypto = window.crypto.subtle;
        var toHash = glbcUtil.str2Uint8Array(data + i);
        var digestPremise;

        webCrypto.digest({name: "SHA-256"}, toHash).then(function (hash) {
          hash = new Uint8Array(hash);
          if (hash[31] === 0) {
            deferred.resolve(i);
          } else {
            work(i+1);
          }
        });
      };

      work(0);

      return deferred.promise;
    }
  };
}]);
