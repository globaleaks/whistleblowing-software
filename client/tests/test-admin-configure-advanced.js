describe("admin configure advanced settings", function() {
  it("should perform main configuration", async function() {
    await browser.gl.utils.login_admin();
    await browser.setLocation("admin/advanced");
    await element(by.cssContainingText("a", "Main configuration")).click();

    // enable features that by default are disabled
    await element(by.model("resources.node.enable_custodian")).click();
    await element(by.model("resources.node.multisite")).click();

    // save settings
    await element.all(by.css("[data-ng-click=\"updateNode()\"]")).first().click();
  });
});

describe("admin disable submissions", function() {
  it("should disable submission", async function() {
    await browser.setLocation("admin/advanced");
    await element(by.cssContainingText("a", "Main configuration")).click();

    await element(by.model("resources.node.disable_submissions")).click();

    // save settings
    await element.all(by.css("[data-ng-click=\"updateNode()\"]")).first().click();

    expect(await element(by.model("resources.node.disable_submissions")).isSelected()).toBeTruthy();

    await browser.gl.utils.logout();

    await browser.get("/#/");

    expect(await browser.isElementPresent(element(by.cssContainingText("span", "Submissions disabled")))).toBe(true);

    await browser.gl.utils.login_admin();

    await browser.setLocation("admin/advanced");

    await element(by.model("resources.node.disable_submissions")).click();

    // save settings
    await element.all(by.css("[data-ng-click=\"updateNode()\"]")).first().click();

    expect(await element(by.model("resources.node.disable_submissions")).isSelected()).toBeFalsy();

    await browser.gl.utils.logout();

    await browser.get("/#/");

    expect(await browser.isElementPresent(element(by.cssContainingText("button", "File a report")))).toBe(true);
  });
});
