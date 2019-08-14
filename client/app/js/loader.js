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

  if (typeof window === "undefined") {
    return false;
  }

  if (!(window.File && window.FileList && window.FileReader)) {
    return false;
  }

  if (typeof Blob === "undefined" ||
      (!Blob.prototype.slice && !Blob.prototype.webkitSlice && !!Blob.prototype.mozSlice)) {
    return false;
  }

  return true;
};

if (!isBrowserCompatible()) {
  document.getElementById("BrowserSupported").style.display = "none";
  document.getElementById("BrowserNotSupported").style.display = "block";
} else {
  var fileref = document.createElement("script");
  fileref.setAttribute("type", "text/javascript");
  fileref.setAttribute("src", "js/scripts.js");
  document.getElementsByTagName("head")[0].appendChild(fileref);
}
