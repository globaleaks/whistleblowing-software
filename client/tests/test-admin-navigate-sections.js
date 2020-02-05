describe("verify navigation of admin sections", function() {
  // Even if not performing real checks this test at least verify to be able to perform the
  // navigation of the admin section without triggering any exception

  it("should should navigate through admin sections", async function() {
    await browser.gl.utils.login_admin();

    await element.all(by.cssContainingText("a", "Home")).first().click();
    await element(by.cssContainingText("ul li a", "Changelog")).click();
    await element(by.cssContainingText("ul li a", "License")).click();

    await element(by.cssContainingText("a", "Site settings")).click();
    await element(by.cssContainingText("ul li a", "Main configuration")).click();
    await element(by.cssContainingText("ul li a", "Theme customization")).click();
    await element(by.cssContainingText("ul li a", "Languages")).click();
    await element(by.cssContainingText("ul li a", "Text customization")).click();

    await element(by.cssContainingText("a", "Users")).click();
    await element(by.cssContainingText("a", "Questionnaires")).click();
    await element(by.cssContainingText("a", "Contexts")).click();
    await element(by.cssContainingText("a", "Case management")).click();

    await element(by.cssContainingText("a", "Notification settings")).click();
    await element(by.cssContainingText("ul li a", "Main configuration")).click();
    await element(by.cssContainingText("ul li a", "Notification templates")).click();

    await element(by.cssContainingText("a", "Network settings")).click();
    await element(by.cssContainingText("ul li a", "Tor")).click();
    await element(by.cssContainingText("ul li a", "HTTPS")).click();
    await element(by.cssContainingText("ul li a", "Access control")).click();

    await element(by.cssContainingText("a", "Sites management")).click();
    await element(by.cssContainingText("ul li a", "Main configuration")).click();
    await element.all(by.cssContainingText("ul li a", "Sites")).get(1).click();

    await element(by.cssContainingText("a", "Advanced settings")).click();
    await element(by.cssContainingText("ul li a", "Main configuration")).click();
    await element(by.cssContainingText("ul li a", "URL redirects")).click();
    await element(by.cssContainingText("ul li a", "Anomaly detection thresholds")).click();

    await element(by.cssContainingText("a", "Audit log")).click();
    await element(by.cssContainingText("ul li a", "Stats")).click();
    await element(by.cssContainingText("ul li a", "Activities")).click();
    await element.all(by.cssContainingText("ul li a", "Users")).get(1).click();
    await element(by.cssContainingText("ul li a", "Anomalies")).click();
    await element(by.cssContainingText("ul li a", "Scheduled jobs")).click();
  });
});
