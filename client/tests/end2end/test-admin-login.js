var utils = require('./utils.js');

describe('admin login', function() {
  it('should login as admin', function() {
    browser.get('/#/admin');

    element(by.model('loginUsername')).sendKeys('admin');
    element(by.model('loginPassword')).sendKeys(utils.vars['user_password']);

    element(by.xpath('//button[contains(., "Log in")]')).click();
    utils.waitForUrl('/admin/landing');
  });
});
