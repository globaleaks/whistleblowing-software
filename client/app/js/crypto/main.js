/* global Uint8Array */

angular.module('GLBrowserCrypto', [])
.factory('pgp', function() {
  return window.openpgp;
})
.factory('glbcUtil', [function() {
  return {
    str2Uint8Array: function(str) {
      var result = new Uint8Array(str.length);
      for (var i = 0; i < str.length; i++) {
        result[i] = str.charCodeAt(i);
      }
      return result;
    }
  };
}])
.factory('glbcProofOfWork', ['$q', 'glbcUtil', function($q, glbcUtil) {
  // proofOfWork return the answer to the proof of work
  // { [challenge string] -> [ answer index] }
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
        var hashme = glbcUtil.str2Uint8Array(str + i);
        var damnIE = getWebCrypto().digest({name: "SHA-256"}, hashme);

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
}])
.factory('glbcKeyLib', ['$q', 'pgp', function($q, pgp) {
    return {
      /**
       * @decription checks to see if passed text is an ascii armored GPG
       * public key. If so, the fnc returns true.
       * @param {String} textInput
       * @return {Bool}
       */
      validPublicKey: function(textInput) {
        if (typeof textInput !== 'string') {
          return false;
        }

        var s = textInput.trim();
        if (s.substr(0, 5) !== '-----') {
          return false;
        }

        // Try to parse the key.
        var result;
        try {
          result = pgp.key.readArmored(s);
        } catch (err) {
          return false;
        }

        // Assert that the parse created no errors.
        if (angular.isDefined(result.err)) {
          return false;
        }

        // Assert that there is only one key in the input.
        if (result.keys.length !== 1) {
          return false;
        }

        var key = result.keys[0];

        // Assert that the key type is not private and the public flag is set.
        if (!key.isPublic() || key.isPrivate()) {
          return false;
        }

        // Verify expiration, revocation, and self sigs.
        if (key.verifyPrimaryKey() !== pgp.enums.keyStatus.valid) {
          return false;
        }

        return true;
      },
    };
}]);
