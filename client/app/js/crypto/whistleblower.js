angular.module('GLBrowserCrypto')
.factory('glbcWhistleblower', ['$q', 'pgp', 'glbcConstants', 'glbcCipherLib', 'glbcKeyLib', 'glbcKeyRing', function($q, pgp, glbcConstants, glbcCipherLib, glbcKeyLib, glbcKeyRing) {

  var passphrase = null;
  var sess_cckey_pub = null;

  var variables = {
    keyDerived: false,
  };

  return {
    variables: variables,

    unlock: function() {
      return glbcKeyRing.unlockKeyRing(passphrase);
    },

    lock: function() {
      return glbcKeyRing.lockKeyRing(passphrase);
    },

    storePassphrase: function(pass) {
      passphrase = pass;
    },

    clear: function() {
      passphrase = null;
      glbcKeyRing.clear();
    },

    initialize: function(armoredPrivateKey, receivers) {
      glbcKeyRing.initialize(armoredPrivateKey, 'whistleblower');
      if (passphrase === null) {
        throw new Error('WB key passphrase is null');
      }

      receivers = receivers.filter(function(rec) {
        return rec.cckey_pub !== "";
      });
      receivers.forEach(function(rec) {
        glbcKeyRing.addPubKey(rec.id, rec.cckey_pub);
      });

      variables.keyDerived = true;
    },

    /**
     * @param {string} keycode
     * @param {string} salt
     * @param {Submission} submission
     * @return {Promise}
     **/
    deriveKey: function(keycode, salt, submission) {
      var self = this;
      var auth_res;

      return glbcKeyLib.deriveUserPassword(keycode, salt, 14).then(function(result) {
        auth_res = result;
        submission.auth_token_hash = auth_res.authentication;
        return glbcKeyLib.generateCCryptoKey(result.passphrase);
      }).then(function(keys) {
        var armored_priv_key = keys.ccrypto_key_private.armor();
        var success = glbcKeyRing.initialize(armored_priv_key, 'whistleblower');
        if (!success) {
          throw new Error('Key Derivation failed!');
        }

        self.storePassphrase(auth_res.passphrase);
        self.unlock();

        submission.wb_cckey_prv_penc = armored_priv_key;
        submission.wb_cckey_pub = keys.ccrypto_key_public.armor();

        variables.keyDerived = true;
      });
    },

    /**
     * @param {Array<String>} rec_ids
     * @param {Object} submission
     * @return {Promise<Object>}
     **/
    deriveSessionKey: function(rec_ids, submission) {
      var key_opts = {
        userIds: [{name: 'Session Key', email:''}],
        numBits: glbcConstants.ccrypto_key_bits,
        unlocked: true,
      };

      var p = pgp.generateKey(key_opts).then(function(res) {
        submission.sess_cckey_pub = res.publicKeyArmored;

        sess_cckey_pub = pgp.key.readArmored(res.publicKeyArmored).keys[0];

        var pckts = res.key.toPacketlist().write();

        var pubKeys = rec_ids.map(function(uuid) {
          return glbcKeyRing.getPubKey(uuid);
        });

        var options = {
          data: pckts,
          publicKeys: pubKeys,
          armor: true,
          filename: 'session-key'
        };

        // specifically dealloc res
        delete res.key;
        delete res.privateKeyArmored;

        // encrypt the session key
        return pgp.encrypt(options);
      }).then(function(sess_cckey_prv_enc) {
        submission.sess_cckey_prv_enc = sess_cckey_prv_enc.data;
      });

      return p;
    },


   /**
    * encrypts the passed file with the keys of the receivers and returns a
    * new encrypted file with '.pgp' added as the extension.
    * @param {File} file
    * @return {Promise<File>}
    **/
    handleFileEncryption: function(file) {
      return glbcCipherLib.createArrayFromBlob(file).then(function(fileArr) {
        var options = {
          data: fileArr,
          publicKeys: [sess_cckey_pub],
          privateKey: glbcKeyRing.getKey(),
          format: 'binary',
          armor: false,
        };
        return pgp.encrypt(options);
      }).then(function(result) {

        var cipherTextArr = result.message.packets.write();

        // Note application/octet-stream must be explicitly set or the new File
        // will append leading and trailing bytes to the upload.
        var cipherBlob = new Blob([cipherTextArr.buffer], {type:'application/octet-stream'});

        return cipherBlob;
      });
    },


    /**
     * @param {String} jsonAnswers a stringified JSON object containing the msg.
     * @param {Array<String>} receiverIds
     * @param {boolean} sign
     * @return {Promise<String>} the armored pgp message
     */
    encryptAndSignAnswers: function(jsonAnswers, sign) {
      var pubKeys = [sess_cckey_pub, glbcKeyRing.getPubKey('whistleblower')];

      var options = {
        data: jsonAnswers,
        publicKeys: pubKeys,
        format: 'utf8',
        armor: true,
      };

      if (sign) {
        options.privateKey = glbcKeyRing.getKey();
      }

      // TODO unlock keyring
      return pgp.encrypt(options).then(function(cipherMsg) {
        return cipherMsg.data;
      });
    },
  };
}]);
