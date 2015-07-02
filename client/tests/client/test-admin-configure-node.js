describe('adming configure node', function() {
  it('should configure node', function() {
    browser.setLocation('admin/advanced_settings');

    /// simplify the configuration in order to simplfy initial tests
    element(by.model('admin.node.disable_security_awareness_badge')).click();

    // configure email used for exceptions testin
    element(by.model('admin.node.exception_email')).clear();
    element(by.model('admin.node.exception_email')).sendKeys('globaleaks-exceptions@mailinator.com');

    //enable all receivers to postpone and delete tips
    element(by.model('admin.node.can_postpone_expiration')).click();
    element(by.model('admin.node.can_delete_submission')).click();

    // grant tor2web permissions
    element(by.cssContainingText("a", "Tor2web Settings")).click();
    element(by.model('admin.node.tor2web_receiver')).click();
    element(by.model('admin.node.tor2web_submission')).click();

    // save settings
    element(by.css('[data-ng-click="updateNode(admin.node)"]')).click().then(function() {

    });

  });
});
