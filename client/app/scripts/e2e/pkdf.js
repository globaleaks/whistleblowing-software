angular.module('e2e', []).
  factory('pkdf', function() {
    return {
      // //https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto/deriveKey
      //Chrome: 42
      pbkdf2_deriveAKey: function(password, iterations) {
        var salt = "Pick anything you want. This isn't secret.";
        //var iterations = 1000;
        var hash = "SHA-256";

        // First, create a PBKDF2 "key" containing the password
        window.crypto.subtle.importKey(
          "raw",
          this.pbkdf2_stringToArrayBuffer(password),
          {"name": "PBKDF2"},
          false,
          ["deriveKey"]).
            // Derive a key from the password
            then(function(baseKey){
            return window.crypto.subtle.deriveKey(
              {
              "name": "PBKDF2",
              "salt": this.pbkdf2_stringToArrayBuffer(salt),
              "iterations": iterations,
              "hash": hash
            },
            baseKey,
            {"name": "AES-CBC", "length": 128}, // Key we want
            true,                               // Extrable
            ["encrypt", "decrypt"]              // For new key
            );
          }).
            // Export it so we can display it
            then(function(aesKey) {
            return window.crypto.subtle.exportKey("raw", aesKey);
          }).
            // Return it in hex format
            then(function(keyBytes) {
            var hexKey = this.pbkdf2_arrayBufferToHexString(keyBytes);
            return hexKey;
          }).
            catch(function(err) {
            alert("Key derivation failed: " + err.message);
          });
      },


      // Utility functions
      pbkdf2_stringToArrayBuffer: function(string) {
        var encoder = new TextEncoder("utf-8");
        return encoder.encode(string);
      },

      pbkdf2_arrayBufferToHexString: function(arrayBuffer) {
        var byteArray = new Uint8Array(arrayBuffer);
        var hexString = "";
        var nextHexByte;

        for (var i=0; i<byteArray.byteLength; i++) {
          nextHexByte = byteArray[i].toString(16);  // Integer to base 16
          if (nextHexByte.length < 2) {
            nextHexByte = "0" + nextHexByte;     // Otherwise 10 becomes just a instead of 0a
          }
          hexString += nextHexByte;
        }
        return hexString;
      },

      //var scrypt = scrypt_module_factory(33554432*2);
      // rounds must be power of 2
      scrypt_hash: function(password, rounds, scrypt) {
        var utf8_pwd = scrypt.encode_utf8(password);
        var salt = "This is the salt.";

        var bytearray_pwd = scrypt.crypto_scrypt(utf8_pwd, salt, rounds, 8, 1, 16);
        return scrypt.to_hex(bytearray_pwd);
      },

      gl_password: function(password) {
        //return password;

        var scrypt = scrypt_module_factory(33554432);
        var key = this.scrypt_hash(password, 4096, scrypt);
        console.log('gl_password for ', password, ' is ', key);
        return key;
      },

      gl_passphrase: function(passphrase) {
        //return passphrase;
        //16384 is minimum suggested for interactive logins

        var scrypt = scrypt_module_factory(33554432);
        var key = this.scrypt_hash(passphrase, 8192, scrypt);
        console.log('gl_passphrase for ', passphrase, ' is ', key);
        return key;
      }
    }
});
