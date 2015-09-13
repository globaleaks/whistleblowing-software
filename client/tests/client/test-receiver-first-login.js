describe('receiver first login', function() {
  it('should redirect to /firstlogin upon successful authentication', function() {
    var deferred = protractor.promise.defer();
    browser.get('/#/login');
    element(by.model('loginUsername')).element(by.xpath(".//*[text()='Receiver 1']")).click().then(function() {
      element(by.model('loginPassword')).sendKeys('globaleaks').then(function() {
        element(by.xpath('//button[contains(., "Log in")]')).click().then(function() {
          expect(browser.getLocationAbsUrl()).toContain('/forcedpasswordchange');
          deferred.fulfill();
        });
      });
    });

    return deferred;
  });
  it('should be able to change password from the default one', function() {
    var deferred = protractor.promise.defer();
    browser.setLocation('/forcedpasswordchange');
    element(by.model('preferences.old_password')).sendKeys('globaleaks').then(function() {
      element(by.model('preferences.password')).sendKeys('ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#').then(function() {
        element(by.model('preferences.check_password')).sendKeys('ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#').then(function() {
          element(by.css('[data-ng-click="pass_save()"]')).click().then(function() {
            expect(browser.getLocationAbsUrl()).toContain('/receiver/tips');
            deferred.fulfill();
          });
        });
      });
    });
    return deferred;
  });
  it('should be able to login with the new password', function() {
    var deferred = protractor.promise.defer();
    browser.get('/#/login');
    element(by.model('loginUsername')).element(by.xpath(".//*[text()='Receiver 1']")).click().then(function() {
      element(by.model('loginPassword')).sendKeys('ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#').then(function() {
        element(by.xpath('//button[contains(., "Log in")]')).click().then(function() {
          expect(browser.getLocationAbsUrl()).toContain('/receiver/tips');
          deferred.fulfill();
        });
      });
    });
    return deferred;
  });
});
