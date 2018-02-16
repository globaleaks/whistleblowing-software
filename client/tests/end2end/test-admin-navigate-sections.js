describe('verify navigation of admin sections', function() {
  // Even if not performing real checks this test at least verify to be able to perform the
  // navigation of the admin section without triggering any exception

  it('should should navigate through admin sections', function() {
    element.all(by.cssContainingText("a", "Home")).first().click();
    element(by.cssContainingText("ul li a", "Changelog")).click();
    element(by.cssContainingText("ul li a", "License")).click();

    element(by.cssContainingText("a", "General settings")).click();
    element(by.cssContainingText("ul li a", "Main configuration")).click();
    element(by.cssContainingText("ul li a", "Theme customization")).click();
    element(by.cssContainingText("ul li a", "Languages")).click();
    element(by.cssContainingText("ul li a", "Text customization")).click();

    element(by.cssContainingText("a", "Users")).click();
    element(by.cssContainingText("a", "Recipients")).click();
    element(by.cssContainingText("a", "Contexts")).click();
    element(by.cssContainingText("a", "Questionnaires")).click();

    element(by.cssContainingText("a", "Notification settings")).click();
    element(by.cssContainingText("ul li a", "Main configuration")).click();
    element(by.cssContainingText("ul li a", "Notification templates")).click();

    element(by.cssContainingText("a", "Network settings")).click();
    element(by.cssContainingText("ul li a", "Tor")).click();
    element(by.cssContainingText("ul li a", "HTTPS")).click();

    element(by.cssContainingText("a", "Advanced settings")).click();
    element(by.cssContainingText("ul li a", "Main configuration")).click();
    element(by.cssContainingText("ul li a", "URL shortener")).click();
    element(by.cssContainingText("ul li a", "Anomaly detection thresholds")).click();
  });
});
