var fs = require('fs');

exports.vars = {
  'default_password': 'globaleaks',
  'user_password': 'ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#',
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

exports.waitUntilReady = function (elm, timeout) {
  var t = timeout === undefined ? 1000 : timeout;
  browser.wait(function () {
    return elm.isPresent();
  }, t);
  browser.wait(function () {
    return elm.isDisplayed();
  }, t);
};

exports.waitForUrl = function (url) {
  return browser.wait(function() {
    return browser.getCurrentUrl().then(function(current_url) {
      current_url = current_url.split('#')[1];
      return (current_url === url);
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

exports.login_whistleblower = function(receipt) {
  return protractor.promise.controlFlow().execute(function() {
    var deferred = protractor.promise.defer();

    browser.get('/#/');

    element(by.model('formatted_keycode')).sendKeys(receipt).then(function() {
      element(by.id('ReceiptButton')).click().then(function() {
        exports.waitForUrl('/status');
        deferred.fulfill();
      });
    });

    return deferred.promise;
  });
};

exports.login_receiver = function(username, password, url) {
  url = url === undefined ? '/#/login' : url;

  return protractor.promise.controlFlow().execute(function() {
    var deferred = protractor.promise.defer();

    browser.get(url);

    element(by.model('loginUsername')).element(by.xpath(".//*[text()='" + username + "']")).click().then(function() {
      element(by.model('loginPassword')).sendKeys(password).then(function() {
        element(by.xpath('//button[contains(., "Log in")]')).click().then(function() {
          url = url.split('#')[1];
          exports.waitForUrl(url === '/login' ? '/receiver/tips' : url);
          deferred.fulfill();
        });
      });
    });

    return deferred.promise;
  });
};

exports.logout = function(redirect_url) {
  redirect_url = redirect_url === undefined ? '/' : redirect_url;

  element(by.id('LogoutLink')).click().then(function() {
    exports.waitForUrl(redirect_url);
  });
};
