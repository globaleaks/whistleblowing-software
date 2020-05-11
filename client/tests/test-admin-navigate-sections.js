describe("verify navigation of admin sections", function() {
  // Even if not performing real checks this test at least verify to be able to perform the
  // navigation of the admin section without triggering any exception

  it("should should navigate through admin sections", async function() {
    await browser.gl.utils.login_admin();

    await element.all(by.cssContainingText("a", "Home")).first().click();
    await element.all(by.cssContainingText("a", "Changelog")).first().click();
    await element.all(by.cssContainingText("a", "License")).first().click();

    await element.all(by.cssContainingText("a", "Site settings")).first().click();
    await element.all(by.cssContainingText("a", "Main configuration")).first().click();
    await element.all(by.cssContainingText("a", "Theme customization")).first().click();
    await element.all(by.cssContainingText("a", "Languages")).first().click();
    await element.all(by.cssContainingText("a", "Text customization")).first().click();

    await element.all(by.cssContainingText("a", "Users")).first().click();
    await element.all(by.cssContainingText("a", "Questionnaires")).first().click();
    await element.all(by.cssContainingText("a", "Contexts")).first().click();
    await element.all(by.cssContainingText("a", "Case management")).first().click();

    await element.all(by.cssContainingText("a", "Notification settings")).first().click();
    await element.all(by.cssContainingText("a", "Main configuration")).first().click();
    await element.all(by.cssContainingText("a", "Notification templates")).first().click();

    await element.all(by.cssContainingText("a", "Network settings")).first().click();
    await element.all(by.cssContainingText("a", "Tor")).first().click();
    await element.all(by.cssContainingText("a", "HTTPS")).first().click();
    await element.all(by.cssContainingText("a", "Access control")).first().click();
    await element.all(by.cssContainingText("a", "URL redirects")).first().click();

    await element.all(by.cssContainingText("a", "Sites management")).first().click();
    await element.all(by.cssContainingText("a", "Main configuration")).first().click();
    await element.all(by.cssContainingText("a", "Sites")).first().click();

    await element.all(by.cssContainingText("a", "Advanced settings")).first().click();
    await element.all(by.cssContainingText("a", "Main configuration")).first().click();
    await element.all(by.cssContainingText("a", "Anomaly detection thresholds")).first().click();

    await element.all(by.cssContainingText("a", "Audit log")).first().click();
    await element.all(by.cssContainingText("a", "Stats")).first().click();
    await element.all(by.cssContainingText("a", "Activities")).first().click();
    await element.all(by.cssContainingText("a", "Users")).get(1).click();
    await element.all(by.cssContainingText("a", "Anomalies")).first().click();
    await element.all(by.cssContainingText("a", "Scheduled jobs")).first().click();
  });
});
