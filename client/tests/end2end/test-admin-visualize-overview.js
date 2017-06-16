var utils = require('./utils.js');

describe('verify navigation of admin overview sections', function() {
  it('should should navigate through overview sections', function() {
    utils.login_admin();
    element(by.cssContainingText("a", "System overview")).click();
    element(by.cssContainingText("a", "Stats")).click();
    element(by.cssContainingText("a", "Activities")).click();
    element(by.cssContainingText("a", "Submissions")).click();
    element(by.cssContainingText("a", "Users")).click();
    element(by.cssContainingText("a", "Files")).click();
    element(by.cssContainingText("a", "Anomalies")).click();
    element(by.cssContainingText("a", "Scheduled jobs")).click();
  });
});
