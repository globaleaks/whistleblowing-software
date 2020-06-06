/*global Uint8Array, sha256*/

angular.module("GLCrypto", [])
.factory("glbcUtil", function() {
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
.factory("glbcProofOfWork", ["$q", "glbcUtil", "TokenResource", function($q, glbcUtil, TokenResource) {
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
    proofOfWork: function() {
      var deferred = $q.defer();

      new TokenResource().$save(function(token) {
	var i = 0;
        var work = function() {
          var webCrypto = getWebCrypto();
          var toHash = glbcUtil.str2Uint8Array(token.id + i);
          var damnIE;

          var xxx = function (hash) {
            hash = new Uint8Array(hash);
            if (hash[31] === 0) {
              token.answer = i;
              token.$update(function(token) {
                deferred.resolve(token);
              });
            } else {
              i += 1;
              work();
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

	work();
      });

      return deferred.promise;
    }
  };
}])
.factory("glbcToken", ["$timeout", "glbcProofOfWork", function($timeout, glbcProofOfWork) {
  return {
    getToken: function() {
      return glbcProofOfWork.proofOfWork().then(function(token) {
        return $timeout(function(){return token;}, token.min_ttl * 1000);
      });
    }
  };
}]);
