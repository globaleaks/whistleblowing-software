exports.waitUntilReady = function (elm, timeout) {
   var timeout = timeout == undefined ? 1000 : timeout;
   browser.wait(function () {
      return elm.isPresent();
   }, timeout);
   browser.wait(function () {
      return elm.isDisplayed();
   }, timeout);
};


browser.getCapabilities().then(function(s) {
  exports.testFileUpload = function() {
    var browserName = s.caps_.browserName.toLowerCase();
    return (['chrome', 'firefox', 'internet explorer', 'edge'].indexOf(browserName) !== -1);
  };

  exports.testFileDownload = function() {
    // Test on file upload is currently performed in all browsers;
    return true;
  };

  exports.isOldIE = function() {
    var browserName = s.caps_.browserName.toLowerCase();
    var browserVersion = s.caps_.version;
    return (browserName == 'internet explorer' && browserVersion < 11);
  };
});


exports.waitForUrl = function (url) {
  browser.wait(function() {
    return browser.getLocationAbsUrl().then(function(current_url) {
      return (current_url.indexOf(url) !== -1);
    });
  });
}
