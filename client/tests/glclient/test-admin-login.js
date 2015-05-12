describe('admin login', function() {
  it('should login as admin', function() {
    browser.get('/admin');

    element(by.model('loginUsername')).sendKeys('admin');
    element(by.model('loginPassword')).sendKeys('ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#');

    element(by.css('button')).click().then(function() {

    });
  });
});
