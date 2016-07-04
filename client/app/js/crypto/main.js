/* global Uint8Array */

angular.module('GLBrowserCrypto', [])
// pgp is a factory for OpenPGP.js for the entire GlobaLeaks frontend.
.factory('pgp', function() {
  return window.openpgp;
})
.factory('glbcUtil', ['pgp', function(pgp) {
  var b64s = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';

  return {

    /**
    * Convert binary array to radix-64. Shamelessly lifted from OpenPGPjs
    * @param {Uint8Array} t Uint8Array to convert
    * @returns {string} radix-64 version of input string
    * @static
    */
    bin2base64: function(t, o) {
      // TODO check btoa alternative
      var a, c, n;
      var r = o ? o : [],
      l = 0,
      s = 0;
      var tl = t.length;

      for (n = 0; n < tl; n++) {
        c = t[n];
        if (s === 0) {
          r.push(b64s.charAt((c >> 2) & 63));
          a = (c & 3) << 4;
        } else if (s === 1) {
          r.push(b64s.charAt((a | (c >> 4) & 15)));
          a = (c & 15) << 2;
        } else if (s === 2) {
          r.push(b64s.charAt(a | ((c >> 6) & 3)));
          l += 1;
          if ((l % 60) === 0) {
            r.push("\n");
          }
          r.push(b64s.charAt(c & 63));
        }
        l += 1;
        if ((l % 60) === 0) {
          r.push("\n");
        }

        s += 1;
        if (s === 3) {
          s = 0;
        }
      }
      if (s > 0) {
        r.push(b64s.charAt(a));
        l += 1;
        if ((l % 60) === 0) {
          r.push("\n");
        }
        r.push('=');
        l += 1;
      }
      if (s === 1) {
        if ((l % 60) === 0) {
          r.push("\n");
        }
        r.push('=');
      }
      if (o)
      {
        return;
      }
      return r.join('');
    },

    /**
     * @param {Uint8Array} bin
     * @return {String} The hex string of the passed array.
     **/
    bin2hex: function(bin) {
      var s = '';
      for (var i = 0; i < bin.length; i++) {
        var out = bin[i].toString(16);
        s += out.length === 2 ? out : '0' + out;
      }
      return s;
    },

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
    },

    generateRandomSalt: function() {
      var salt = pgp.crypto.random.getRandomBytes(16);
      return this.bin2base64(salt);
    },

  };
}])
.factory('glbcProofOfWork', ['$q', 'glbcUtil', function($q, glbcUtil) {
  // proofOfWork returns the answer to the proof of work
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
.factory('glbcKeyLib', ['$q', 'pgp', 'glbcUtil', function($q, pgp, glbcUtil) {
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

    var ccrypto_key_bits = 1024;

    return {
      scrypt: function(data, salt, logN, dkLen) {
        var defer = $q.defer();

        scrypt(data, salt, logN, dkLen, 'utf-8').then(function(stretched) {
          defer.resolve({
            value: data,
            stretched: stretched,
          });
        });

        return defer.promise;
      },

      deriveAuthentication: function(user_password, salt) {
        var h = pgp.crypto.hash.sha512(this.scrypt(user_password, salt, 14, 8));
        return glbcUtil.bin2hex(h);
      },

      /*
       * @param {String} user_password
       * @param {String} salt a 16 byte base64 encoded random salt.
       * @returns {Object} hex passphrase and hex authentication token.
       **/
      deriveUserPassword: function (user_password, salt) {
        var promise = this.scrypt(user_password, salt, 14, 256)
        .then(function(passphrase) {
          var token_hash =  pgp.crypto.hash.sha512(passphrase.stretched);
          return {
            passphrase: glbcUtil.bin2hex(passphrase.stretched),
            authentication: glbcUtil.bin2hex(token_hash),
          };

        });

        return promise;
      },

      generateCCryptoKey: function (passphrase) {
        var deferred = $q.defer();

        var key_options = {
          userIds: [{ name:'Random User', email:'randomuser@globaleaks.org' }],
          passphrase: passphrase,
          numBits: ccrypto_key_bits
        };

        deferred.notify("Handed key gen to PGP. . .");
        pgp.generateKey(key_options).then(function(keyPair) {
          deferred.notify("Key gen returned. . .");
          deferred.resolve({
            ccrypto_key_public: keyPair.key.toPublic(),
            ccrypto_key_private: keyPair.key,
          });
        });

        return deferred.promise;
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

        var res = pgp.key.readArmored(keyStr);
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
     * @param {boolean} sign
     * @return {Promise<String>} a promise for an ASCII armored encrypted message.
     */
    encryptAndSignMessage: function(m, uuid, sign) {
      var pubKeys = [glbcKeyRing.getPubKey(uuid),
                     glbcKeyRing.getPubKey('private')];

      var options = {
        data: m,
        format: 'utf8',
        publicKeys: pubKeys,
        armored: true,
      };

      if (sign) {
        options['privateKey'] = glbcKeyRing.getKey();
      }

      return $q(function(resolve, reject) {
        pgp.encrypt(options).then(function(result) {
          resolve(result.data);
        }, function(err) {
          reject(err);
        });
      });
    },

    /*
     * @param {Array<Object>} msgs a list of {content: 'a', id: 'a23a-' } objs
     * @param {Array<Object>} receivers who have access to the tip.
     * @param {boolean} verify
     * @return {Promise<Array<String>>} the list of the decrypted msg contents
     */
    decryptAndVerifyMessages: function(msgs, receivers, verify) {
      // TODO replace with something more reliable this is shit.
      var author_map = {'Whistleblower': 'whistleblower'};

      angular.forEach(receivers, function(rec) {
        author_map[rec.name] = rec.id;
      });

      angular.forEach(msgs, function(m) {
        m.author_id = author_map[m.author];
      });

      var decPromises = [];

      for (var i = 0; i < msgs.length; i++) {
        var c = pgp.message.readArmored(msgs[i].content);
        var pubKey = glbcKeyRing.getPubKey(msgs[i].author_id);

        var options = {
          message: c,
          privateKey: glbcKeyRing.getKey(),
          format: 'utf8',
        };

        if (verify) {
          options['publicKeys'] = pubKey;
        }

        var promise = pgp.decrypt(options).then(function(result) {
          return result.data;
        });

        decPromises.push(promise);
      }

      return $q.all(decPromises);
    },

    /**
     * @param {String} msg
     * @param {[<Receivers>]} the intended recipients
     * @param {boolean} sign
     * @return {Promise<String>}
     **/
    encryptAndSignComment: function(msg, receivers, sign) {
      var pubKeys = receivers.map(function(rec) {
        return glbcKeyRing.getPubKey(rec.id);
      });

      pubKeys.push(glbcKeyRing.getPubKey('private'));

      var options = {
        data: msg,
        format: 'utf8',
        publicKeys: pubKeys,
        armored: true,
      };

      if (sign) {
        options['privateKey'] = glbcKeyRing.getKey();
      }

      return $q(function(resolve, reject) {
        pgp.encrypt(options).then(function(result) {
          resolve(result.data);
        }, function(err) {
          reject(err);
        });
      });
    },


    /**
     * @param {pgp.Message} message
     * @param {boolean} verify
     * @return {Promise<pgp.Message>}
     */
    decryptAndVerifyAnswers: function(message, verify) {
      var options = {
        message: message,
        format: 'utf8',
        privateKey: glbcKeyRing.getKey(),
      };

      if (verify) {
        options['publicKeys'] = glbcKeyRing.getPubKey('whistleblower');
      }

      return $q(function(resolve, reject) {
        pgp.decrypt(options).then(function(res) {
          resolve(res);   
        }, function(e) {
          reject(e);
        });
      });
    },
 };
}])

// glbcKeyRing holds the private key material of authenticated users. It handles
// all of the cryptographic operations internally so that the rest of the UI
// does not.
.factory('glbcKeyRing', ['$q', 'pgp', 'glbcKeyLib', function($q, pgp, glbcKeyLib) {
  function newRing() {
    return {
      privateKey: null,
      publicKeys: {}, // map of uuids to pgp.Key objects
      _pubKey: null,
      _passphrase: null,
    };
  }

  // keyRing is kept private.
  var keyRing = newRing();
  
  return {
    getKey: function() { return keyRing.privateKey; },

    exportPrivKey: function() {
      if (keyRing.privateKey.isDecrypted) {
        throw new Error("Attempted to export decrypted privateKey");
      }
      return this.getKey().armor();
    },

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
      } else {
        throw new Error('Could not add pubkey to key ring!');
      }
    },

    isInitialized: function() {
      return keyRing.privateKey !== null;
    },

    /**
     * @description intialize validates the passed privateKey and places it in the keyRing.
     * @param {String} armoredPrivKey
     * @param {String} uuid of the receiver or 'whistleblower' if used by the WB
     * @return {Bool}
     */
    initialize: function(armoredPrivKey, uuid) {
      if (!glbcKeyLib.validPrivateKey(armoredPrivKey)) {
        throw new Error('Failed to parse private key!');
      }

      // Parsing the private key here should produce no errors. Once it is no
      // longer needed we will explicity remove references to this key.
      var tmpKeyRef = pgp.key.readArmored(armoredPrivKey).keys[0];

      // TODO assert that the pgp key is locked

      keyRing.privateKey = tmpKeyRef;
      keyRing._pubKey = tmpKeyRef.toPublic();
      tmpKeyRef = null;

      if (angular.isUndefined(uuid)) {
        uuid = 'public';
      }

      keyRing.publicKeys[uuid] = keyRing._pubKey;

      return true;
    },

    createNewCCryptoKey: function() {
      var self = this;
      return glbcKeyLib.generateCCryptoKey().then(function(pair) {
        self.initialize(pair.ccrypto_key_private.armor());
        return pair;
      });
    },

    /**
     * @description encrypts the private key material of the key using the passed
     * password. The primary key and all subkeys are encrypted with the password.
     * @param {String} password
     */
    lockKeyRing: function(scrypt_passphrase) {
       return keyRing.privateKey.encrypt(scrypt_passphrase);
    },

    /**
     * @description decrypts the private key's encrypted key material with the
     * passed password. Returns true if successful.
     * @param {String} password
     */
    unlockKeyRing: function(scrypt_passphrase) {
      return keyRing.privateKey.decrypt(scrypt_passphrase);
    },

    changeKeyPassphrase: function(old_pw, new_pw) {
      this.unlockKeyRing(old_pw);
      this.lockKeyRing(new_pw);
    },

    clear: function() {
      keyRing = newRing();
    }
  };
}]);
