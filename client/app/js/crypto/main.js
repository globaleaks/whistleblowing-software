angular.module('GLBrowserCrypto', [])
.factory('glbcProofOfWork', ['$q', function($q) {
  // proofOfWork return the answer to the proof of work
  // { [challenge string] -> [ answer index] }
  var str2Uint8Array = function(str) {
    var result = new Uint8Array(str.length);
    for (var i = 0; i < str.length; i++) {
      result[i] = str.charCodeAt(i);
    }
    return result;
  };

  var getWebCrypto = function() {
    if (typeof window !== 'undefined') {
      if (window.crypto) {
        return window.crypto.subtle || window.crypto.webkitSubtle;
      }
      if (window.msCrypto) {
        return window.msCrypto.subtle;
      }
    }
  };

  return {
    proofOfWork: function(str) {
      var deferred = $q.defer();

      var work = function(i) {
        var hashme = str2Uint8Array(str + i);
        getWebCrypto().digest({name: "SHA-256"}, hashme).then(function (hash) {
          hash = new Uint8Array(hash);
          if (hash[31] === 0) {
            deferred.resolve(i);
          } else {
            work(i + 1);
          }
        });
      }

      work(0);

      return deferred.promise;
    }
  };
}]);
