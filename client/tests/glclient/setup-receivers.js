describe('globaLeaks setup receiver(s)', function() {
  it('should allow the user to setup the wizard', function() {
      browser.get('http://127.0.0.1:8082/admin');
      
      // Go to step 2
      //element(by.css('[data-ng-click="step=step+1"]')).click();
      
      // Fill out the form
      element(by.model('loginUsername')).sendKeys('admin');
      element(by.model('loginPassword')).sendKeys('Antani1234');

      element(by.css('button')).submit();
      browser.pause();

      browser.setLocation('admin/receivers');
      browser.pause();

      element(by.model('new_receiver.name')).sendKeys('altro');
      element(by.model('new_receiver.email')).sendKeys('altro@altro.xxx');

      element(by.css('button')).submit();
      /*
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
      */
    });
});
