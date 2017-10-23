describe('verify navigation of admin sections', function() {
  // Even if not performing real checks this test at least verify to be able to perform the
  // navigation of the admin section without triggering any exception

  it('should should navigate through admin sections', function() {
    element.all(by.cssContainingText("a", "Home")).first().click();
    element(by.cssContainingText("a", "Changelog")).click();
    element(by.cssContainingText("a", "License")).click();

    element(by.cssContainingText("a", "General settings")).click();
    element(by.cssContainingText("a", "Main configuration")).click();
    element(by.cssContainingText("a", "Theme customization")).click();
    element(by.cssContainingText("a", "Languages")).click();
    element(by.cssContainingText("a", "Text customization")).click();

    element(by.cssContainingText("a", "User management")).click();
    element(by.cssContainingText("a", "Recipient configuration")).click();
    element(by.cssContainingText("a", "Context configuration")).click();
    element(by.cssContainingText("a", "Questionnaire configuration")).click();
    element(by.cssContainingText("a", "Sites management")).click();

    element(by.cssContainingText("a", "Notification settings")).click();
    element(by.cssContainingText("a", "Main configuration")).click();
    element(by.cssContainingText("a", "Notification templates")).click();
    element(by.cssContainingText("a", "Exception notification")).click();

    element(by.cssContainingText("a", "URL shortener")).click();

    element(by.cssContainingText("a", "Network settings")).click();
    element(by.cssContainingText("a", "Main configuration")).click();
    element(by.cssContainingText("a", "HTTPS settings")).click();
    element(by.cssContainingText("a", "Access control")).click();

    element(by.cssContainingText("a", "Advanced settings")).click();
    element(by.cssContainingText("a", "Main configuration")).click();
    element(by.cssContainingText("a", "Anomaly detection thresholds")).click();
  });
});
