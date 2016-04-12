var utils = require('./utils.js');

exports.adminLoginPage = function() {
  var loginUser = element(by.model('loginUsername'));
  var loginPass = element(by.model('loginPassword'));

  this.get = function() {
    browser.get('/#/admin');
  };

  this.login = function(uname, pass) {
    this.get();
    loginUser.sendKeys(uname);
    loginPass.sendKeys(pass);
    element(by.xpath('//button[contains(., "Log in")]')).click();
    utils.waitForUrl('/admin/landing');
  };
};
