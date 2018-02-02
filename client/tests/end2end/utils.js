var fs = require('fs');
var path = require('path');
var crypto = require('crypto');

exports.vars = {
  'user_password': 'ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#',
  'field_types': [
    'Single-line text input',
    'Multi-line text input',
    'Multiple choice input',
    'Selection box',
    'Checkbox',
    'Attachment',
    'Terms of service',
    'Date',
    'Group of questions'
  ],
  'testFileDir': './tests/end2end/files'
};

browser.getCapabilities().then(function(capabilities) {
  var platformName = capabilities.get('platformName') || capabilities.get('platform');
  platformName = platformName.toLowerCase();

  var browserName = capabilities.get('browserName').toLowerCase();

  exports.isMobile = function() {
    return (['android', 'ios'].indexOf(platformName) !== -1);
  };

  exports.testFileUpload = function() {
    if (exports.isMobile()) {
      return false;
    }

    return (['chrome', 'firefox', 'internet explorer', 'microsoftedge'].indexOf(browserName) !== -1);
  };

  exports.testFileDownload = function() {
    if (browser.params.testFileDownload) {
      return true;
    }

    if (exports.isMobile()) {
      return false;
    }

    return ((['chrome'].indexOf(browserName) !== -1) && platformName === 'linux');
  };

  exports.verifyFileDownload = function() {
    return browser.params.verifyFileDownload;
  };

  exports.browserTimeout = function() {
    return 30000;
  };
});

exports.waitUntilPresent = function (locator, timeout) {
  var t = timeout === undefined ? exports.browserTimeout() : timeout;
  browser.waitForAngular();
  return browser.wait(function() {
    return element(locator).isDisplayed().then(function(present) {
      return present;
    }, function() {
      return false;
    });
  }, t);
};

exports.waitUntilClickable = function (locator, timeout) {
  var t = timeout === undefined ? exports.browserTimeout() : timeout;
  var EC = protractor.ExpectedConditions;
  browser.waitForAngular();
  return browser.wait(EC.elementToBeClickable(element(locator)), t);
};

exports.waitForUrl = function (url, timeout) {
  var t = timeout === undefined ? exports.browserTimeout() : timeout;
  browser.waitForAngular();
  return browser.wait(function() {
    return browser.getCurrentUrl().then(function(current_url) {
      current_url = current_url.split('#')[1];
      return (current_url === url);
    });
  }, t);
};

exports.waitForFile = function (filename, timeout) {
  var t = timeout === undefined ? exports.browserTimeout() : timeout;
  browser.waitForAngular();
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

exports.login_admin = function() {
  browser.get('/#/admin');
  element(by.model('loginUsername')).sendKeys('admin');
  element(by.model('loginPassword')).sendKeys(exports.vars['user_password']);
  element(by.id('login-button')).click();
  exports.waitForUrl('/admin/home');
};

exports.login_whistleblower = function(receipt) {
  browser.get('/#/');
  element(by.model('formatted_keycode')).sendKeys(receipt);
  element(by.id('ReceiptButton')).click();
  exports.waitForUrl('/status');
}

exports.login_receiver = function(username, password, url, firstlogin) {
  username = username === undefined ? 'recipient' : username;
  password = password === undefined ? exports.vars['user_password'] : password;
  url = url === undefined ? '/#/login' : url;

  browser.get(url);
  element(by.model('loginUsername')).sendKeys(username);
  element(by.model('loginPassword')).sendKeys(password);
  element(by.id('login-button')).click();

  if (firstlogin) {
    url = '/forcedpasswordchange';
  } else {
    url = url.split('#')[1];
    url = url === '/login' ? '/receiver/tips' : url;
  }

  exports.waitForUrl(url);
};

exports.login_custodian = function(username, password, url, firstlogin) {
  username = username === undefined ? 'Custodian1' : username;
  password = password === undefined ? exports.vars['user_password'] : password;
  url = url === undefined ? '/#/custodian' : url;

  browser.get(url);
  element(by.model('loginUsername')).sendKeys(username);
  element(by.model('loginPassword')).sendKeys(password);
  element(by.id('login-button')).click();

  if (firstlogin) {
    url = '/forcedpasswordchange';
  } else {
    url = url.split('#')[1];
    url = url === '/custodian' ? '/custodian/identityaccessrequests' : url;
  }

  exports.waitForUrl(url);
};

exports.logout = function(redirect_url) {
  redirect_url = redirect_url === undefined ? '/' : redirect_url;
  element(by.id('LogoutLink')).click();
  exports.waitForUrl(redirect_url);
};

exports.clickFirstDisplayed = function(selector) {
  var elems = element.all(selector);

  var displayedElems = elems.filter(function(elem) {
    return elem.isDisplayed();
  });

  displayedElems.first().click();
}

// Utility Functions for handling File operations

exports.makeTestFilePath = function(name) {
  return path.resolve(path.join(exports.vars.testFileDir, name));
};

exports.makeSavedFilePath = function(name) {
  return path.resolve(path.join(browser.params.tmpDir, name));
};

exports.checksum = function(input) {
  return crypto.createHash('sha1').update(input, 'utf8').digest('hex');
};

exports.testFileEquality = function(a_path, b_path) {
  var a_hash = exports.checksum(fs.readFileSync(a_path));
  var b_hash = exports.checksum(fs.readFileSync(b_path));
  expect(a_hash).toEqual(b_hash);
};
