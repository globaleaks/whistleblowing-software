var utils = require('./utils.js');

var pages = require('./pages.js');
var receiver = new pages.receiver();

var fs = require('fs');
var opts = { encoding: 'utf8', flag: 'r' };
var pgp_key = fs.readFileSync('../backend/globaleaks/tests/keys/VALID_PGP_KEY1_PUB', opts);

describe('receiver first login', function() {
  it('should redirect to /firstlogin upon successful authentication', function() {
    utils.login_receiver('Recipient1', utils.vars['default_password'], '/login', true);
  });

  it('should be able to change password from the default one', function() {
    element(by.model('preferences.old_password')).sendKeys(utils.vars['default_password']);
    element(by.model('preferences.password')).sendKeys(utils.vars['user_password']);
    element(by.model('preferences.check_password')).sendKeys(utils.vars['user_password']);
    element(by.css('[data-ng-click="pass_save()"]')).click();
    utils.waitForUrl('/receiver/tips');
  });

  it('should be able to login with the new password', function() {
    utils.login_receiver();
  });

  it('should be able to navigate through receiver preferences', function() {
    element(by.id('PreferencesLink')).click();
    utils.waitForUrl('/receiver/preferences');
    var preferencesForm = element(by.id("preferencesForm"));
    preferencesForm.element(by.cssContainingText("a", "Preferences")).click();
    preferencesForm.element(by.cssContainingText("a", "Password configuration")).click();
    preferencesForm.element(by.cssContainingText("a", "Notification settings")).click();
    preferencesForm.element(by.cssContainingText("a", "Encryption settings")).click();
  });

  it('should be able to load his/her public PGP key', function() {
    receiver.addPublicKey(pgp_key);
  });
});
