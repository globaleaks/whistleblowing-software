var utils = require('./utils.js');

var fs = require('fs');

var opts = { encoding: 'utf8', flag: 'r' };
var pgp_key = fs.readFileSync('../backend/globaleaks/tests/keys/VALID_PGP_KEY1_PUB', opts);

describe('receiver first login', function() {
  it('should redirect to /firstlogin upon successful authentication', function(done) {
    browser.get('/#/login');
    element(by.model('loginUsername')).element(by.xpath(".//*[text()='Recipient 1']")).click().then(function() {
      element(by.model('loginPassword')).sendKeys('globaleaks').then(function() {
        element(by.xpath('//button[contains(., "Log in")]')).click().then(function() {
          utils.waitForUrl('/forcedpasswordchange');
          done();
        });
      });
    });
  });

  it('should be able to change password from the default one', function(done) {
    element(by.model('preferences.old_password')).sendKeys(utils.vars['default_password']).then(function() {
      element(by.model('preferences.password')).sendKeys(utils.vars['user_password']).then(function() {
        element(by.model('preferences.check_password')).sendKeys(utils.vars['user_password']).then(function() {
          element(by.css('[data-ng-click="pass_save()"]')).click().then(function() {
            utils.waitForUrl('/receiver/tips');
            done();
          });
        });
      });
    });
  });

  it('should be able to login with the new password', function(done) {
    browser.get('/#/login');
    element(by.model('loginUsername')).element(by.xpath(".//*[text()='Recipient 1']")).click().then(function() {
      element(by.model('loginPassword')).sendKeys(utils.vars['user_password']).then(function() {
        element(by.xpath('//button[contains(., "Log in")]')).click().then(function() {
          expect(browser.getLocationAbsUrl()).toContain('/receiver/tips');
          done();
        });
      });
    });
  });

  it('should be able to navigate through receiver preferences', function(done) {
    element(by.id('PreferencesLink')).click().then(function() {
      utils.waitForUrl('/receiver/preferences');
      var preferencesForm = element(by.id("preferencesForm"));
      preferencesForm.element(by.cssContainingText("a", "Preferences")).click();
      preferencesForm.element(by.cssContainingText("a", "Password configuration")).click();
      preferencesForm.element(by.cssContainingText("a", "Notification settings")).click();
      preferencesForm.element(by.cssContainingText("a", "Encryption settings")).click();
      done();
    });
  });

  it('should be able to load his/her public PGP key', function(done) {
    browser.setLocation('receiver/preferences');
    element(by.cssContainingText("a", "Encryption settings")).click();
    element(by.model('preferences.pgp_key_public')).sendKeys(pgp_key);
    element(by.cssContainingText("span", "Update notification and encryption settings")).click();
    done();
  });
});
