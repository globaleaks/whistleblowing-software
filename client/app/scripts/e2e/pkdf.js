// //https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto/deriveKey
//Chrome: 42
function pbkdf2_deriveAKey(password, iterations) {
  var salt = "Pick anything you want. This isn't secret.";
  //var iterations = 1000;
  var hash = "SHA-256";

  // First, create a PBKDF2 "key" containing the password
  window.crypto.subtle.importKey(
    "raw",
    pbkdf2_stringToArrayBuffer(password),
    {"name": "PBKDF2"},
    false,
    ["deriveKey"]).
      // Derive a key from the password
      then(function(baseKey){
      return window.crypto.subtle.deriveKey(
        {
        "name": "PBKDF2",
        "salt": pbkdf2_stringToArrayBuffer(salt),
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
      var hexKey = pbkdf2_arrayBufferToHexString(keyBytes);
      return hexKey;
    }).
      catch(function(err) {
      alert("Key derivation failed: " + err.message);
    });
}


// Utility functions
function pbkdf2_stringToArrayBuffer(string) {
  var encoder = new TextEncoder("utf-8");
  return encoder.encode(string);
}

function pbkdf2_arrayBufferToHexString(arrayBuffer) {
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
}

//var scrypt = scrypt_module_factory(33554432*2);
// rounds must be power of 2
function scrypt_hash(password, rounds, scrypt) {
  var utf8_pwd = scrypt.encode_utf8(password);
  var salt = "This is the salt.";

  var bytearray_pwd = scrypt.crypto_scrypt(utf8_pwd, salt, rounds, 8, 1, 16);
  return scrypt.to_hex(bytearray_pwd);
}

function gl_password(password) {
  //return password;

  var scrypt = scrypt_module_factory(33554432);
  var key = scrypt_hash(password, 4096, scrypt);
  console.log('gl_password for ', password, ' is ', key);
  return key;
}
function gl_passphrase(passphrase) {
  //return passphrase;
  //16384 is minimum suggested for interactive logins

  var scrypt = scrypt_module_factory(33554432);
  var key = scrypt_hash(passphrase, 8192, scrypt);
  console.log('gl_passphrase for ', passphrase, ' is ', key);
  return key;
}
