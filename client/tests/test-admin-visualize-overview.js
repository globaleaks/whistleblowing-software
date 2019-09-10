describe("verify navigation of admin overview sections", function() {
  it("should should navigate through overview sections", async function() {
    await browser.gl.utils.login_admin();

    await element(by.cssContainingText("a", "System overview")).click();

    var pageContent = element(by.id("PageContent"));

    await pageContent.element(by.cssContainingText("a", "Stats")).click();
    await pageContent.element(by.cssContainingText("a", "Activities")).click();
    await pageContent.element(by.cssContainingText("a", "Users")).click();
    await pageContent.element(by.cssContainingText("a", "Anomalies")).click();
    await pageContent.element(by.cssContainingText("a", "Scheduled jobs")).click();
  });
});
