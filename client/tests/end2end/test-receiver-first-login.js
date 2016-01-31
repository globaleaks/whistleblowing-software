var utils = require('./utils.js');

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
    element(by.model('preferences.old_password')).sendKeys('globaleaks').then(function() {
      element(by.model('preferences.password')).sendKeys('ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#').then(function() {
        element(by.model('preferences.check_password')).sendKeys('ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#').then(function() {
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
      element(by.model('loginPassword')).sendKeys('ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#').then(function() {
        element(by.xpath('//button[contains(., "Log in")]')).click().then(function() {
          expect(browser.getLocationAbsUrl()).toContain('/receiver/tips');
          element(by.id('LogoutLink')).click().then(function() {
            utils.waitForUrl('/login');
            done();
          });
        });
      });
    });
  });
});
