var fs = require('fs');

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
  ]
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

function genericWait(waitFn, timeout) {
  var t = timeout === undefined ? 1000 : timeout;
  return browser.wait(waitFn, t);
}

exports.waitUntilEnabled = function (elm, timeout) {
  genericWait(function() {
    return elm.isEnabled();
  }, timeout);
};

exports.waitUntilClickable = function (elm, timeout) {
  var EC = protractor.ExpectedConditions;
  genericWait(EC.elementToBeClickable(elm), timeout);
};

exports.waitUntilHidden = function(elem, timeout) {
  if (elem.isPresent()) {
    var EC = protractor.ExpectedConditions;
    genericWait(EC.invisibilityOf(elem), timeout);
  } else {
    return; // The element is not on the page.
  }
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

exports.waitForUrl = function (url) {
  return browser.wait(function() {
    return browser.getCurrentUrl().then(function(current_url) {
      current_url = current_url.split('#')[1];
      return (current_url === url);
    });
  }, 10000);
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
};

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
