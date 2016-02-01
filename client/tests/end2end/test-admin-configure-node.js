var utils = require('./utils.js');

describe('adming configure node', function() {
  it('should configure node', function(done) {
    browser.setLocation('admin/advanced_settings');

    // simplify the configuration in order to simplfy initial tests
    element(by.model('admin.node.disable_security_awareness_badge')).click();

    // enable all receivers to postpone and delete tips
    element(by.model('admin.node.can_postpone_expiration')).click();
    element(by.model('admin.node.can_delete_submission')).click();

    // temporary fix in order to disable the proof of work for testing IE9
    // and generically test all the browsers that does not support workers
    if (utils.isOldIE()) {
      element(by.model('admin.node.enable_proof_of_work')).click();
    }

    // enable experimental featuress that by default are disabled
    element(by.model('admin.node.enable_experimental_features')).click();

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
      done();
      });
    });
  });
});

describe('verify navigation of admin sections', function() {
  // Even if not performing real checks this test at least verify to be able to perform the
  // navigation of the admin section without triggering any exception

  it('should should navigate through admin sections', function(done) {
    element(by.cssContainingText("a", "General settings")).click().then(function() {
      browser.waitForAngular();
      element(by.cssContainingText("a", "Main configuration")).click();
      browser.waitForAngular();
      element(by.cssContainingText("a", "Theme customization")).click();
      browser.waitForAngular();
      element(by.cssContainingText("a", "Translation customization")).click();
      browser.waitForAngular();
    });

    element(by.cssContainingText("a", "User management")).click();
    browser.waitForAngular();
    element(by.cssContainingText("a", "Recipient configuration")).click();
    browser.waitForAngular();
    element(by.cssContainingText("a", "Context configuration")).click();
    browser.waitForAngular();
    element(by.cssContainingText("a", "Questionnaire configuration")).click();
    browser.waitForAngular();

    element(by.cssContainingText("a", "Notification settings")).click().then(function() {
      browser.waitForAngular();
      element(by.cssContainingText("a", "Main configuration")).click();
      browser.waitForAngular();
      element(by.cssContainingText("a", "Admin notification templates")).click();
      browser.waitForAngular();
      element(by.cssContainingText("a", "Recipient notification templates")).click();
      browser.waitForAngular();
      element(by.cssContainingText("a", "Exception notification")).click();
      browser.waitForAngular();
    });

    element(by.cssContainingText("a", "URL shortener")).click();
    browser.waitForAngular();

    element(by.cssContainingText("a", "Advanced settings")).click().then(function() {
      browser.waitForAngular();
      element(by.cssContainingText("a", "Main configuration")).click();
      browser.waitForAngular();
      element(by.cssContainingText("a", "HTTPS settings")).click();
      browser.waitForAngular();
      element(by.cssContainingText("a", "Anomaly detection thresholds")).click();
      browser.waitForAngular();
    });

    element(by.cssContainingText("a", "Recent activities")).click();
    browser.waitForAngular();
    element(by.cssContainingText("a", "System stats")).click();
    browser.waitForAngular();
    element(by.cssContainingText("a", "Anomalies")).click();
    browser.waitForAngular();
    element(by.cssContainingText("a", "User overview")).click();
    browser.waitForAngular();
    element(by.cssContainingText("a", "Submission overview")).click();
    browser.waitForAngular();
    element(by.cssContainingText("a", "File overview")).click();
    browser.waitForAngular();

    done();
  });
});

describe('configure short urls', function() {
  it('should should be able to configure short urls', function(done) {
    for (var i = 0; i < 3; i++) {
      element(by.cssContainingText("a", "URL shortener")).click().then(function() {
        element(by.model('new_shorturl.shorturl')).sendKeys('shorturl');
        element(by.model('new_shorturl.longurl')).sendKeys('longurl');
        element(by.cssContainingText("button", "Add")).click().then(function() {
          browser.waitForAngular();
          element(by.cssContainingText("button", "Delete")).click().then(function() {
            browser.waitForAngular();
            done();
          });
        });
      });
    }
  });
});
