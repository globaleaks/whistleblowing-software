importScripts('openpgp.worker.min.js');

sha256 = window.openpgp.crypto.hash.sha256;

var isAGoodPOW = function(binaryhash) {
  if (binaryhash.charCodeAt(31) == 0) {
    // Note: one ZERO check here, means TWO in the backend
    verification = "";
    for (k = 0; k < 32; k++) {
      verification = (verification + binaryhash.charCodeAt(k).toString(16));
    }
    return true;
  }
  return false;
}

var iterateOverSHA = function(seed) {
  for (i = 0; i < 1024; i++) {
    var x = sha256(seed + i);

    if (isAGoodPOW(x)) {
      postMessage(i);
    }
  }
  postMessage("12345");
}

onmessage = function(e) {
  iterateOverSHA(e.data.pow);
}
