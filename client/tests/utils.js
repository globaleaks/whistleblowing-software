var fs = require("fs");
var path = require("path");
var crypto = require("crypto");

exports.vars = {
  "user_password": "ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#",
  "field_types": [
    "Single-line text input",
    "Multi-line text input",
    "Selection box",
    "Checkbox",
    "Attachment",
    "Terms of service",
    "Date",
    "Group of questions"
  ]
};

browser.getCapabilities().then(function(capabilities) {
  var platformName = capabilities.get("platformName") || capabilities.get("platform");
  platformName = platformName.toLowerCase();

  var browserName = capabilities.get("browserName").toLowerCase();

  exports.isMobile = function() {
    return (["android", "ios"].indexOf(platformName) !== -1);
  };

  exports.testFileUpload = function() {
    if (exports.isMobile()) {
      return false;
    }

    return (["chrome", "firefox", "internet explorer", "microsoftedge"].indexOf(browserName) !== -1);
  };

  exports.testFileDownload = function() {
    if (browser.params.testFileDownload) {
      return true;
    }

    if (exports.isMobile()) {
      return false;
    }

    return ((["chrome"].indexOf(browserName) !== -1) && platformName === "linux");
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
  return browser.wait(EC.elementToBeClickable(element(locator)), t);
};

exports.waitForUrl = async function (url, timeout) {
  var t = timeout === undefined ? exports.browserTimeout() : timeout;
  return browser.wait(function() {
    return browser.getCurrentUrl().then(function(current_url) {
      current_url = current_url.split("#")[1];
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

exports.login_whistleblower = async function(receipt) {
  await browser.get("/#/");
  await element(by.model("formatted_receipt")).sendKeys(receipt);
  await element(by.id("ReceiptButton")).click();
  await browser.gl.utils.waitUntilPresent(by.id("TipInfoBox"));
};

exports.login_admin = async function(username, password, url, firstlogin) {
  username = username === undefined ? "admin" : username;
  password = password === undefined ? exports.vars["user_password"] : password;
  url = url === undefined ? "/#/login" : url;

  await browser.get(url);
  await element(by.model("loginData.loginUsername")).sendKeys(username);
  await element(by.model("loginData.loginPassword")).sendKeys(password);
  await element(by.id("login-button")).click();

  if (firstlogin) {
    url = "/actions/forcedpasswordchange";
  } else {
    url = url.split("#")[1];
    url = url === "/login" ? "/admin/home" : url;
  }

  await exports.waitForUrl(url);
};

exports.login_receiver = async function(username, password, url, firstlogin) {
  username = username === undefined ? "Recipient1" : username;
  password = password === undefined ? exports.vars["user_password"] : password;
  url = url === undefined ? "/#/login" : url;

  await browser.get(url);
  await element(by.model("loginData.loginUsername")).sendKeys(username);
  await element(by.model("loginData.loginPassword")).sendKeys(password);
  await element(by.id("login-button")).click();

  if (firstlogin) {
    url = "/actions/forcedpasswordchange";
  } else {
    url = url.split("#")[1];
    url = url === "/login" ? "/receiver/home" : url;
  }

  await exports.waitForUrl(url);
};

exports.login_custodian = async function(username, password, url, firstlogin) {
  username = username === undefined ? "Custodian1" : username;
  password = password === undefined ? exports.vars["user_password"] : password;
  url = url === undefined ? "/#/login" : url;

  await browser.get(url);
  await element(by.model("loginData.loginUsername")).sendKeys(username);
  await element(by.model("loginData.loginPassword")).sendKeys(password);
  await element(by.id("login-button")).click();

  if (firstlogin) {
    url = "/actions/forcedpasswordchange";
  } else {
    url = url.split("#")[1];
    url = url === "/login" ? "/custodian/home" : url;
  }

  await exports.waitForUrl(url);
};

exports.logout = async function(redirect_url) {
  redirect_url = redirect_url === undefined ? "/" : redirect_url;
  await element(by.id("LogoutLink")).click();
  await exports.waitForUrl(redirect_url);
};

exports.clickFirstDisplayed = async function(selector) {
  var elems = element.all(selector);

  var displayedElems = elems.filter(function(elem) {
    return elem.isDisplayed();
  });

  await displayedElems.first().click();
};

// Utility Functions for handling File operations

exports.makeTestFilePath = function(name) {
  return path.resolve(path.join(browser.params.testDir, "files", name));
};

exports.makeSavedFilePath = function(name) {
  return path.resolve(path.join(browser.params.tmpDir, name));
};

exports.checksum = function(input) {
  return crypto.createHash("sha1").update(input, "utf8").digest("hex");
};

exports.testFileEquality = function(a_path, b_path) {
  var a_hash = exports.checksum(fs.readFileSync(a_path));
  var b_hash = exports.checksum(fs.readFileSync(b_path));
  expect(a_hash).toEqual(b_hash);
};
