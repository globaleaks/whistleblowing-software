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
    // Test on file upload is currently performed in all browsers;
    return true;
  };

  exports.testFileDownload = function() {
    // Test on file download is currently performed only in chrome and safary;
    // the reason is that except this these, the other browsers asks user interaction;
    var browserName = s.caps_.browserName.toLowerCase();
    return (['chrome', 'safari'].indexOf(browserName) !== -1);
  };

  exports.isOldIE = function() {
    var browserName = s.caps_.browserName.toLowerCase();
    var browserVersion = s.caps_.version;
    return (browserName == 'internet explorer' && browserVersion < 11);
  };

  exports.isChrome = function() {
    var browserName = s.caps_.browserName.toLowerCase();
    return browserName == 'chrome';
  };
});


exports.waitForUrl = function (url) {
  browser.wait(function() {
    return browser.getLocationAbsUrl().then(function(current_url) {
      return (current_url.indexOf(url) !== -1);
    });
  });
}
