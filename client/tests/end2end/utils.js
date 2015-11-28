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
    return (s.caps_.platform === 'LINUX');
  };

  exports.isOldIE = function() {
    browserName = s.caps_.browserName;
    browserVersion = s.caps_.version;
    return (browserName == 'internet explorer' && browserVersion < 11);
  };
});
