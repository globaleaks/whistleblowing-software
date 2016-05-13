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

      var i = 0;

      var xxx = function (hash) {
        hash = new Uint8Array(hash);
        if (hash[31] === 0) {
          deferred.resolve(i);
        } else {
          i += 1;
          work();
        }
      }

      var work = function() {
        var hashme = str2Uint8Array(str + i);
        var damnIE = getWebCrypto().digest({name: "SHA-256"}, hashme);

        if (damnIE.then !== undefined) {
          damnIE.then(xxx);
        } else {
          damnIE.oncomplete = function(r) { xxx(r.target.result); };
        }
      }

      work();

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
      glbcKeyLib.deriveUserPassword("antani", "salt", 24).then(function(result) {
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
                          dkLen,
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
        dkLen: dkLen,
        encoding: encoding
      });

      return defer.promise;
    };

    var ccrypto_key_bits = 4096;

    return {
      scrypt: function(data, salt, logN, dkLen) {
        var defer = $q.defer();

        scrypt(data, salt, logN, dkLen, 'hex').then(function(stretched) {
          defer.resolve({
            value: data,
            stretched: stretched
          });
        });

        return defer.promise;
      },

      deriveAuthentication: function(user_password, salt, M) {
        return this.scrypt(user_password, salt, M, 64);
      },

      derivePassphrase: function(user_password, salt, N) {
        return this.scrypt(user_password, salt, N, 256);
      },

      deriveUserPassword: function (user_password, salt, N) {
        var defer1 = $q.defer();
        var defer2 = $q.defer();
        var result = $q.defer();

        this.derivePassphrase(user_password, salt, N).then(function(passphrase) {
          defer1.resolve(passphrase.stretched);
        });

        this.deriveAuthentication(user_password, salt, N+1).then(function(authentication) {
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
.factory('glbcCipherLib', ['$q', 'pgp', 'glbcKeyLib', 'glbcKeyRing', function($q, pgp, glbcKeyLib, glbcKeyRing) {
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
    },

    /**
     * @param {String} m the message to encrypt
     * @param {String} uuid of the the intended recipient.
     * @return {Promise<String>} a promise for an ASCII armored encrypted message.
     */
    encryptAndSignMessage: function(m, uuid) {

      var pubKeys = [glbcKeyRing.getPubKey(uuid), 
                     glbcKeyRing.getPubKey('private')];

      var options = {
        data: m,
        format: 'utf8',
        privateKey: glbcKeyRing.getKey(),
        publicKeys: pubKeys,
        armored: true,
      };
      return pgp.encrypt(options).then(function(result) {
        return result.data;
      });
    },

    /*
     * @param {Array<Object>} msgs a list of {content: 'a', id: 'a23a-' } objs
     * @return {Promise<Array<String>>} the list of the decrypted msg contents
     */
    decryptAndVerifyMessages: function(msgs) {

      var decPromises = [];
      for (var i = 0; i < msgs.length; i++) {
        var c = pgp.message.readArmored(msgs[i].content);
        // TODO use receiver.id not msg.id..........
        //var pubKey = glbcKeyRing.getPubKey(msgs[i].id);

        var options = {
          message: c,
          privateKey: glbcKeyRing.getKey(),
          // publicKeys: pubKey,
          format: 'utf8', 
        };
        var promise = pgp.decrypt(options).then(function(result) {
          return result.data; 
        });
        decPromises.push(promise);
      }
      
      return $q.all(decPromises);
    },

    /**
     * @param {pgp.Message} message
     * @param {String} wb_uuid of the Whistleblower
     * @return {Promise<pgp.Message>}
     */
    decryptAndVerifyAnswers: function(message, wb_uuid) {
      // TODO glbcKeyRing.unlockKeyRing(passphrase);
      var wbPubKey = glbcKeyRing.getPubKey(wb_uuid);

      var options = {
        message: message,
        format: 'utf8',
        privateKey: glbcKeyRing.getKey(),
        publicKeys: wbPubKey,
      };
      // TODO glbcKeyRing.lockKeyRing(passphrase);
      return pgp.decrypt(options);
    },
 };
}])

// glbcKeyRing holds the private key material of authenticated users. It handles
// all of the cryptographic operations internally so that the rest of the UI 
// does not.
.factory('glbcKeyRing', ['$q', 'pgp', 'glbcKeyLib', function($q, pgp, glbcKeyLib) {
  // keyRing is kept private.
  var keyRing = {
    privateKey: null,
    // publicKeys is a map of uuids to pgp.Key objects.
    publicKeys: {
    
    },
    _pubKey: null,
  };

  return {
    getKey: function() { return keyRing.privateKey; },

    getPubKey: function(s) { 
      if (s === 'private') {
        return keyRing._pubKey;
      }
      if (keyRing.publicKeys.hasOwnProperty(s)) {
        return keyRing.publicKeys[s];
      }
      throw new Error('Key not found in keyring. ' + s);
    },
    
    /**
     * @param {String} uuid 
     * @param {String} armored
     */
    addPubKey: function(uuid, armored) {
      if (glbcKeyLib.validPublicKey(armored)) {
        var key = pgp.key.readArmored(armored).keys[0]; 
        keyRing.publicKeys[uuid] = key;
      }
    },

    /**
     * @description intialize validates the passed privateKey and places it in the keyRing.
     * @param {String} armoredPrivKey
     * @param {String} uuid of the receiver, undefined if the session is a whistleblower
     * @return {Bool}
     */
    initialize: function(armoredPrivKey, uuid) {
      if (!glbcKeyLib.validPrivateKey(armoredPrivKey)) {
        return false;
      }

      // Parsing the private key here should produce no errors. Once it is no
      // longer needed we will explicity remove references to this key.
      var tmpKeyRef = pgp.key.readArmored(armoredPrivKey).keys[0];

      keyRing.privateKey = tmpKeyRef;
      keyRing._pubKey = tmpKeyRef.toPublic();
      tmpKeyRef = null;

      if (typeof uuid === 'string') {
        keyRing.publicKeys[uuid] = keyRing._pubKey;
      }

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

  };
}]);
