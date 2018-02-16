var temporary_password = "typ0drome@absurd.org";

describe('receiver first login', function() {
  it('should redirect to /firstlogin upon successful authentication', function() {
    browser.gl.utils.login_custodian('Custodian1', 'custodian', '/#/custodian', true);
  });

  it('should be able to change password from the default one', function() {
    element(by.model('preferences.old_password')).sendKeys('custodian');
    element(by.model('preferences.password')).sendKeys(temporary_password);
    element(by.model('preferences.check_password')).sendKeys(temporary_password);
    element(by.css('[data-ng-click="save()"]')).click();
    browser.gl.utils.waitForUrl('/custodian/identityaccessrequests');
  });

  it('should be able to login with the new password', function() {
    browser.gl.utils.login_custodian('Custodian1', temporary_password, '/#/custodian', false);
  });

  it('should be able to change password accessing the user preferences', function() {
    element(by.cssContainingText("a", "Preferences")).click();
    element(by.cssContainingText("a", "Password")).click();
    element(by.model('preferences.old_password')).sendKeys(temporary_password);
    element(by.model('preferences.password')).sendKeys(browser.gl.utils.vars['user_password']);
    element(by.model('preferences.check_password')).sendKeys(browser.gl.utils.vars['user_password']);
    browser.gl.utils.clickFirstDisplayed(by.css('[data-ng-click="save()"]'));
  });
});
