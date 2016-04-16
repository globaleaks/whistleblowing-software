importScripts('../../components/openpgp/dist/openpgp.worker.min.js');

var sha256 = window.openpgp.crypto.hash.sha256;

var iterateOverSHA = function(seed) {
  var i;
  for (i = 0; i < 1024; i++) {
    var x = sha256(seed + i);

    if (x[31] === 0) {
      postMessage(i);
    }
  }

  postMessage("12345");
};

onmessage = function(e) {
  iterateOverSHA(e.data.pow);
};
