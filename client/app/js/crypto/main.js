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
}]).
.factory('glbcKeyLib', ['$q', function($q) {
    /*
      The code below could be tested with:

      To following code is the PoC for:
        - authentication secrete derivation from user password
        - pgp passphrase derivation from user password
        - pgp key creation passphrase protected with the passphrase derived by
      GLBrowserCrypto.derive_user_password("antani", "salt").then(function(result) {
        GLBrowserCrypto.generate_e2e_key(result.passphrase).then(function(result) {
          console.log(result);
        });
      });

      The following code is the PoC for the clientside keycode generation:
      var keycode = GLBrowserCrypto.generate_keycode();

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

    var e2e_key_bits = 4096;

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

      derive_authentication: function(user_password, salt) {
        return this.scrypt(user_password, salt, M);
      },

      derive_passphrase: function(user_password, salt) {
        return this.scrypt(user_password, salt, N);
      },

      derive_user_password: function (user_password, salt) {
        var defer1 = $q.defer();
        var defer2 = $q.defer();
        var result = $q.defer();

        this.derive_passphrase(user_password, salt).then(function(passphrase) {
          defer1.resolve(passphrase.stretched);
        });

        this.derive_authentication(user_password, salt).then(function(authentication) {
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

      generate_e2e_key: function (passphrase) {
        var defer = $q.defer();

        var key_options = {
          userIds: [{ name:'Random User', email:'randomuser@globaleaks.org' }],
          passphrase: passphrase,
          numBits: e2e_key_bits
        };

        openpgp.generateKey(key_options).then(function(keyPair) {
          defer.resolve({
            e2e_key_pub: keyPair.key.toPublic(),
            e2e_key_prv: keyPair.key,
          });
        });

        return defer.promise;
      },

      // generate_keycode generates the 16 digit keycode used by whistleblowers
      // in the frontend.
      // { () -> string }
      generate_keycode: function() {
        var keycode = '';
        for (var i=0; i<16; i++) {
          keycode += openpgp.crypto.random.getSecureRandom(0, 9);
        }
        return keycode;
      },

      // validatePrivateKey ensures that the passed textInput is a valid ascii
      // armored privateKey. It additionally asserts that the key is passphrase
      // protected.
      // { string -> bool }
      validPrivateKey: function(textInput) {
        if (typeof textInput !== 'string') {
          return false;
        }
        var result = openpgp.key.readArmored(textInput);
        if (angular.isDefined(result.err) || result.keys.length !== 1) {
          return false;
        }

        var key = result.keys[0];
        if (!key.isPrivate() || key.isPublic()) {
          return false;
        }

        // Verify expiration, revocation, and self sigs.
        if (key.verifyPrimaryKey() !== openpgp.enums.keyStatus.valid) {
          return false;
        }

        // TODO check if key secret packets are encrypted.

        return true;
      },

      // validPublicKey checks to see if passed text is an ascii armored GPG
      // public key. If so, the fnc returns true.
      // { string -> bool }
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
          result = openpgp.key.readArmored(s);
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
        if (key.verifyPrimaryKey() !== openpgp.enums.keyStatus.valid) {
          return false;
        }

        return true;
      },

    };
}])

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
      console.log(str);
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
}])

.factory('glbcCipherLib', ['$q', 'glbcKeyLib', function($q, glbcKeyLib) {
  return {
    // loadPublicKeys parses the passed public keys and returns a list of 
    // openpgpjs Keys. Note that if there is a problem when parsing a key the 
    // function throws an error.
    // { [ string... ] -> [ openpgp.Key ] }
    loadPublicKeys: function(armoredKeys) {

      var pgpPubKeys = [];
      armoredKeys.forEach(function(keyStr) {
        // If there is any problem with validating the keys generate an error.
        if (!glbcKeyLib.validPublicKey(keyStr)) {
          throw new Error("Attempted to load invalid public key");
        }

        res = openpgp.key.readArmored(keyStr);
        if (angular.isDefined(res.err)) {
          // Note only the first error is thrown
          throw res.err[0];
        } else {
          pgpPubKeys.push(res.keys[0]);
        }
      });

      return pgpPubKeys;
    },

    // encryptMsg
    // { Uint8Array | string, [ openpgpjs.Key... ] -> { Promise -> openpgpjs.Message } }
    encryptMsg: function(data, pgpPubKeys) {
      var deferred = $q.defer();
      var options = {
        data: data,
        publicKeys: pgpPubKeys,
        armor: false,
        format: 'binary',
      };
      openpgp.encrypt(options).then(function(cipherMsg) {
        deferred.resolve(cipherMsg.message);
      });
      // TODO catch expired keys, formatting errors, etc etc.
      return deferred.promise;
    },

    // encryptArray encrypts the byte array with the list of public passed to 
    // it.
    // { Uint8Array, [ openpgpjs.Key... ] -> { Promise -> Uint8Array } }
    encryptArray: function(uintArr, pgpPubKeys) {
        var deferred = $q.defer();
        
        // TODO fix me fix me!
        self.encryptMsg(uintArr, pgpPubKeys).then(function(cipherMsg) {
          deferred.resolve(cipherMsg.packets.write());
        });

        return deferred.promise;
    },

    // decryptMsg 
    // { openpgp.Message, openpgp.Key -> { Promise -> string } }
    decryptMsg: function(m, privKey) {
      var deferred = $q.defer();

      var options = {
        message: m,
        privateKey: privKey,
        format: 'utf8',
      };
      openpgp.decrypt(options).then(function(plaintext) {
        deferred.resolve(plaintext.data);
      });

      return deferred.promise;
    },

    // decryptArray uses the passed privKey to decrypt the byte array. Note that
    // the privKey's secret material must be decrypted before usage here.
    // {  Uint8Array, openpgp.Key -> { Promise -> Uint8Array } }
    decryptArray: function(ciphertextArr, privKey) {

      var deferred = $q.defer();

      var options = {
        message: openpgp.message.read(ciphertextArr),
        privateKey: privKey,
        format: 'binary',
      };
      openpgp.decrypt(options).then(function(plaintext) {
        deferred.resolve(plaintext.data);
      });

      return deferred.promise;
    },

    // createArrayFromBlob returns a promise for an array of the bytes in the 
    // passed file. It functions on both Blobs and Files, which are blobs.
    // { Blob -> { Promise -> Uint8Array } }
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
.factory('glbcKeyRing', ['glbcCipherLib', 'glbcKeyLib', function(glbcCipherLib, glbcKeyLib) {
  // keyRing is kept private.
  var keyRing = {
    privateKey: null,
  };

  return {
    // intialize validates the passed privateKey and places it in the keyRing.
    // The validates the key and checks to see if the key's fingerprint equals
    // the fingerprint passed to it.
    // { string -> bool }
    initialize: function(armoredPrivKey, fingerprint) {
      if (!glbcKeyLib.validPrivateKey(armoredPrivKey)) {
        return false;
      }

      // Parsing the private key here should produce no errors. Once it is no
      // longer needed we will explicity remove references to this key.
      var tmpKeyRef = openpgp.key.readArmored(armoredPrivKey).keys[0];

      if (fingerprint !== tmpKeyRef.primaryKey.fingerprint) {
        tmpKeyRef = null;
        return false;
      }

      keyRing.privateKey = tmpKeyRef;
      tmpKeyRef = null;
      return true;
    },

    // lockKeyRing encrypts the private key material of the key using the passed
    // password. The primary key and all subkeys are encrypted with the password.
    // { string -> bool }
    lockKeyRing: function(password) {
      var w = true;
      // TODO create issue on GH openpgp js so the library will support:
      // Key.encrypt(passphrase) because it ain't there. TODO
      w = w && keyRing.privateKey.primaryKey.encrypt(password);
      keyRing.privateKey.subKeys.forEach(function(sk) {
        w = w && sk.subKey.encrypt(password);
      });
      return w;
    },

    // unlockKeyRing decrypts the private key's encrypted key material with the
    // passed password. Returns true if succesful.
    // { string -> bool }
    unlockKeyRing: function(password) {
      keyRing.privateKey.decrypt(password);
    },

    // preformDecrypt uses the private key to decrypt the passed array, which
    // should represent the raw bytes of an openpgp Message.
    // { Uint8Array -> { Promise: Uint8Array } }
    performDecrypt: function(ciphertext) {
      if (keyRing.privateKey === null) {
        throw new Error("Keyring not initialized!");
      }
      return glbcCipherLib.decryptMsg(ciphertext, keyRing.privateKey);
    },
  };
}]);
