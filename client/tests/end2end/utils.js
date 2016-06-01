var fs = require('fs');

exports.vars = {
  'default_password': 'globaleaks',
  'user_password': '"ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#'
};

exports.waitUntilReady = function (elm, timeout) {
  var t = timeout === undefined ? 1000 : timeout;
  browser.wait(function () {
    return elm.isPresent();
  }, t);
  browser.wait(function () {
    return elm.isDisplayed();
  }, t);
};

browser.getCapabilities().then(function(capabilities) {
  exports.testFileUpload = function() {
    var browserName = capabilities.get('browserName').toLowerCase();
    return (['chrome', 'firefox', 'internet explorer', 'edge'].indexOf(browserName) !== -1);
  };

  exports.testFileDownload = function() {
    if (browser.params.testFileDownload) {
      return true;
    }

    // The only browser that does not ask for user interaction is chrome
    var browserName = capabilities.get('browserName').toLowerCase();
    var platform = capabilities.get('platform').toLowerCase();
    return ((['chrome'].indexOf(browserName) !== -1) && platform === 'linux');
  };

  exports.verifyFileDownload = function() {
    return browser.params.verifyFileDownload;
  };
});

exports.waitForUrl = function (url) {
  return browser.wait(function() {
    return browser.getCurrentUrl().then(function(current_url) {
      return (current_url.indexOf(url) !== -1);
    });
  });
};

exports.waitForFile = function (filename, timeout) {    
  var t = timeout === undefined ? 1000 : timeout;    
  return browser.wait(function() {    
    try {   
      var buf = fs.readFileSync(filename);   
      if (buf.length > 5) {    
        return true;
      }   
    } catch(err) {   
      // no-op
      return false;
    } 
  }, t);    
};

exports.emulateUserRefresh = function () {
  return browser.getCurrentUrl().then(function(current_url) {
    current_url = current_url.split('#')[1];
    return browser.setLocation('').then(function() {
      return browser.setLocation(current_url);
    });
  });
};
