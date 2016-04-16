importScripts("../../components/scrypt-async/scrypt-async.min.js");

onmessage = function(e) {
  options = e.data;

  return new Promise(function(resolve, reject) {
    var callback = function(result) {
      postMessage(result);
    };

    scrypt(options.password,
           options.salt,
           options.logN,
           options.r,
           options.dkLen,
           callback,
           options.encoding);
  });
};
