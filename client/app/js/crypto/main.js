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
    }

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
        }

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
          console.log(err);
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

        return true;
      },

    };
}])
.factory('glbcCipherLib', ['$q', 'glbcKeyLib', function($q, glbcKeyLib){
  return {
    
    // loadPublicKeys parses the passed public keys and returns a list of openpgpjs Keys
    // Note that if there is a problem when parsing a key the function throws an error.
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

    // encryptArray encrypts the byte array with the list of public passed to it.
    // { (Uint8Array, [ openpgpjs.Key... ]) --> Uint8Array }
    encryptArray: function(uintArr, pgpPubKeys) {
      // TODO assert that all pubkeys are actually there.
      var deferred = $q.defer();
      var options = {
        data: uintArr,
        publicKeys: pgpPubKeys,
        armor: false,
        format: 'binary',
      };
      openpgp.encrypt(options).then(function(ciphertext) {
        deferred.resolve(ciphertext.message.packets.write()); 
      });
      // TODO catch expired keys, formatting errors, etc etc.
      return deferred.promise;
    },
    
    // decryptArray uses the passed privKey to decrypt the byte array. Note that 
    // the privKey's secret material must be decrypted before usage here.
    // { ( Uint8Array, openpgp.Key, string ) -> { Promise -> Uint8Array } }
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

  };
}])
// glbcKeyRing holds the private key material of authenticated users. It handles
// all of the cryptographic operations internally so that the rest of the UI does 
// not.
.factory('glbcKeyRing', ['glbcKeyLib', function(glbcKeyLib) {
    // keyring is kept private.
    var keyring = {
      privateKey: null,
    };

    return {
      // intialize validates the passed privateKey and places it in the keyring.
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
        
        keyring.privateKey = tmpKeyRef; 
        tmpKeyRef = null;
        return true;
      },

    };
}]);
