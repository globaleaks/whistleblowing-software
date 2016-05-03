angular.module('GLBrowserCrypto', [])
// pgp is a factory for OpenPGP.js for the entire GlobaLeaks frontend. This 
// factory handles the proper initialization of a Web Worker for asynchronous
// operations.
.factory('pgp', function() {
  
  // TODO handle packaging more intelligently, this kicks off yet another xhr request.
  window.openpgp.initWorker({ path:'components/openpgp/dist/openpgp.worker.js' });

  return window.openpgp;
})
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
      };

      work(0);

      return deferred.promise;
    }
  };
}])
.factory('glbcKeyLib', ['$q', 'pgp', function($q, pgp) {
    /*
      The code below could be tested with:

      To following code is the PoC for:
        - authentication secrete derivation from user password
        - pgp passphrase derivation from user password
        - pgp key creation passphrase protected with the passphrase derived by
      glbcKeyLib.deriveUserPassword("antani", "salt").then(function(result) {
        glbcKeyLib.generateCCryptoKey(result.passphrase).then(function(result) {
          console.log(result);
        });
      });

      The following code is the PoC for the clientside keycode generation:
      var keycode = glbcKeyLib.generateKeycode();

      The keycode could be used in place of the "antani" above.
    */

    var scrypt = function(password,
                          salt,
                          logN,
                          encoding) {
      var defer = $q.defer();

      var worker = new Worker('/js/crypto/scrypt-async.worker.js');

      worker.onmessage = function(e) {
        defer.resolve(e.data);
        worker.terminate();
      };

      worker.postMessage({
        password: password,
        salt: salt,
        logN: logN,
        r: 8,
        dkLen: 256,
        encoding: encoding
      });

      return defer.promise;
    };

    var ccrypto_key_bits = 4096;

    var N = 13;
    var M = N + 1;

    return {
      scrypt: function(data, salt, logN) {
        var defer = $q.defer();

        scrypt(data, salt, logN, 'hex').then(function(stretched) {
          defer.resolve({
            value: data,
            stretched: stretched
          });
        });

        return defer.promise;
      },

      deriveAuthentication: function(user_password, salt) {
        return this.scrypt(user_password, salt, M);
      },

      derivePassphrase: function(user_password, salt) {
        return this.scrypt(user_password, salt, N);
      },

      deriveUserPassword: function (user_password, salt) {
        var defer1 = $q.defer();
        var defer2 = $q.defer();
        var result = $q.defer();

        this.derivePassphrase(user_password, salt).then(function(passphrase) {
          defer1.resolve(passphrase.stretched);
        });

        this.deriveAuthentication(user_password, salt).then(function(authentication) {
          defer2.resolve(authentication.stretched);
        });

        $q.all([defer1.promise, defer2.promise]).then(function(values) {
          result.resolve({
            passphrase: values[0],
            authentication: values[1]
          });
        });

        return result.promise;
      },

      generateCCryptoKey: function (passphrase) {
        var defer = $q.defer();

        var key_options = {
          userIds: [{ name:'Random User', email:'randomuser@globaleaks.org' }],
          passphrase: passphrase,
          numBits: ccrypto_key_bits
        };

        pgp.generateKey(key_options).then(function(keyPair) {
          defer.resolve({
            ccrypto_key_public: keyPair.key.toPublic(),
            ccrypto_key_private: keyPair.key,
          });
        });

        return defer.promise;
      },

      /**
       * @return {String} the 16 digit keycode used by whistleblowers in the 
       * frontend.
       */
      generateKeycode: function() {
        var keycode = '';
        for (var i=0; i<16; i++) {
          keycode += pgp.crypto.random.getSecureRandom(0, 9);
        }
        return keycode;
      },

      /**
       * @description ensures that the passed textInput is a valid ascii 
       * armored privateKey. It additionally asserts that the key is passphrase
       * protected.
       * @param {String} textInput
       * @return {Bool}
       */
      validPrivateKey: function(textInput) {
        if (typeof textInput !== 'string') {
          return false;
        }
        var result = pgp.key.readArmored(textInput);
        if (angular.isDefined(result.err) || result.keys.length !== 1) {
          return false;
        }

        var key = result.keys[0];
        if (!key.isPrivate() || key.isPublic()) {
          return false;
        }

        // Verify expiration, revocation, and self sigs.
        if (key.verifyPrimaryKey() !== pgp.enums.keyStatus.valid) {
          return false;
        }

        // TODO check if key secret packets are encrypted.

        return true;
      },

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
        if (!s.startsWith('-----')) {
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
        if (key.isPrivate() || !key.isPublic()) {
          // Woops, the user just pasted a private key. Pray to the almighty
          // browser that a scrubbing GC descends upon the variables.
          // TODO scrub private key material with acid
          key = null;
          result = null;
          return false;
        }

        // Verify expiration, revocation, and self sigs.
        if (key.verifyPrimaryKey() !== pgp.enums.keyStatus.valid) {
          return false;
        }

        return true;
      },
    };
}])
.factory('glbcCipherLib', ['$q', 'pgp', 'glbcKeyLib', function($q, pgp, glbcKeyLib) {
  return {
    /**
     * @description parses the passed public keys and returns a list of 
     * openpgpjs Keys. Note that if there is a problem when parsing a key the 
     * function throws an error.
     * @param {Array<String>} armoredKeys
     * @return {Array<pgp.Key>} 
     */
    loadPublicKeys: function(armoredKeys) {

      var pgpPubKeys = [];
      armoredKeys.forEach(function(keyStr) {
        // If there is any problem with validating the keys generate an error.
        if (!glbcKeyLib.validPublicKey(keyStr)) {
          throw new Error("Attempted to load invalid public key");
        }

        res = pgp.key.readArmored(keyStr);
        if (angular.isDefined(res.err)) {
          // Note only the first error is thrown
          throw res.err[0];
        } else {
          pgpPubKeys.push(res.keys[0]);
        }
      });

      return pgpPubKeys;
    },
  
    /**
     * @param {Blob|File} blob
     * @return {Promise<Uint8Array>} a promise for an array of the bytes in the
     * passed file.
     */
    createArrayFromBlob: function(blob) {
      var deferred = $q.defer();
      var fileReader = new FileReader();
      fileReader.onload = function() {
        var arrayBufferNew = this.result;
        var uintArray = new Uint8Array(arrayBufferNew);
        deferred.resolve(uintArray);
      };
      fileReader.readAsArrayBuffer(blob);
      return deferred.promise;
    }
 };
}])

// glbcKeyRing holds the private key material of authenticated users. It handles
// all of the cryptographic operations internally so that the rest of the UI 
// does not.
.factory('glbcKeyRing', ['$q', 'pgp', 'glbcCipherLib', 'glbcKeyLib', function($q, pgp, glbcCipherLib, glbcKeyLib) {
  // keyRing is kept private.
  var keyRing = {
    privateKey: null,
  };

  return {
    getKey: function() { return keyRing.privateKey; },
    
    /**
     * @description intialize validates the passed privateKey and places it in the keyRing.
     * The validates the key and checks to see if the key's fingerprint equals
     * the fingerprint passed to it.
     * @param {String} armoredPrivKey
     * @param {String} fingerprint
     * @return {Bool}
     */
    initialize: function(armoredPrivKey, fingerprint) {
      if (!glbcKeyLib.validPrivateKey(armoredPrivKey)) {
        return false;
      }

      // Parsing the private key here should produce no errors. Once it is no
      // longer needed we will explicity remove references to this key.
      var tmpKeyRef = pgp.key.readArmored(armoredPrivKey).keys[0];

      if (fingerprint !== tmpKeyRef.primaryKey.fingerprint) {
        tmpKeyRef = null;
        return false;
      }

      keyRing.privateKey = tmpKeyRef;
      tmpKeyRef = null;
      return true;
    },

    /**
     * @description encrypts the private key material of the key using the passed
     * password. The primary key and all subkeys are encrypted with the password.
     * @param {String} password
     * @return {Bool}
     */
    lockKeyRing: function(password) {
       return keyRing.privateKey.encrypt(password);
    },

    /**
     * @description decrypts the private key's encrypted key material with the
     * passed password. Returns true if successful.
     * @param {String} password
     * @return {Bool}
     */
    unlockKeyRing: function(password) {
      return keyRing.privateKey.decrypt(password);
    },


    /**
     * @param {pgp.Message} message
     * @param {String} format
     * @return {Promise<pgp.Message>}
     */
    performDecrypt: function(message, format) {
      if (keyRing.privateKey === null) {
        throw new Error("Keyring not initialized!");
      }
      if (format !== 'binary' && format !== 'utf8') {
        throw new Error("Supplied wrong decrypt format!");
      }
      var options = {
        message: message,
        format: format,
        privateKey: keyRing.privateKey,
        publicKeys: keyRing.privateKey.toPublic(),
      };
      return pgp.decrypt(options);
    },
  };
}]);
