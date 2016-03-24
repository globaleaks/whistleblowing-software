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
      done();
    });
  });
});

describe('verify navigation of admin sections', function() {
  // Even if not performing real checks this test at least verify to be able to perform the
  // navigation of the admin section without triggering any exception

  it('should should navigate through admin sections', function(done) {
    element(by.cssContainingText("a", "General settings")).click().then(function() {
      element(by.cssContainingText("a", "Main configuration")).click();
      element(by.cssContainingText("a", "Theme customization")).click();
      element(by.cssContainingText("a", "Translation customization")).click();
    });

    element(by.cssContainingText("a", "User management")).click();
    element(by.cssContainingText("a", "Recipient configuration")).click();
    element(by.cssContainingText("a", "Context configuration")).click();
    element(by.cssContainingText("a", "Questionnaire configuration")).click();

    element(by.cssContainingText("a", "Notification settings")).click().then(function() {
      element(by.cssContainingText("a", "Main configuration")).click();
      element(by.cssContainingText("a", "Admin notification templates")).click();
      element(by.cssContainingText("a", "Recipient notification templates")).click();
      element(by.cssContainingText("a", "Exception notification")).click();
    });

    element(by.cssContainingText("a", "URL shortener")).click();

    element(by.cssContainingText("a", "Advanced settings")).click().then(function() {
      element(by.cssContainingText("a", "Main configuration")).click();
      element(by.cssContainingText("a", "HTTPS settings")).click();
      element(by.cssContainingText("a", "Anomaly detection thresholds")).click();
    });

    element(by.cssContainingText("a", "Recent activities")).click();
    element(by.cssContainingText("a", "System stats")).click();
    element(by.cssContainingText("a", "Anomalies")).click();
    element(by.cssContainingText("a", "User overview")).click();
    element(by.cssContainingText("a", "Submission overview")).click();
    element(by.cssContainingText("a", "File overview")).click();

    done();
  });
});

describe('configure short urls', function() {
  it('should should be able to configure short urls', function() {
    for (var i = 0; i < 3; i++) {
      element(by.cssContainingText("a", "URL shortener")).click();
      element(by.model('new_shorturl.shorturl')).sendKeys('shorturl');
      element(by.model('new_shorturl.longurl')).sendKeys('longurl');
      element(by.cssContainingText("button", "Add")).click();
      element(by.cssContainingText("button", "Delete")).click();
    }
  });
});
