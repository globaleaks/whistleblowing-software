/* eslint no-console: ["error", { allow: ["error"] }] */

var isBrowserCompatible = function() {
  var crawlers = [
    "Googlebot",
    "Bingbot",
    "Slurp",
    "DuckDuckBot",
    "Baiduspider",
    "YandexBot",
    "Sogou",
    "Exabot",
    "ia_archiver"
  ];

  for (var i=0; i < crawlers.length; crawlers++) {
    if (navigator.userAgent.indexOf(crawlers[i]) !== -1) {
      return true;
    }
  }

  if (typeof window === 'undefined') {
    return false;
  }

  if (!(window.File && window.FileList && window.FileReader)) {
    console.error("GlobaLeaks startup failure: missing support for File API");
    return false;
  }

  if (typeof Blob === 'undefined' || (!Blob.prototype.slice && !Blob.prototype.webkitSlice && !!Blob.prototype.mozSlice)) {
    console.error("GlobaLeaks startup failure: missing support for Blob API");
    return false;
  }

  // Checks related to Webworker compatibility
  if (typeof window.Worker === 'undefined') {
    console.error("GlobaLeaks startup failure: missing Webworker support");
    return false;
  }

  // Check related to WebCrypto compatibility currently disabled as end2end encryption is still not finalized
  if (!(window.crypto && (window.crypto.subtle || window.crypto.webkitSubtle) && window.crypto.getRandomValues) && !(typeof window.msCrypto === 'object' && typeof window.msCrypto.getRandomValues === 'function')) {
    console.error("GlobaLeaks startup failure: missing end-2-end encryption requirements");
    return false;
  }

  return true;
};

function loadjsfile(filepath) {
  var fileref = document.createElement('script');
  fileref.setAttribute("type", "text/javascript");
  fileref.setAttribute("src", filepath);
  if (typeof fileref !== "undefined") {
    document.getElementsByTagName("head")[0].appendChild(fileref);
  }
}
 
function start_globaleaks() {
  if (isBrowserCompatible()) {
    loadjsfile("js/scripts.js");
  } else {
    document.getElementById("BrowserSupported").style.display = "none";
    document.getElementById("BrowserNotSupported").style.display = "block";
  }
}

start_globaleaks();
