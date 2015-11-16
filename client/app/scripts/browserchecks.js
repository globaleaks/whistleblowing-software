var isBrowserCompatible = function() {
  if (typeof window === 'undefined') {
    return false;
  }

 // Checks related to FileAPI compatibility
 if(typeof File === 'undefined' ||
    typeof Blob === 'undefined' ||
    typeof FileList === 'undefined' ||
    (!Blob.prototype.slice && !Blob.prototype.webkitSlice && !Blob.prototype.mozSlice)){

    console.log("GlobaLeaks startup failure: missing requirements for Flow.js");
    return false;
  }

  // Checks related to Webworker compatibility
  if (typeof window.Worker === 'undefined') {
    console.log("GlobaLeaks startup failure: missing Webworker support");
    return false;
  }

  // Check related to WebCrypto compatibility
  if (!(window.crypto && window.crypto.getRandomValues) &&
      !(typeof window.msCrypto === 'object' && typeof window.msCrypto.getRandomValues === 'function')) {
    console.log("GlobaLeaks startup failure: missing end-2-end encryption requirements");
    return false;
  }

  return true;
};
