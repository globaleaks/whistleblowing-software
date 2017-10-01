var receiver = new browser.gl.pages.receiver();

var path = require('path');

var pgp_key_path = path.resolve('../backend/globaleaks/tests/data/gpg/VALID_PGP_KEY1_PUB');

describe('receiver first login', function() {
  it('should redirect to /firstlogin upon successful authentication', function() {
    browser.gl.utils.login_receiver('recipient', browser.gl.utils.vars['default_password'], '/#/login', true);
  });

  it('should be able to change password from the default one', function() {
    element(by.model('preferences.old_password')).sendKeys(browser.gl.utils.vars['default_password']);
    element(by.model('preferences.password')).sendKeys(browser.gl.utils.vars['user_password']);
    element(by.model('preferences.check_password')).sendKeys(browser.gl.utils.vars['user_password']);
    element(by.css('[data-ng-click="save()"]')).click();
    browser.gl.utils.waitForUrl('/receiver/tips');
  });

  it('should be able to login with the new password', function() {
    browser.gl.utils.login_receiver();
  });

  it('should be able to navigate through receiver preferences', function() {
    element(by.id('PreferencesLink')).click();
    browser.gl.utils.waitForUrl('/receiver/preferences');
    var preferencesForm = element(by.id("preferencesForm"));
    preferencesForm.element(by.cssContainingText("a", "Preferences")).click();
    preferencesForm.element(by.cssContainingText("a", "Password configuration")).click();
    preferencesForm.element(by.cssContainingText("a", "Notification settings")).click();
    preferencesForm.element(by.cssContainingText("a", "Encryption settings")).click();
  });

  it('should be able to load his/her public PGP key', function() {
    receiver.addPublicKey(pgp_key_path);
  });
});
