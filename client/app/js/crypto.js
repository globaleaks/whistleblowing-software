/* global Uint8Array */

angular.module('GLBrowserCrypto', [])
.factory('sha256', function() {
  return window.sha256;
})
.factory('glbcUtil', function() {
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
.factory('glbcProofOfWork', ['$q', 'sha256', 'glbcUtil', function($q, sha256, glbcUtil) {
  // proofOfWork return the answer to the proof of work
  // { [challenge string] -> [ answer index] }
  var getWebCrypto = function() {
    if (typeof window === 'undefined') {
      return;
    }

    if (window.crypto) {
      return window.crypto.subtle || window.crypto.webkitSubtle;
    } else if (window.msCrypto) {
      return window.msCrypto.subtle;
    }
  };

  return {
    proofOfWork: function(str) {
      var deferred = $q.defer();

      var i = 0;

      var xxx = function (hash) {
        hash = new Uint8Array(hash);
        if (hash[31] === 0) {
          deferred.resolve(i);
        } else {
          i += 1;
          work();
        }
      };

      var work = function() {
        var webCrypto = getWebCrypto();
        var toHash = glbcUtil.str2Uint8Array(str + i);
        var damnIE;

        if (webCrypto) {
            damnIE = webCrypto.digest({name: "SHA-256"}, toHash);
        } else {
            damnIE = $q.resolve(sha256(toHash));
        }

        if (damnIE.then !== undefined) {
          damnIE.then(xxx);
        } else {
          damnIE.oncomplete = function(r) { xxx(r.target.result); };
        }
      };

      work();

      return deferred.promise;
    }
  };
}]);
