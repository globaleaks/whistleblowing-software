describe('adming configure node', function() {
  it('should configure node', function() {
    var deferred = protractor.promise.defer();

    browser.setLocation('admin/advanced_settings');

    /// simplify the configuration in order to simplfy initial tests
    element(by.model('admin.node.disable_security_awareness_badge')).click();

    //enable all receivers to postpone and delete tips
    element(by.model('admin.node.can_postpone_expiration')).click();
    element(by.model('admin.node.can_delete_submission')).click();

    // grant tor2web permissions
    element(by.cssContainingText("a", "Tor2web Settings")).click();
    element(by.model('admin.node.tor2web_receiver')).click();
    element(by.model('admin.node.tor2web_whistleblower')).click();

    // save settings
    element(by.css('[data-ng-click="updateNode(admin.node)"]')).click().then(function() {
      browser.setLocation('/admin/mail');

      element(by.cssContainingText("a", "Exception Notification")).click();

      // configure email used for exceptions testin
      element(by.model('admin.notification.exception_email_address')).clear();
      element(by.model('admin.notification.exception_email_address')).sendKeys('globaleaks-exceptions@mailinator.com');

      element(by.css('[data-ng-click="update(admin.notification)"]')).click().then(function() {
        deferred.fulfill();
      });

    });

    return deferred;

  });
});
