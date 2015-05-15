describe('receiver first login', function() {
  it('should redirect to /firstlogin upon successful authentication', function() {
    browser.get('/#/login');
    element(by.model('loginUsername')).element(by.xpath(".//*[text()='Receiver 1']")).click().then(function() {
      element(by.model('loginPassword')).sendKeys('globaleaks').then(function() {
        element(by.xpath('//button[contains(., "Log in")]')).click();
        expect(browser.getLocationAbsUrl()).toContain('/#/receiver/firstlogin');
      });
    });
  });
  it('should be able to change password from the default one', function() {
    browser.setLocation('/receiver/firstlogin');
    element(by.model('preferences.old_password')).sendKeys('globaleaks').then(function() {
      element(by.model('preferences.password')).sendKeys('ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#').then(function() {
        element(by.model('preferences.check_password')).sendKeys('ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#').then(function() {
          element(by.css('[data-ng-click="pass_save()"]')).click();
          expect(browser.getLocationAbsUrl()).toContain('/#/receiver/tips');
        });
      });
    });
  });
  it('should be able to login with the new password', function() {
    browser.get('/#/login');
    element(by.model('loginUsername')).element(by.xpath(".//*[text()='Receiver 1']")).click().then(function() {
      element(by.model('loginPassword')).sendKeys('ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#').then(function() {
        element(by.xpath('//button[contains(., "Log in")]')).click();
        expect(browser.getLocationAbsUrl()).toContain('/#/receiver/tips');
      });
    });
  });
});
