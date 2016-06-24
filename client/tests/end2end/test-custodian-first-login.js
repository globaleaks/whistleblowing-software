var utils = require('./utils.js');

describe('receiver first login', function() {
  it('should redirect to /firstlogin upon successful authentication', function() {
    utils.login_custodian('Custodian1', utils.vars['default_password'], '/#/custodian', true);
  });

  it('should be able to change password from the default one', function() {
    element(by.model('preferences.old_password')).sendKeys(utils.vars['default_password']);
    element(by.model('preferences.password')).sendKeys(utils.vars['user_password']);
    element(by.model('preferences.check_password')).sendKeys(utils.vars['user_password']);
    element(by.css('[data-ng-click="pass_save()"]')).click();
    utils.waitForUrl('/custodian/identityaccessrequests');
  });

  it('should be able to login with the new password', function() {
    utils.login_custodian();
  });
});
