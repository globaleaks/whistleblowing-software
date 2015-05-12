describe('globaLeaks grant tor2web permissions', function() {
  it('should grant accesses via tor2web', function() {
    browser.get('/admin');

    element(by.model('loginUsername')).sendKeys('admin');
    element(by.model('loginPassword')).sendKeys('ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#');

    element(by.css('button')).click().then(function () {

      browser.setLocation('admin/advanced_settings');

      element(by.model('admin.node.disable_privacy_badge')).click();
      element(by.model('admin.node.disable_security_awareness_questions')).click();

      element(by.cssContainingText("a", "Tor2web Settings")).click();

      element(by.model('admin.node.tor2web_receiver')).click();
      element(by.model('admin.node.tor2web_submission')).click();
      element(by.css('[data-ng-click="updateNode(admin.node)"]')).click();

    });
  });
});
