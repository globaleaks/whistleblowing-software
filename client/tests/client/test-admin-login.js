describe('admin login', function() {
  it('should login as admin', function() {
    var deferred = protractor.promise.defer();

    browser.get('/#/admin');

    element(by.model('loginUsername')).sendKeys('admin');
    element(by.model('loginPassword')).sendKeys('ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#');

    element(by.xpath('//button[contains(., "Log in")]')).click().then(function() {
      expect(browser.getLocationAbsUrl()).toContain('/admin/landing');
      deferred.fulfill();
    });

    return deferred;
  });
});
