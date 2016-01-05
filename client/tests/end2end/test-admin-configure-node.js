var utils = require('./utils.js');

describe('adming configure node', function() {
  it('should configure node', function() {
    browser.setLocation('admin/advanced_settings');

    /// simplify the configuration in order to simplfy initial tests
    element(by.model('admin.node.disable_security_awareness_badge')).click();

    //enable all receivers to postpone and delete tips
    element(by.model('admin.node.can_postpone_expiration')).click();
    element(by.model('admin.node.can_delete_submission')).click();

    // temporary fix in order to disable the proof of work for testing IE9
    // and generically test all the browsers that does not support workers
    if (utils.isOldIE()) {
      element(by.model('admin.node.enable_proof_of_work')).click();
    }

    // grant tor2web permissions
    element(by.cssContainingText("a", "HTTPS settings")).click();
    element(by.model('admin.node.tor2web_whistleblower')).click();

    // save settings
    element(by.css('[data-ng-click="updateNode(admin.node)"]')).click().then(function() {
      browser.setLocation('/admin/mail');

      element(by.cssContainingText("a", "Exception notification")).click();

      // configure email used for exceptions testin
      element(by.model('admin.notification.exception_email_address')).clear();
      element(by.model('admin.notification.exception_email_address')).sendKeys('globaleaks-exceptions@mailinator.com');

      element(by.css('[data-ng-click="update(admin.notification)"]')).click().then(function() {

      });
    });
  });
});
