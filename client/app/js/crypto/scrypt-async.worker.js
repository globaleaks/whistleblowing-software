/* global scrypt */

importScripts("lib/scrypt-async.min.js");

onmessage = function(e) {
  var options = e.data;

  var callback = function(result) {
    postMessage(result);
  };

  scrypt(options.password,
         options.salt,
         options.logN,
         options.r,
         options.dkLen,
         0,
         callback,
         options.encoding);
};
