var fs = require('fs');
var path = require('path');
var crypto = require('crypto');

exports.vars = {
  'default_password': 'globaleaks',
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

exports.browserTimeout = function() {
  return 30000;
};

exports.waitUntilPresent = function (locator, timeout) {
  var t = timeout === undefined ? exports.browserTimeout() : timeout;
  return browser.wait(function() {
    return element(locator).isDisplayed().then(function(present) {
      return present;
    }, function() {
      return false;
    });
  }, t);
};

exports.waitForUrl = function (url, timeout) {
  var t = timeout === undefined ? exports.browserTimeout() : timeout;
  return browser.wait(function() {
    return browser.getCurrentUrl().then(function(current_url) {
      current_url = current_url.split('#')[1];
      return (current_url === url);
    });
  }, t);
};

exports.waitForFile = function (filename, timeout) {
  var t = timeout === undefined ? exports.browserTimeout() : timeout;
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
  browser.getCurrentUrl().then(function(current_url) {
    current_url = current_url.split('#')[1];
    browser.setLocation('');
    browser.setLocation(current_url);
  });
};

exports.login_admin = function() {
  browser.get('/#/admin');
  element(by.model('loginUsername')).sendKeys('admin');
  element(by.model('loginPassword')).sendKeys(exports.vars['user_password']);
  element(by.id('login-button')).click();
  exports.waitForUrl('/admin/landing');
};

exports.login_whistleblower = function(receipt) {
  browser.get('/#/');
  element(by.model('formatted_keycode')).sendKeys(receipt);
  element(by.id('ReceiptButton')).click();
  exports.waitForUrl('/status');
}

exports.login_receiver = function(username, password, url, firstlogin) {
  username = username === undefined ? 'Recipient1' : username;
  password = password === undefined ? exports.vars['user_password'] : password;
  url = url === undefined ? '/#/login' : url;

  browser.get(url);
  element(by.model('loginUsername')).element(by.xpath(".//*[text()='" + username + "']")).click();
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

exports.TestFileEquality = function(a_path, b_path) {
  var a_hash = exports.checksum(fs.readFileSync(a_path));
  var b_hash = exports.checksum(fs.readFileSync(b_path));
  expect(a_hash).toEqual(b_hash);
};
