var utils = require('./utils.js');

describe('verify navigation of admin sections', function() {
  it('should should navigate through stats sections', function() {
    utils.login_admin();

    element(by.cssContainingText("a", "Recent activities")).click();
    element(by.cssContainingText("a", "System stats")).click();
    element(by.cssContainingText("a", "Anomalies")).click();
    element(by.cssContainingText("a", "User overview")).click();
    element(by.cssContainingText("a", "Submission overview")).click();
    element(by.cssContainingText("a", "File overview")).click();
  });
});
