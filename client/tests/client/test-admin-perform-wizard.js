describe('globaLeaks setup wizard', function() {
  it('should allow the user to setup the wizard', function() {
    browser.setLocation('wizard');

    // Go to step 2
    element(by.id('ButtonNext1')).click();
      
    // Fill out the form
    element(by.model('admin.node.name')).sendKeys('E2E Test Instance');
    element(by.model('admin.node.description')).sendKeys('This instance is for E2E testing');
    element(by.model('admin.node.email')).sendKeys('globaleaks-admin@mailinator.com');
    element(by.model('admin.node.password')).sendKeys('ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#');
    element(by.model('admin.node.check_password')).sendKeys('ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#');

    element(by.model('receiver.name')).sendKeys('Receiver 1');
    element(by.model('receiver.mail_address')).sendKeys('globaleaks-receiver1@mailinator.com');
      
    // Disable encryption for receiver
    element(by.model('admin.node.allow_unencrypted')).click();
    element(by.css('[data-ng-click="ok()"]')).click();
 
    element(by.model('context.name')).sendKeys('Context 1');
      
    // Complete the form
    element.all(by.id('ButtonNext2')).click();

    expect(element(by.css('.congratulations')).isPresent()).toBe(true);

    // Go to admin interface
    element(by.id('ButtonNext3')).click();
  });
});
