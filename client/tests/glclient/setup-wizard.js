describe('globaLeaks setup wizard', function() {
  it('should allow the user to setup the wizard', function() {
      browser.get('http://127.0.0.1:8082/');
      
      // Go to step 2
      element(by.css('[data-ng-click="step=step+1"]')).click();
      
      // Fill out the form
      element(by.model('admin.node.name')).sendKeys('My Node');
      element(by.model('admin.node.description')).sendKeys('My Description');

      element(by.model('admin.node.email')).sendKeys('info@globaleaks.org');

      element(by.model('admin.node.password')).sendKeys('Antani1234');
      element(by.model('admin.node.check_password')).sendKeys('Antani1234');

      element(by.model('receiver.name')).sendKeys('Beppa Pigga');
      element(by.model('receiver.mail_address')).sendKeys('info@globaleaks.org');
      
      // Disable encryption for receiver
      element(by.model('admin.node.allow_unencrypted')).click();
      element(by.css('[data-ng-click="ok()"]')).click();
      
      element(by.model('context.name')).sendKeys('My Context');
      
      // Complete the form
      element.all(by.css('[data-ng-click="step=step+1"]')).get(1).click();
      
      // Make sure the congratulations text is present
      expect(element(by.css('.congratulations')).isPresent()).toBe(true) 
      
      // Go to admin interface
      element(by.css('[data-ng-click="finish()"]')).click();
      
      // Edit the advanced settings
      browser.setLocation('admin/advanced_settings');

      element(by.model('admin.node.disable_privacy_badge')).click();
      element(by.model('admin.node.disable_security_awareness_questions')).click();

      element(by.cssContainingText("a", "Tor2web Settings")).click();

      element(by.model('admin.node.tor2web_receiver')).click();
      element(by.model('admin.node.tor2web_submission')).click();

      element(by.css('[data-ng-click="updateNode(admin.node)"]')).click();
    });
});
