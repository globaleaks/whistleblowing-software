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

  // Check related to WebCrypto compatibility currently disabled as end2end encryption  is still not finalized
  //if (!(window.crypto && window.crypto.getRandomValues) &&
  //    !(typeof window.msCrypto === 'object' && typeof window.msCrypto.getRandomValues === 'function')) {
  //  console.log("GlobaLeaks startup failure: missing end-2-end encryption requirements");
  //  return false;
  //}

  return true;
};

/*
      function loadjsfile(filepath) {
       var fileref = document.createElement('script');
       fileref.setAttribute("type", "text/javascript");
       fileref.setAttribute("src", filepath);
       if (typeof fileref != "undefined") {
         document.getElementsByTagName("head")[0].appendChild(fileref);
       }
      }

      function start_globaleaks() {
        if (isBrowserCompatible()) {
          loadjsfile("scripts.js");
        } else {
          var error = document.getElementById("error_unsupported_browser");
          error.setAttribute("style", "block");
        }
*/

function httpGetAsync(theUrl, callback)
{
  var xmlHttp = new XMLHttpRequest();
  xmlHttp.onreadystatechange = function() {
  if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
    callback(xmlHttp.responseText);
  }
  xmlHttp.open("GET", theUrl, true); // true for asynchronous
  xmlHttp.send(null);
}

if (isBrowserCompatible()) {
  httpGetAsync("/globaleaks.html", function(data) {
    document.open();
    document.write(data);
    document.close();
  });
} else {
  document.getElementById("LoaderBox").style.display = "none";
  document.getElementById("error_unsupported_browser").style.display = "block";
}
