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
  var getWebCrypto = function() {
    if (typeof window === "undefined" || !window.isSecureContext) {
      return;
    }

    if (window.crypto) {
      return window.crypto.subtle || window.crypto.webkitSubtle;
    } else if (window.msCrypto) {
      return window.msCrypto.subtle;
    }
  };

  return {
    proofOfWork: function(data) {
      var deferred = $q.defer();

      var work = function(i) {
        var webCrypto = getWebCrypto();
        var toHash = glbcUtil.str2Uint8Array(data + i);
        var damnIE;

        var xxx = function (hash) {
          hash = new Uint8Array(hash);
          if (hash[31] === 0) {
            deferred.resolve(i);
          } else {
            work(i+1);
          }
        };

        if (webCrypto) {
          damnIE = webCrypto.digest({name: "SHA-256"}, toHash);
        } else {
          damnIE = $q.resolve(sha256(toHash));
        }

        if (typeof damnIE.then !== "undefined") {
          damnIE.then(xxx);
        } else {
          damnIE.oncomplete = function(r) { xxx(r.target.result); };
        }
      };

      work(0);

      return deferred.promise;
    }
  };
}]);
