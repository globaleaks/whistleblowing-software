var utils = require('./utils.js');

var temporary_password = "typ0drome@absurd.org";

describe('receiver first login', function() {
  it('should redirect to /firstlogin upon successful authentication', function() {
    utils.login_custodian('Custodian1', utils.vars['default_password'], '/#/custodian', true);
  });

  it('should be able to change password from the default one', function() {
    element(by.model('preferences.old_password')).sendKeys(utils.vars['default_password']);
    element(by.model('preferences.password')).sendKeys(temporary_password);
    element(by.model('preferences.check_password')).sendKeys(temporary_password);
    element(by.css('[data-ng-click="save()"]')).click();
    utils.waitForUrl('/custodian/identityaccessrequests');
  });

  it('should be able to login with the new password', function() {
    utils.login_custodian('Custodian1', temporary_password, '/#/custodian', false);
  });

  it('should be able to change password accessing the user preferences', function() {
    element(by.cssContainingText("a", "Preferences")).click();
    element(by.cssContainingText("a", "Password configuration")).click();
    element(by.model('preferences.old_password')).sendKeys(temporary_password);
    element(by.model('preferences.password')).sendKeys(utils.vars['user_password']);
    element(by.model('preferences.check_password')).sendKeys(utils.vars['user_password']);
    utils.clickFirstDisplayed(by.css('[data-ng-click="save()"]'));
  });
});
